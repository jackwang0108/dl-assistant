"""Structural document index: sections, objects, labels, and direct reference edges."""

import re
from pathlib import Path

from pylatexenc.latexwalker import (
    LatexEnvironmentNode,
    LatexGroupNode,
    LatexMacroNode,
    LatexMathNode,
)

from .acquire import contained
from .bibliography import read_references
from .models import TexError
from .syntax import (
    CITE_COMMANDS,
    DEFINITIONS,
    OPAQUE,
    REF_COMMANDS,
    Processor,
    args,
    argument,
    children,
    locations,
    parse_nodes,
    required_args,
)

LEVELS = {
    "part": 0,
    "chapter": 1,
    "section": 2,
    "subsection": 3,
    "subsubsection": 4,
    "paragraph": 5,
}
OBJECTS = {
    "figure": "figure",
    "figure*": "figure",
    "wrapfigure": "figure",
    "table": "table",
    "table*": "table",
    "wraptable": "table",
    "longtable": "table",
    "equation": "equation",
    "equation*": "equation",
    "align": "equation",
    "align*": "equation",
    "gather": "equation",
    "gather*": "equation",
    "multline": "equation",
    "multline*": "equation",
    "eqnarray": "equation",
    "subequations": "equation",
}


def main_candidates(root):
    candidates = []
    for file in sorted(root.rglob("*.tex")):
        text = file.read_text(encoding="utf-8", errors="replace")
        # Inspect syntax nodes so commented documentclass does not qualify.
        nodes = parse_nodes(text, [])
        if any(isinstance(n, LatexMacroNode) and n.macroname == "documentclass" for n in nodes):
            candidates.append(str(file.relative_to(root)))
    return candidates


