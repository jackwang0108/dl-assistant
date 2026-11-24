"""TeX-aware nodes and order/scoped conservative expansion with source provenance."""

import re
from bisect import bisect_right
from functools import lru_cache
from pathlib import Path

from pylatexenc.latexwalker import (
    LatexCommentNode,
    LatexEnvironmentNode,
    LatexGroupNode,
    LatexWalker,
    LatexWalkerEndOfStream,
    LatexWalkerParseError,
    get_default_latex_context_db,
)
from pylatexenc.macrospec import MacroSpec

from .acquire import contained
from .models import TexError

OPAQUE = {"verbatim", "verbatim*", "lstlisting", "minted", "comment"}
DEFINITIONS = {"newcommand", "renewcommand", "providecommand", "DeclareMathOperator"}
REF_COMMANDS = {
    "ref",
    "eqref",
    "autoref",
    "cref",
    "Cref",
    "nameref",
    "vref",
    "Vref",
    "pageref",
    "subref",
}
CITE_COMMANDS = {
    "cite",
    "citep",
    "citet",
    "parencite",
    "textcite",
    "autocite",
    "footcite",
    "nocite",
}


@lru_cache(maxsize=1)
def context():
    ctx = get_default_latex_context_db()
    specs = [MacroSpec(name, "*{") for name in REF_COMMANDS]
    specs += [
        MacroSpec(name, "{")
        for name in (
            "input",
            "include",
            "subfile",
            "label",
            "bibliography",
            "addbibresource",
            "graphicspath",
        )
    ]
    specs += [MacroSpec(name, "*[[{") for name in CITE_COMMANDS]
    specs += [
        MacroSpec("includegraphics", "*[{"),
        MacroSpec("caption", "*[{"),
        MacroSpec("subcaption", "*[{"),
        MacroSpec("captionof", "{{"),
        MacroSpec("import", "{{"),
        MacroSpec("subimport", "{{"),
    ]
    ctx.add_context_category("tex-mcp", macros=specs, prepend=True)
    return ctx


def parse_nodes(text, diagnostics=None):
    try:
        return LatexWalker(text, latex_context=context(), tolerant_parsing=False).get_latex_nodes()[
            0
        ]
    except (LatexWalkerParseError, IndexError, ValueError) as exc:
        if diagnostics is not None:
            diagnostics.append({"code": "SYNTAX_RECOVERY", "message": str(exc)[:500]})
        try:
            return LatexWalker(
                text, latex_context=context(), tolerant_parsing=True
            ).get_latex_nodes()[0]
        except (LatexWalkerParseError, IndexError, ValueError):
            raise TexError("PARSE_FAILED", "Cannot recover a TeX syntax tree") from None


def args(node):
    return list(getattr(getattr(node, "nodeargd", None), "argnlist", []) or [])


def argument(node, text):
    if node is None:
        return None
    raw = text[node.pos : node.pos + node.len]
    if isinstance(node, LatexGroupNode):
        return raw[1:-1]
    return raw


def required_args(node, text):
    return [
        argument(a, text)
        for a in args(node)
        if isinstance(a, LatexGroupNode) and a.delimiters == ("{", "}")
    ]


def children(node):
    return getattr(node, "nodelist", None) or []


