"""Version-local citation records; external paper identity is deliberately separate."""

import re
from pathlib import Path

from pybtex.database import parse_string
from pybtex.exceptions import PybtexError

from .acquire import contained


def read_references(root, declarations, cited_keys, locations_for):
    records, diagnostics = {}, []
    files = []
    for value, origin in declarations:
        for name in value.split(","):
            name = name.strip()
            candidate = Path(origin["file"]).parent / name
            if not candidate.suffix:
                candidate = candidate.with_suffix(".bib")
            path = contained(root, candidate)
            if not path.is_file():
                path = contained(root, Path(name).with_suffix(".bib"))
            if path.is_file():
                files.append(path)
            else:
                diagnostics.append({"code": "MISSING_BIB_FILE", "path": str(candidate)})
    if not files:
        files = list(root.rglob("*.bib"))
        if len(files) > 1:
            diagnostics.append(
                {
                    "code": "BIB_DISCOVERY",
                    "message": "No explicit bibliography matched; scanned source .bib files.",
                }
            )
    for file in dict.fromkeys(files):
        try:
            data = parse_string(file.read_text(encoding="utf-8"), "bibtex")
        except (PybtexError, UnicodeError, ValueError) as exc:
            diagnostics.append(
                {
                    "code": "BIB_PARSE_FAILED",
                    "file": str(file.relative_to(root)),
                    "message": str(exc)[:400],
                }
            )
            continue
        for key, entry in data.entries.items():
            fields = dict(entry.fields)
            authors = [str(person) for person in entry.persons.get("author", [])]
            item = {
                "key": key,
                "type": entry.type,
                "fields": fields,
                "authors": authors,
                "source": {"file": str(file.relative_to(root)), "format": "bib"},
            }
            if key in records:
                records[key].setdefault("alternatives", []).append(item)
                diagnostics.append({"code": "DUPLICATE_CITATION_KEY", "key": key})
            else:
                records[key] = item
    # BBL and inline bibliography supplement missing keys, rather than shadowing them.
    for file in sorted(list(root.rglob("*.bbl")) + list(root.rglob("*.tex"))):
        path = contained(root, file.relative_to(root))
        text = path.read_text(encoding="utf-8", errors="replace")
        matches = list(re.finditer(r"\\bibitem\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}", text))
        for index, match in enumerate(matches):
            end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else text.find("\\end{thebibliography}", match.end())
            )
            if end < 0:
                end = len(text)
            key = match.group(1)
            item = {
                "key": key,
                "type": None,
                "fields": {},
                "authors": [],
                "text": text[match.end() : end].strip(),
                "source": {
                    "file": str(path.relative_to(root)),
                    "format": "bbl" if file.suffix == ".bbl" else "inline",
                    "line": text.count("\n", 0, match.start()) + 1,
                },
            }
            if key not in records:
                records[key] = item
            else:
                records[key].setdefault("rendered_sources", []).append(item)
    for key in cited_keys:
        if key == "*":
            continue
        records.setdefault(
            key, {"key": key, "fields": {}, "authors": [], "source": None, "status": "missing"}
        )
    for key, item in records.items():
        item["cited_at"] = locations_for(key)
        item["cited_in_body"] = any(
            location.get("command") != "nocite" for location in item["cited_at"]
        )
        item["included_by_nocite"] = "*" in cited_keys or any(
            location.get("command") == "nocite" for location in item["cited_at"]
        )
        item["status"] = item.get("status", "parsed")
        fields = item["fields"]
        identifiers = []
        if fields.get("doi"):
            identifiers.append("doi:" + fields["doi"].removeprefix("https://doi.org/").strip())
        if fields.get("eprint") and (
            fields.get("archiveprefix", "").lower() == "arxiv"
            or re.fullmatch(r"\d{4}\.\d{4,5}(v\d+)?", fields["eprint"])
        ):
            identifiers.append("arxiv:" + fields["eprint"])
        evidence_text = item.get("text", "") + " " + fields.get("url", "")
        evidence_text += " " + " ".join(r.get("text", "") for r in item.get("rendered_sources", []))
        identifiers += [
            "doi:" + m
            for m in re.findall(r"(?<![A-Za-z0-9])(10\.\d{4,9}/[^\s{}\\<>]+)", evidence_text)
        ]
        identifiers += [
            "arxiv:" + m
            for m in re.findall(
                r"(?:arxiv:\s*|arxiv\.org/(?:abs|pdf)/)(\d{4}\.\d{4,5}(?:v\d+)?)",
                evidence_text,
                re.IGNORECASE,
            )
        ]
        item["identifiers_from_source"] = list(dict.fromkeys(identifiers))
        item["external_identity"] = "unverified"
    missing = [key for key in cited_keys if key != "*" and records[key]["status"] == "missing"]
    if missing:
        diagnostics.append({"code": "MISSING_CITATIONS", "keys": missing})
    return records, diagnostics