def parse_document(root, main_tex=None, max_chars=4_000_000):
    root = Path(root).resolve()
    candidates = main_candidates(root)
    if main_tex is None:
        if len(candidates) != 1:
            raise TexError(
                "MAIN_AMBIGUOUS" if candidates else "MAIN_NOT_FOUND",
                "Choose a document entry explicitly",
                candidates=candidates,
            )
        main_tex = candidates[0]
    contained(root, main_tex)
    if not (root / main_tex).is_file():
        raise TexError("MAIN_NOT_FOUND", "Requested entry does not exist")
    processor = Processor(root, max_chars)
    processor.file(main_tex)
    text, segments, diagnostics = processor.result()
    nodes = parse_nodes(text, diagnostics)
    sections, objects, edges, labels, declarations = [], [], [], {}, []
    body_start, body_end = 0, len(text)
    counters = {k: 0 for k in ("figure", "table", "equation")}
    section_events = []
    graphics_dirs = []

    def locate(start, end):
        return locations(segments, start, end)

    def caption_kind(node):
        if isinstance(node, LatexMacroNode) and node.macroname == "captionof":
            values = required_args(node, text)
            return values[0] if values and values[0] in ("figure", "table") else None
        if isinstance(node, LatexEnvironmentNode) and node.environmentname in OPAQUE | set(OBJECTS):
            return None
        for child in children(node):
            found = caption_kind(child)
            if found:
                return found
        return None

    def visit(node, owner=None):
        nonlocal body_start, body_end
        start, end = node.pos, node.pos + node.len
        if isinstance(node, LatexEnvironmentNode):
            env = node.environmentname
            if env in OPAQUE:
                return
            if env == "document":
                nested = children(node)
                if nested:
                    body_start, body_end = nested[0].pos, nested[-1].pos + nested[-1].len
            if env in OBJECTS:
                kind = OBJECTS[env]
                counters[kind] += 1
                obj = {
                    "object_id": f"{kind}:{counters[kind]}",
                    "kind": kind,
                    "environment": env,
                    "start": start,
                    "end": end,
                    "labels": [],
                    "caption": "",
                    "assets": [],
                    "source_locations": locate(start, end),
                    "number_status": "source_order_not_compiled",
                }
                objects.append(obj)
                owner = obj
            elif env in ("abstract",):
                section_events.append(
                    {
                        "id": "abstract",
                        "level": -1,
                        "title": "Abstract",
                        "start": start,
                        "exact_end": end,
                    }
                )
        bounded_caption = (
            isinstance(node, LatexEnvironmentNode)
            and node.environmentname in ("center", "minipage", "strip", "flushleft", "flushright")
        ) or isinstance(node, LatexGroupNode)
        if owner is None and bounded_caption:
            kind = caption_kind(node)
            if kind:
                counters[kind] += 1
                owner = {
                    "object_id": f"{kind}:{counters[kind]}",
                    "kind": kind,
                    "environment": "captionof_container",
                    "start": start,
                    "end": end,
                    "labels": [],
                    "caption": "",
                    "assets": [],
                    "source_locations": locate(start, end),
                    "number_status": "source_order_not_compiled",
                }
                objects.append(owner)
        if isinstance(node, LatexMacroNode):
            name = node.macroname
            if name in DEFINITIONS or name in (
                "def",
                "gdef",
                "edef",
                "newenvironment",
                "renewenvironment",
            ):
                return
            values = required_args(node, text)
            if name in LEVELS and values:
                section_events.append(
                    {
                        "level": LEVELS[name],
                        "title": values[-1],
                        "start": start,
                        "starred": any(
                            argument(a, text) == "*" for a in args(node) if a is not None
                        ),
                    }
                )
            elif name == "appendix":
                section_events.append({"appendix": True, "start": start})
            elif name == "label" and values:
                key = values[0]
                target = owner["object_id"] if owner else None
                if key in labels:
                    diagnostics.append(
                        {"code": "DUPLICATE_LABEL", "label": key, "locations": locate(start, end)}
                    )
                    labels[key].append({"target": target, "position": start})
                else:
                    labels[key] = [{"target": target, "position": start}]
                if owner:
                    owner["labels"].append(key)
            elif name in REF_COMMANDS and values:
                for key in values[-1].split(","):
                    edges.append(
                        {
                            "kind": "object_reference",
                            "key": key.strip(),
                            "start": start,
                            "end": end,
                            "command": name,
                            "source_locations": locate(start, end),
                        }
                    )
            elif name in CITE_COMMANDS and values:
                for key in values[-1].split(","):
                    edges.append(
                        {
                            "kind": "citation",
                            "key": key.strip(),
                            "start": start,
                            "end": end,
                            "command": name,
                            "source_locations": locate(start, end),
                        }
                    )
            elif name in ("caption", "subcaption") and values and owner:
                owner["caption"] += ("\n" if owner["caption"] else "") + values[-1]
            elif name == "captionof" and len(values) > 1:
                kind = values[0]
                if owner is not None and owner["kind"] == kind:
                    owner["caption"] += ("\n" if owner["caption"] else "") + values[1]
                elif kind in ("figure", "table"):
                    diagnostics.append(
                        {
                            "code": "CAPTIONOF_NEEDS_SCOPE",
                            "locations": locate(start, end),
                            "message": "Non-float caption retained; surrounding object boundary not assumed.",
                        }
                    )
            elif name == "graphicspath" and values:
                graphics_dirs.extend(re.findall(r"\{([^}]+)\}", values[-1]))
            elif name == "includegraphics" and values and owner:
                ref = values[-1]
                origin = locate(start, end)
                options = [ref]
                if not Path(ref).suffix:
                    options = [
                        ref + ext for ext in (".pdf", ".png", ".jpg", ".jpeg", ".eps", ".svg")
                    ]
                roots = [Path(origin[0]["file"]).parent if origin else Path("."), Path(".")]
                roots += [Path(x) for x in graphics_dirs]
                matches = []
                for directory in roots:
                    for option in options:
                        candidate = contained(root, directory / option)
                        if candidate.is_file() and str(candidate.relative_to(root)) not in matches:
                            matches.append(str(candidate.relative_to(root)))
                owner["assets"].append(
                    {
                        "reference": ref,
                        "paths": matches,
                        "status": "resolved"
                        if len(matches) == 1
                        else "ambiguous"
                        if matches
                        else "missing",
                        "locations": origin,
                        "options": text[start:end],
                    }
                )
            elif name in ("bibliography", "addbibresource") and values:
                origins = locate(start, end)
                declarations.append((values[-1], origins[0] if origins else {"file": main_tex}))
            for group in args(node):
                if group is not None:
                    for child in children(group):
                        visit(child, owner)
            return
        if isinstance(node, LatexMathNode) and node.delimiters in [("\\[", "\\]"), ("$$", "$$")]:
            counters["equation"] += 1
            objects.append(
                {
                    "object_id": f"equation:{counters['equation']}",
                    "kind": "equation",
                    "environment": "display_math",
                    "start": start,
                    "end": end,
                    "labels": [],
                    "caption": "",
                    "assets": [],
                    "source_locations": locate(start, end),
                    "number_status": "unnumbered_display",
                }
            )
            owner = objects[-1]
        for child in children(node):
            visit(child, owner)

    for node in nodes:
        visit(node)
    section_events.sort(key=lambda e: e["start"])
    numeric = [0] * 6
    top = None
    appendix = False
    star = 0
    for event in section_events:
        if event.get("appendix"):
            appendix = True
            numeric = [0] * 6
            continue
        if event.get("id") == "abstract":
            section = {**event, "end": event["exact_end"], "parent": None}
        else:
            level = event["level"]
            top = level if top is None else min(top, level)
            if event.get("starred"):
                star += 1
                ident = f"unnumbered:{star}"
            else:
                numeric[level] += 1
                for n in range(level + 1, 6):
                    numeric[n] = 0
                pieces = [str(numeric[n]) for n in range(top, level + 1)]
                if appendix:
                    pieces[0] = (
                        chr(64 + numeric[top])
                        if numeric[top] <= 26
                        else "appendix" + str(numeric[top])
                    )
                ident = ".".join(pieces)
            section = {**event, "id": ident, "end": body_end, "parent": None}
        sections.append(section)
    for i, section in enumerate(sections):
        section["source_locations"] = locate(
            section["start"], section.get("exact_end", section["start"] + 1)
        )
        if section["id"] == "abstract":
            continue
        for following in sections[i + 1 :]:
            if following["level"] >= 0 and following["level"] <= section["level"]:
                section["end"] = following["start"]
                break
        ancestors = [
            s
            for s in sections[:i]
            if s["level"] >= 0 and s["level"] < section["level"] and s["end"] > section["start"]
        ]
        section["parent"] = ancestors[-1]["id"] if ancestors else None

    def section_at(position):
        found = [s for s in sections if s["start"] <= position < s["end"]]
        return max(found, key=lambda s: s["level"])["id"] if found else None

    for obj in objects:
        obj["section_id"] = section_at(obj["start"])
        obj["conditional_status"] = (
            "uncertain"
            if any(loc.get("uncertain") for loc in obj["source_locations"])
            else "not_flagged"
        )
    for edge in edges:
        edge["section_id"] = section_at(edge["start"])
        if edge["kind"] == "object_reference":
            targets = labels.get(edge["key"], [])
            if len(targets) == 1:
                edge["target"] = targets[0]["target"] or section_at(targets[0]["position"])
                edge["status"] = "resolved" if edge["target"] else "unresolved"
            else:
                edge["target"] = None
                edge["status"] = "ambiguous" if targets else "unresolved"
            if edge["status"] != "resolved":
                diagnostics.append(
                    {
                        "code": "UNRESOLVED_REFERENCE",
                        "key": edge["key"],
                        "locations": edge["source_locations"],
                    }
                )
    cited = list(dict.fromkeys(e["key"] for e in edges if e["kind"] == "citation"))
    references, bib_diagnostics = read_references(
        root,
        declarations,
        cited,
        lambda key: [
            {
                "section_id": e["section_id"],
                "command": e["command"],
                "locations": e["source_locations"],
            }
            for e in edges
            if e["kind"] == "citation" and e["key"] == key
        ],
    )
    diagnostics += bib_diagnostics
    return {
        "main_tex": main_tex,
        "main_candidates": candidates,
        "text": text,
        "segments": segments,
        "sections": sections,
        "objects": objects,
        "edges": edges,
        "labels": labels,
        "references": references,
        "body_start": body_start,
        "body_end": body_end,
        "diagnostics": diagnostics,
        "macro_expansions": processor.expansions,
        "numbering": "Structural source numbering; compiled numbering is not asserted.",
    }
