"""Read source HTML/JATS structure without reconstructing it from PDF pixels."""

import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup, Tag
from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from .models import PdfError


def parse_structured(data, format_, base_url=None):
    if len(data) > 16_000_000:
        raise PdfError("STRUCTURE_LIMIT", "Structured source exceeds 16 MB")
    if format_ == "xml":
        try:
            ElementTree.fromstring(data)
        except (ElementTree.ParseError, DefusedXmlException, ValueError) as error:
            raise PdfError(
                "INVALID_XML", "Invalid or unsafe XML", reason=type(error).__name__
            ) from None
    soup = BeautifulSoup(data, "xml" if format_ == "xml" else "html.parser")
    root = soup.find("article") or soup.find("body") or soup
    if len(soup.find_all()) > 100_000:
        raise PdfError("STRUCTURE_LIMIT", "Too many source elements")
    for node in root.find_all(["script", "style", "nav", "header", "footer"]):
        node.decompose()
    blocks, objects, sections, references, diagnostics, stack = [], [], [], [], [], []

    def content(node):
        copy = BeautifulSoup(str(node), "html.parser")
        for math in copy.find_all("math"):
            annotation = math.find(
                "annotation", attrs={"encoding": re.compile("tex", re.IGNORECASE)}
            )
            latex = math.get("alttext") or (annotation.get_text() if annotation else None)
            math.replace_with(" $" + latex + "$ " if latex else math.get_text(" ", strip=True))
        return copy.get_text(" ", strip=True)

    def emit(node, kind, text=None, **extra):
        aliases = [n.get("id") for n in [node, *node.find_all(id=True)] if n.get("id")]
        targets = []
        for anchor in node.find_all(["a", "xref"]):
            href = anchor.get("href", "")
            target = anchor.get("rid") or (href[1:] if href.startswith("#") else None)
            if target:
                targets.extend(target.split())
        value = {
            "block_id": f"block:{len(blocks) + 1}",
            "kind": kind,
            "text": text if text is not None else content(node),
            "page": None,
            "bbox": None,
            "source_id": node.get("id"),
            "source_aliases": list(dict.fromkeys(aliases)),
            "section_ids": [s[1] for s in stack],
            "reference_targets": list(dict.fromkeys(targets)),
            "provenance": "source_structure",
            "links": [
                {"href": a.get("href") or a.get("xlink:href"), "text": a.get_text(" ", strip=True)}
                for a in node.find_all(["a", "ext-link"])
                if a.get("href") or a.get("xlink:href")
            ],
            **extra,
        }
        inline = []
        for math in ([node] if node.name == "math" else []) + node.find_all("math"):
            annotation = math.find(
                "annotation", attrs={"encoding": re.compile("tex", re.IGNORECASE)}
            )
            inline.append(
                {
                    "mathml": str(math),
                    "latex_from_source": math.get("alttext")
                    or (annotation.get_text() if annotation else None),
                }
            )
        if inline:
            value["math"] = inline
        blocks.append(value)
        return value

    def walk(node):
        if not isinstance(node, Tag):
            return
        name = node.name.split(":")[-1]
        classes = node.get("class", [])
        if isinstance(classes, str):
            classes = classes.split()
        if name in ("section", "sec"):
            previous = list(stack)
            for child in node.children:
                walk(child)
            stack[:] = previous
            return
        heading = bool(re.fullmatch(r"h[1-6]", name)) or (
            name == "title" and node.parent.name in ("sec", "body")
        )
        if heading:
            level = int(name[1]) if name.startswith("h") else len(node.find_parents("sec")) + 1
            while stack and stack[-1][0] >= level:
                stack.pop()
            ident = node.parent.get("id") or node.get("id") or f"section:{len(sections) + 1}"
            section = {
                "id": ident,
                "title": content(node),
                "level": level,
                "parent": stack[-1][1] if stack else None,
                "boundary_basis": "source_structure",
                "page": None,
            }
            sections.append(section)
            stack.append((level, ident))
            emit(node, "heading", level=level)
            return
        if name in ("figure", "fig", "table-wrap", "table", "disp-formula") or (
            name == "math" and node.get("display") == "block"
        ):
            table = node if name == "table" else node.find("table")
            kind = (
                "table" if table else "equation" if name in ("math", "disp-formula") else "figure"
            )
            caption = node.find(["figcaption", "caption"])
            obj = emit(
                node, kind, caption=content(caption) if caption else "", source_markup=str(node)
            )
            obj["object_id"] = "object:" + (node.get("id") or str(len(objects) + 1))
            if table:
                obj["rows"] = [
                    [
                        {
                            "text": content(c),
                            "rowspan": c.get("rowspan", "1"),
                            "colspan": c.get("colspan", "1"),
                        }
                        for c in row.find_all(["th", "td"], recursive=False)
                    ]
                    for row in table.find_all("tr")
                ]
            assets = []
            for image in node.find_all(["img", "graphic"]):
                source = image.get("src") or image.get("xlink:href") or image.get("href")
                if source:
                    url = urljoin(base_url or "", source)
                    assets.append(
                        {
                            "source": url,
                            "status": "remote_reference"
                            if urlsplit(url).scheme in ("http", "https")
                            else "local_reference",
                            "alt": image.get("alt", ""),
                        }
                    )
            obj["assets"] = assets
            objects.append(obj)
            return
        if name == "ref" or "ltx_bibitem" in classes:
            references.append(emit(node, "reference", reference_key=node.get("id")))
            return
        if name in ("p", "pre") or (name == "li" and not node.find(["p", "ref"])):
            emit(node, "text")
            return
        for child in node.children:
            walk(child)

    walk(root)
    if not blocks:
        raise PdfError("NO_STRUCTURE", "No readable article content found")
    if soup.select(".ltx_ERROR, .ltx_missing"):
        diagnostics.append(
            {"code": "SOURCE_CONVERSION_ERROR", "message": "HTML includes conversion error markers"}
        )
    known_ids = {n.get("id") for n in root.find_all(id=True)}
    if root.get("id"):
        known_ids.add(root.get("id"))
    unresolved = sorted(
        {
            target
            for block in blocks
            for target in block["reference_targets"]
            if target not in known_ids
        }
    )
    if unresolved:
        diagnostics.append({"code": "SOURCE_LINK_UNRESOLVED", "targets": unresolved})
    title_node = soup.find("article-title") or soup.find("title") or soup.find("h1")
    return {
        "blocks": blocks,
        "objects": objects,
        "sections": sections,
        "references": references,
        "diagnostics": diagnostics,
        "metadata": {"title": title_node.get_text(" ", strip=True) if title_node else ""},
        "reading_order": "source_structure",
        "coverage": "partial" if diagnostics else "source_structure_not_independently_verified",
    }