class Processor:
    def __init__(self, root, limit=4_000_000):
        self.root, self.limit = Path(root), limit
        self.parts, self.segments, self.diagnostics = [], [], []
        self.length = 0
        self.macros = {}
        self.file_texts = {}
        self.expansions = 0
        self.unknown_names = set()

    def origin(self, path, start, end):
        text = self.file_texts[str(path)]
        return {
            "file": str(path),
            "start": start,
            "end": end,
            "line": text.count("\n", 0, start) + 1,
            "end_line": text.count("\n", 0, end) + 1,
        }

    def emit(self, text, origin, expanded=False, uncertain=False):
        if not text:
            return
        if self.length + len(text) > self.limit:
            raise TexError("PARSE_BUDGET", "Expanded text character limit reached")
        self.parts.append(text)
        self.segments.append(
            {
                "start": self.length,
                "end": self.length + len(text),
                "origin": origin,
                "expanded": expanded,
                "uncertain": uncertain,
            }
        )
        self.length += len(text)

    def file(self, relative, macros=None, stack=()):
        relative = str(Path(relative))
        if relative in stack:
            self.diagnostics.append({"code": "INPUT_CYCLE", "file": relative, "stack": list(stack)})
            return
        if len(stack) > 40:
            raise TexError("PARSE_BUDGET", "Include depth exceeded")
        path = contained(self.root, relative)
        if not path.is_file():
            self.diagnostics.append({"code": "MISSING_INPUT", "file": relative})
            return
        data = path.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1")
            self.diagnostics.append(
                {"code": "ENCODING_FALLBACK", "file": relative, "encoding": "latin-1"}
            )
        self.file_texts[relative] = text
        self.process(
            text,
            parse_nodes(text, self.diagnostics),
            relative,
            self.macros if macros is None else macros,
            stack + (relative,),
        )

    def process(
        self, text, nodes, file, macros, stack, override=None, depth=0, inherited_uncertain=False
    ):
        if depth > 30:
            raise TexError("PARSE_BUDGET", "Macro/group expansion depth exceeded")
        skip_until = -1
        conditions = []
        for node in nodes:
            if node.pos < skip_until:
                continue
            start, end = node.pos, node.pos + node.len
            origin = override or self.origin(file, start, end)
            raw = text[start:end]
            name = getattr(node, "macroname", None)
            if (
                name in ("iftrue", "iffalse")
                or name
                and name.startswith("if")
                and name not in macros
                and not args(node)
            ):
                conditions.append(
                    True if name == "iftrue" else False if name == "iffalse" else None
                )
                if conditions[-1] is None:
                    self.diagnostics.append(
                        {"code": "UNKNOWN_CONDITION", "command": name, "origin": origin}
                    )
                continue
            if name == "else" and conditions:
                if conditions[-1] is not None:
                    conditions[-1] = not conditions[-1]
                continue
            if name == "fi" and conditions:
                conditions.pop()
                continue
            if False in conditions:
                continue
            uncertain = inherited_uncertain or None in conditions
            if isinstance(node, LatexCommentNode):
                self.emit("\n" if "\n" in raw else "", origin, override is not None, uncertain)
                continue
            if name in DEFINITIONS:
                values = args(node)
                try:
                    macro_name = argument(values[1], text).strip().lstrip("\\")
                    if name == "DeclareMathOperator":
                        definition = {
                            "nargs": 0,
                            "default": None,
                            "body": "\\operatorname{" + argument(values[2], text) + "}",
                        }
                    else:
                        definition = {
                            "nargs": int(argument(values[2], text) or 0),
                            "default": argument(values[3], text),
                            "body": argument(values[4], text),
                        }
                    if not uncertain and (name != "providecommand" or macro_name not in macros):
                        macros[macro_name] = {**definition, "origin": origin}
                except (IndexError, AttributeError, ValueError, TypeError):
                    self.diagnostics.append({"code": "UNSUPPORTED_DEFINITION", "origin": origin})
                self.emit(raw, origin, override is not None, uncertain)
                continue
            if name in ("def", "gdef", "edef", "xdef"):
                match = re.match(
                    r"\\(?:def|gdef|edef|xdef)\s*\\([A-Za-z@]+)((?:#[1-9])*)\s*", text[start:]
                )
                if match:
                    position = start + match.end()
                    try:
                        group, pos, length = LatexWalker(
                            text, latex_context=context(), tolerant_parsing=False
                        ).get_latex_expression(position)
                        if not isinstance(group, LatexGroupNode):
                            raise TypeError()
                        full_end = pos + length
                        definition_origin = override or self.origin(file, start, full_end)
                        params = re.findall(r"#([1-9])", match.group(2))
                        if (
                            name == "def"
                            and params == [str(i) for i in range(1, len(params) + 1)]
                            and not uncertain
                        ):
                            macros[match.group(1)] = {
                                "nargs": len(params),
                                "default": None,
                                "body": argument(group, text),
                                "origin": definition_origin,
                            }
                        else:
                            self.diagnostics.append(
                                {
                                    "code": "UNSUPPORTED_DEFINITION",
                                    "command": name,
                                    "origin": definition_origin,
                                }
                            )
                        self.emit(
                            "[Definition retained in original source]",
                            definition_origin,
                            True,
                            uncertain,
                        )
                        skip_until = full_end
                        continue
                    except (ValueError, TypeError, IndexError, LatexWalkerParseError):
                        pass
            if name in ("def", "gdef", "edef", "xdef", "let", "newenvironment", "renewenvironment"):
                self.diagnostics.append(
                    {"code": "UNSUPPORTED_DEFINITION", "command": name, "origin": origin}
                )
                self.emit(raw, origin, override is not None, uncertain)
                continue
            if name in ("input", "include", "subfile", "import", "subimport") and not uncertain:
                values = required_args(node, text)
                target = values[-1] if values else ""
                prefix = values[0] if name in ("import", "subimport") and len(values) > 1 else ""
                if not target or "\\" in target:
                    self.diagnostics.append(
                        {"code": "DYNAMIC_INPUT", "origin": origin, "target": target}
                    )
                    self.emit(raw, origin, override is not None, uncertain)
                    continue
                relative = Path(file).parent / prefix / target
                candidates = (
                    [relative] if relative.suffix else [relative.with_suffix(".tex"), relative]
                )
                if Path(file).parent != Path("."):
                    candidates += [Path(target).with_suffix(".tex")]
                found = None
                for candidate in candidates:
                    path = contained(self.root, candidate)
                    if path.is_file():
                        found = path.relative_to(self.root)
                        break
                if found is None:
                    self.diagnostics.append(
                        {"code": "MISSING_INPUT", "origin": origin, "target": target}
                    )
                    self.emit(raw, origin, override is not None, uncertain)
                else:
                    self.file(found, macros, stack)
                continue
            if name in macros and not uncertain:
                definition = macros[name]
                try:
                    position = start + len(name) + 1
                    walker = LatexWalker(text, latex_context=context(), tolerant_parsing=False)
                    values = []
                    if definition["default"] is not None:
                        optional = walker.get_latex_maybe_optional_arg(position)
                        if optional:
                            item, p, length = optional
                            values.append(argument(item, text))
                            position = p + length
                        else:
                            values.append(definition["default"])
                    for _ in range(definition["nargs"] - len(values)):
                        item, p, length = walker.get_latex_expression(position, strict_braces=True)
                        values.append(argument(item, text))
                        position = p + length
                    replacement = definition["body"]
                    for index, value in reversed(list(enumerate(values, 1))):
                        replacement = replacement.replace("#" + str(index), value)
                    if not values:
                        position = end
                    if replacement == raw or "\\" + name in replacement:
                        raise ValueError("Recursive macro")
                    call_origin = override or self.origin(file, start, position)
                    self.expansions += 1
                    self.process(
                        replacement,
                        parse_nodes(replacement, self.diagnostics),
                        file,
                        macros.copy(),
                        stack,
                        call_origin,
                        depth + 1,
                    )
                    skip_until = max(end, position)
                    continue
                except (
                    ValueError,
                    IndexError,
                    TypeError,
                    LatexWalkerParseError,
                    LatexWalkerEndOfStream,
                ):
                    self.diagnostics.append(
                        {"code": "UNEXPANDED_MACRO", "command": name, "origin": origin}
                    )
            if isinstance(node, LatexEnvironmentNode):
                if node.environmentname in OPAQUE:
                    if node.environmentname != "comment":
                        self.emit(raw, origin, override is not None, uncertain)
                    continue
                nested = children(node)
                if nested:
                    first, last = nested[0].pos, nested[-1].pos + nested[-1].len
                    self.emit(
                        text[start:first],
                        override or self.origin(file, start, first),
                        override is not None,
                        uncertain,
                    )
                    self.process(
                        text, nested, file, macros.copy(), stack, override, depth + 1, uncertain
                    )
                    self.emit(
                        text[last:end],
                        override or self.origin(file, last, end),
                        override is not None,
                        uncertain,
                    )
                else:
                    self.emit(raw, origin, override is not None, uncertain)
                continue
            if isinstance(node, LatexGroupNode):
                self.emit(raw[:1], origin, override is not None, uncertain)
                self.process(
                    text, children(node), file, macros.copy(), stack, override, depth + 1, uncertain
                )
                self.emit(raw[-1:], origin, override is not None, uncertain)
                continue
            if (
                name
                and context().get_macro_spec(name) is None
                and name not in macros
                and (name, file) not in self.unknown_names
            ):
                self.unknown_names.add((name, file))
                self.diagnostics.append(
                    {"code": "UNKNOWN_MACRO", "command": name, "origin": origin}
                )
            groups = [g for g in args(node) if isinstance(g, LatexGroupNode)]
            if groups:
                previous = start
                for group in groups:
                    self.emit(
                        text[previous : group.pos + 1],
                        override or self.origin(file, previous, group.pos + 1),
                        override is not None,
                        uncertain,
                    )
                    self.process(
                        text,
                        children(group),
                        file,
                        macros.copy(),
                        stack,
                        override,
                        depth + 1,
                        uncertain,
                    )
                    previous = group.pos + group.len - 1
                    self.emit(
                        text[previous : previous + 1],
                        override or self.origin(file, previous, previous + 1),
                        override is not None,
                        uncertain,
                    )
                    previous += 1
                self.emit(
                    text[previous:end],
                    override or self.origin(file, previous, end),
                    override is not None,
                    uncertain,
                )
            elif children(node):
                nested = children(node)
                first = nested[0].pos
                last = nested[-1].pos + nested[-1].len
                self.emit(
                    text[start:first],
                    override or self.origin(file, start, first),
                    override is not None,
                    uncertain,
                )
                self.process(
                    text, nested, file, macros.copy(), stack, override, depth + 1, uncertain
                )
                self.emit(
                    text[last:end],
                    override or self.origin(file, last, end),
                    override is not None,
                    uncertain,
                )
            else:
                self.emit(raw, origin, override is not None, uncertain)
        if conditions:
            self.diagnostics.append({"code": "UNBALANCED_CONDITION", "file": file})

    def result(self):
        return "".join(self.parts), self.segments, self.diagnostics


def locations(segments, start, end, text=None):
    origins = []
    first_segment = bisect_right(segments, start, key=lambda segment: segment["end"])
    for index in range(first_segment, len(segments)):
        segment = segments[index]
        if segment["start"] >= end:
            break
        origin = dict(segment["origin"])
        if (
            text is not None
            and not segment["expanded"]
            and origin["end"] - origin["start"] == segment["end"] - segment["start"]
        ):
            first, last = max(start, segment["start"]), min(end, segment["end"])
            origin["line"] += text.count("\n", segment["start"], first)
            origin["end_line"] = origin["line"] + text.count("\n", first, last)
            origin["start"] += first - segment["start"]
            origin["end"] -= segment["end"] - last
        origin["expanded"] = segment["expanded"]
        origin["uncertain"] = segment["uncertain"]
        if origin not in origins:
            origins.append(origin)
    return origins
