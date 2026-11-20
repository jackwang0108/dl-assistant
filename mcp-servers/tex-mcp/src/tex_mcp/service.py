"""Version-bound document operations and bounded section-plus-attachments reading."""

import base64
import json
import os
import tempfile
from pathlib import Path

import regex

from . import images
from .acquire import Acquisition, arxiv_ref, contained, sha
from .document import parse_document
from .models import WARNING, TexError
from .storage import Storage, digest
from .syntax import locations


class Service:
    def __init__(self, cache_dir=None, client=None, interval=3.0):
        self.storage = Storage(cache_dir)
        self.client, self.interval = client, interval

    def capabilities(self):
        return {
            "api_version": 2,
            "source_types": ["arxiv", "local_directory"],
            "views": ["source", "expanded"],
            "objects": ["figure", "table", "equation"],
            "section_attachments": "owned objects plus directly referenced objects, deduplicated",
            "bibliography": "version-local citation evidence; external identity remains unverified",
            "isolated_tex_configured": bool(os.getenv("TEX_MCP_RENDER_IMAGE")),
            "render_methods": [
                "source_asset",
                "explicit_original_pdf_crop",
                "configured_isolated_tex",
            ],
            "limitations": [
                "No complete TeX interpreter or compiled numbering guarantee.",
                "Unknown conditionals and unsupported definitions are diagnostic limitations.",
            ],
        }

    def open(self, source, main_tex=None, limits=None, refresh=False):
        operation = Acquisition(limits, self.client, self.interval)
        metadata = None
        if not Path(source).expanduser().is_dir():
            ident, revision = arxiv_ref(source)
            cached = (
                self.storage.find_arxiv(ident, revision, main_tex)
                if revision and not refresh
                else None
            )
            if cached is None:
                metadata = operation.resolve_arxiv(source)
                cached = (
                    self.storage.find_arxiv(ident, metadata["actual_version"], main_tex)
                    if not refresh
                    else None
                )
            if cached:
                self.document(cached["document_id"])
                return {**self.summary(cached), "cache_state": "hit", "usage": operation.usage()}
        with tempfile.TemporaryDirectory(prefix=".stage-", dir=self.storage.root) as temporary:
            stage = Path(temporary)
            metadata = operation.acquire(source, stage, metadata)
            text_bytes = sum(
                p.stat().st_size
                for p in stage.rglob("*")
                if p.is_file() and p.suffix in (".tex", ".bib", ".bbl", ".sty", ".cls")
            )
            if text_bytes > operation.limits.max_text_chars * 4:
                raise TexError("PARSE_BUDGET", "Text source bytes exceed parser input budget")
            parsed = parse_document(stage, main_tex, operation.limits.max_text_chars)
            manifest = [
                {"path": str(p.relative_to(stage)), "sha256": sha(p), "bytes": p.stat().st_size}
                for p in sorted(stage.rglob("*"))
                if p.is_file()
            ]
            doc = self.storage.save(stage, metadata, parsed, manifest)
        return {**self.summary(doc), "import_source": metadata, "usage": operation.usage()}

    @staticmethod
    def summary(doc):
        return {
            "document_id": doc["document_id"],
            "actual_version": doc.get("actual_version"),
            "arxiv_id": doc.get("arxiv_id"),
            "main_tex": doc["main_tex"],
            "main_candidates": doc["main_candidates"],
            "sections": len(doc["sections"]),
            "objects": len(doc["objects"]),
            "references": len(doc["references"]),
            "coverage": {
                "status": "partial" if doc["diagnostics"] else "parsed_subset",
                "diagnostic_count": len(doc["diagnostics"]),
                "resolved_object_references": sum(
                    e.get("status") == "resolved"
                    for e in doc["edges"]
                    if e["kind"] == "object_reference"
                ),
                "unresolved_object_references": sum(
                    e.get("status") != "resolved"
                    for e in doc["edges"]
                    if e["kind"] == "object_reference"
                ),
                "missing_citation_keys": sum(
                    r["status"] == "missing" for r in doc["references"].values()
                ),
                "unknown_macros": sum(d["code"] == "UNKNOWN_MACRO" for d in doc["diagnostics"]),
            },
            "numbering": doc["numbering"],
            "content_warning": WARNING,
        }

    def document(self, document_id):
        doc = self.storage.get(document_id)
        changed = self.storage.verify(document_id)
        if changed:
            raise TexError(
                "CACHE_CHANGED", "Source snapshot changed; reopen original source", files=changed
            )
        return doc

    def outline(self, document_id):
        doc = self.document(document_id)
        return {
            **self.summary(doc),
            "outline": doc["sections"],
            "body_range": [doc["body_start"], doc["body_end"]],
        }

    @staticmethod
    def section(doc, query=None, include_nested=True):
        if query is None:
            return doc["body_start"], doc["body_end"], None
        exact = [s for s in doc["sections"] if s["id"] == query]
        label_targets = doc["labels"].get(query, [])
        if not exact and len(label_targets) == 1 and label_targets[0]["target"] is None:
            position = label_targets[0]["position"]
            enclosing = [s for s in doc["sections"] if s["start"] <= position < s["end"]]
            if enclosing:
                exact = [max(enclosing, key=lambda s: s["level"])]
        candidates = exact or [
            s for s in doc["sections"] if query.casefold() in s["title"].casefold()
        ]
        if len(candidates) != 1:
            raise TexError(
                "SECTION_AMBIGUOUS" if candidates else "SECTION_NOT_FOUND",
                "Select exactly one section",
                candidates=[{"id": s["id"], "title": s["title"]} for s in candidates],
            )
        section = candidates[0]
        end = section["end"]
        if not include_nested:
            after = [s["start"] for s in doc["sections"] if section["start"] < s["start"] < end]
            if after:
                end = min(after)
        return section["start"], end, section

    @staticmethod
    def object(doc, ref):
        candidates = [o for o in doc["objects"] if o["object_id"] == ref or ref in o["labels"]]
        if len(candidates) != 1:
            raise TexError(
                "OBJECT_AMBIGUOUS" if candidates else "OBJECT_NOT_FOUND",
                "Object selector must match exactly one object",
                candidates=[o["object_id"] for o in candidates],
            )
        return candidates[0]

    def object_payload(self, doc, obj, asset_mode="paths", dpi=160):
        result = {
            k: v for k, v in obj.items() if k not in ("start", "end", "source_locations", "kind")
        }
        result["object_kind"] = obj["kind"]
        result["source_locations"] = obj["source_locations"][:4]
        result["source_location_count"] = len(obj["source_locations"])
        result["latex"] = doc["text"][obj["start"] : obj["end"]]
        if asset_mode == "images":
            result["assets"] = images.source_images(self.storage, doc, obj, dpi)
        elif asset_mode == "paths":
            root = self.storage.source_root(doc["document_id"])
            result["assets"] = [
                {**a, "absolute_paths": [str(contained(root, p)) for p in a["paths"]]}
                for a in obj["assets"]
            ]
        if obj["kind"] != "figure":
            result["availability"] = "source_available"
        elif asset_mode == "images":
            states = [a.get("image_status") for a in result["assets"]]
            result["availability"] = (
                "ready"
                if states and all(v == "ready" for v in states)
                else "partial"
                if "ready" in states
                else "no_ready_image"
            )
        else:
            result["availability"] = (
                "source_paths_available"
                if any(a.get("status") == "resolved" for a in result["assets"])
                else "no_resolved_source_image"
            )
        if obj["kind"] == "figure" and not obj["assets"]:
            result["limitations"] = [
                "Figure may be generated by TeX; use attached original PDF with an explicit crop or isolated rendering."
            ]
        return result

    def page(self, document_id, operation, records, max_chars=24000, cursor=None):
        if not 2000 <= max_chars <= 100000:
            raise TexError("INVALID_INPUT", "max_chars must be 2000..100000")
        binding = digest([document_id, operation])
        offset = 0
        if cursor:
            try:
                tag, offset = json.loads(base64.urlsafe_b64decode(cursor))
                if tag != binding or type(offset) is not int or offset < 0:
                    raise ValueError()
            except (ValueError, TypeError):
                raise TexError(
                    "INVALID_CURSOR", "Cursor does not match this document and operation"
                ) from None
        # Large object/entry payloads are split explicitly, never silently dropped.
        prepared = []
        width = max(200, min(5000, (max_chars - 1200) // 2))
        for index, record in enumerate(records):
            encoded = json.dumps(record, ensure_ascii=False)
            if len(encoded) <= max_chars - 1200:
                prepared.append(record)
            else:
                for part, start in enumerate(range(0, len(encoded), width)):
                    prepared.append(
                        {
                            "kind": "record_fragment",
                            "record_index": index,
                            "original_kind": record.get("kind"),
                            "part": part,
                            "encoding": "json",
                            "text": encoded[start : start + width],
                            "final": start + width >= len(encoded),
                        }
                    )
        if offset > len(prepared):
            raise TexError("INVALID_CURSOR", "Cursor offset out of range")
        result = {
            "document_id": document_id,
            "items": [],
            "next_cursor": None,
            "truncated": False,
            "content_warning": WARNING,
        }
        while offset < len(prepared):
            proposed = {
                **result,
                "items": result["items"] + [prepared[offset]],
                "next_cursor": "X" * 120,
                "truncated": True,
            }
            if len(json.dumps(proposed, ensure_ascii=False)) > max_chars:
                break
            result["items"].append(prepared[offset])
            offset += 1
        if offset < len(prepared):
            result["next_cursor"] = base64.urlsafe_b64encode(
                json.dumps([binding, offset]).encode()
            ).decode()
            result["truncated"] = True
        return result

    def read(
        self,
        document_id,
        section=None,
        view="expanded",
        include_nested=True,
        include_referenced=True,
        asset_mode="images",
        dpi=160,
        max_chars=24000,
        cursor=None,
    ):
        doc = self.document(document_id)
        start, end, selected = self.section(doc, section, include_nested)
        edges = [e for e in doc["edges"] if start <= e["start"] < end]
        owned = [o for o in doc["objects"] if start <= o["start"] < end]
        referenced_ids = (
            {e.get("target") for e in edges if e["kind"] == "object_reference"}
            if include_referenced
            else set()
        )
        objects = [o for o in doc["objects"] if o in owned or o["object_id"] in referenced_ids]
        records = [
            {
                "kind": "section",
                "id": selected["id"] if selected else "document",
                "title": selected["title"] if selected else "Document",
                "view": view,
                "source_range": [start, end],
                "diagnostic_count": len(doc["diagnostics"]),
                "coverage": "partial" if doc["diagnostics"] else "parsed_subset",
                "unresolved_references": [
                    e["key"]
                    for e in edges
                    if e["kind"] == "object_reference" and e["status"] != "resolved"
                ],
            }
        ]
        for obj in objects:
            payload = self.object_payload(doc, obj, asset_mode, dpi)
            records.append(
                {
                    "kind": "object",
                    "defined_in_section": obj["section_id"],
                    "relationship": "owned" if obj in owned else "directly_referenced",
                    "referenced_at": [
                        e["source_locations"][:1]
                        for e in edges
                        if e.get("target") == obj["object_id"]
                    ],
                    **payload,
                }
            )
        cited = {e["key"] for e in edges if e["kind"] == "citation"}
        if include_referenced:
            for e in doc["edges"]:
                if e["kind"] == "citation" and any(
                    o["start"] <= e["start"] < o["end"] for o in objects
                ):
                    cited.add(e["key"])
            records += [
                {"kind": "reference", **doc["references"][key]}
                for key in sorted(cited)
                if key in doc["references"]
            ]
        if view == "expanded":
            text = doc["text"][start:end]
            replacements = [o for o in owned if o["kind"] in ("figure", "table")]
            for obj in sorted(replacements, key=lambda o: o["start"], reverse=True):
                text = (
                    text[: obj["start"] - start]
                    + "[Object "
                    + obj["object_id"]
                    + "]"
                    + text[obj["end"] - start :]
                )
            width = max(200, min(4000, max_chars // 3))
            records += [
                {"kind": "body", "chunk": i // width, "text": text[i : i + width]}
                for i in range(0, len(text), width)
            ]
        elif view == "source":
            root = self.storage.source_root(document_id)
            origins = locations(doc["segments"], start, end)
            spans = []
            for origin in origins:
                if (
                    spans
                    and spans[-1]["file"] == origin["file"]
                    and origin["start"] <= spans[-1]["end"]
                ):
                    spans[-1]["end"] = max(spans[-1]["end"], origin["end"])
                else:
                    spans.append(dict(origin))
            for location in spans:
                raw = contained(root, location["file"]).read_text(
                    encoding="utf-8", errors="replace"
                )
                records.append(
                    {
                        "kind": "source_fragment",
                        "file": location["file"],
                        "start": location["start"],
                        "end": location["end"],
                        "text": raw[location["start"] : location["end"]],
                    }
                )
        else:
            raise TexError("INVALID_INPUT", "Unknown reading view")
        operation = [
            "read",
            section,
            view,
            include_nested,
            include_referenced,
            asset_mode,
            dpi,
            max_chars,
        ]
        return self.page(document_id, operation, records, max_chars, cursor)

    def objects(self, document_id, kind=None, section=None, max_chars=24000, cursor=None):
        doc = self.document(document_id)
        records = [
            {
                "kind": "object",
                "object_kind": obj["kind"],
                **{k: v for k, v in obj.items() if k not in ("source_locations", "kind")},
            }
            for obj in doc["objects"]
            if (kind is None or obj["kind"] == kind)
            and (section is None or obj["section_id"] == section)
        ]
        return self.page(
            document_id, ["objects", kind, section, max_chars], records, max_chars, cursor
        )

    def get_object(
        self, document_id, object_ref, asset_mode="images", dpi=160, max_chars=24000, cursor=None
    ):
        doc = self.document(document_id)
        obj = self.object(doc, object_ref)
        return self.page(
            document_id,
            ["object", object_ref, asset_mode, dpi, max_chars],
            [{"kind": "object", **self.object_payload(doc, obj, asset_mode, dpi)}],
            max_chars,
            cursor,
        )

    def references(self, document_id, keys=None, section=None, max_chars=24000, cursor=None):
        doc = self.document(document_id)
        wanted = set(keys) if keys is not None else None
        if section is not None:
            start, end, _ = self.section(doc, section)
            cited = {
                e["key"]
                for e in doc["edges"]
                if e["kind"] == "citation" and start <= e["start"] < end
            }
            wanted = cited if wanted is None else wanted & cited
        refs = doc["references"]
        records = [
            {"kind": "reference", **refs[key]}
            for key in refs
            if (wanted is not None and key in wanted)
            or (wanted is None and (refs[key]["cited_in_body"] or refs[key]["included_by_nocite"]))
        ]
        if keys:
            records += [
                {"kind": "reference", "key": key, "status": "not_in_document"}
                for key in keys
                if key not in refs
            ]
        return self.page(
            document_id, ["references", keys, section, max_chars], records, max_chars, cursor
        )

    def reference_lookups(self, document_id, keys=None, max_chars=24000, cursor=None):
        doc = self.document(document_id)
        result = []
        for key, entry in doc["references"].items():
            if keys is not None and key not in keys:
                continue
            if keys is None and not entry["cited_in_body"] and not entry["included_by_nocite"]:
                continue
            identifiers = entry["identifiers_from_source"]
            fields = entry["fields"]
            lookup = [{"identifier": value} for value in identifiers]
            if not lookup and fields.get("title"):
                value = {"title": fields["title"], "authors": entry["authors"]}
                if fields.get("year", "").isdigit():
                    value["year"] = int(fields["year"])
                lookup = [value]
            result.append(
                {
                    "kind": "reference_lookup",
                    "key": key,
                    "paper_search_inputs": lookup,
                    "status": "ready_for_lookup" if lookup else "insufficient_metadata",
                    "external_identity": "unverified",
                    "source": entry["source"],
                }
            )
        # No implicit API spending or invented ID binding.
        records = [
            {
                "kind": "handoff",
                "tool": "paper-search.resolve_papers",
                "limitations": [
                    "These are source claims, not externally verified identities. No API calls were made."
                ],
            }
        ] + result
        return self.page(
            document_id, ["reference_lookups", keys, max_chars], records, max_chars, cursor
        )

    def read_file(
        self, document_id, path, start_line=1, end_line=None, max_chars=24000, cursor=None
    ):
        doc = self.document(document_id)
        root = self.storage.source_root(document_id)
        if path not in {f["path"] for f in doc["manifest"]}:
            raise TexError("FILE_NOT_FOUND", "File is not in source manifest")
        if not path.endswith((".tex", ".bib", ".bbl", ".sty", ".cls", ".txt")):
            raise TexError("INVALID_INPUT", "Text source file required")
        raw = (
            contained(root, path)
            .read_text(encoding="utf-8", errors="replace")
            .splitlines(keepends=True)
        )
        end_line = len(raw) if end_line is None else end_line
        if start_line < 1 or end_line < start_line:
            raise TexError("INVALID_INPUT", "Invalid 1-based line range")
        records = [
            {"kind": "source_line", "file": path, "line": i + 1, "text": raw[i]}
            for i in range(start_line - 1, min(end_line, len(raw)))
        ]
        return self.page(
            document_id, ["file", path, start_line, end_line, max_chars], records, max_chars, cursor
        )

    def diagnostics(self, document_id, max_chars=24000, cursor=None):
        doc = self.document(document_id)
        return self.page(
            document_id,
            ["diagnostics", max_chars],
            [{"kind": "diagnostic", **d} for d in doc["diagnostics"]],
            max_chars,
            cursor,
        )

    def search(self, document_id, query, mode="literal", section=None, max_results=20):
        if not query or not 1 <= max_results <= 100:
            raise TexError("INVALID_INPUT", "Nonempty query and max_results 1..100 required")
        doc = self.document(document_id)
        start, end, _ = self.section(doc, section)
        text = doc["text"][start:end]
        pattern = query if mode == "regex" else regex.escape(query)
        if mode in ("and", "or"):
            terms = query.split()
            if mode == "and" and not all(term.casefold() in text.casefold() for term in terms):
                return {"document_id": document_id, "matches": [], "truncated": False}
            pattern = "|".join(regex.escape(t) for t in terms)
        try:
            compiled = regex.compile(pattern, regex.IGNORECASE)
            matches = []
            truncated = False
            for hit in compiled.finditer(text, timeout=0.15):
                if len(matches) >= max_results:
                    truncated = True
                    break
                position = start + hit.start()
                matches.append(
                    {
                        "start": position,
                        "end": start + hit.end(),
                        "snippet": text[max(0, hit.start() - 100) : hit.end() + 100],
                        "source_locations": locations(doc["segments"], position, start + hit.end())[
                            :4
                        ],
                    }
                )
        except TimeoutError:
            raise TexError("SEARCH_TIMEOUT", "Regex evaluation exceeded timeout") from None
        except regex.error:
            raise TexError("INVALID_REGEX", "Invalid regex pattern") from None
        return {
            "document_id": document_id,
            "matches": matches,
            "truncated": truncated,
            "content_warning": WARNING,
        }

    def compare(self, left, right, max_chars=24000, cursor=None):
        a, b = self.document(left), self.document(right)
        records = []
        for tag in ("sections", "objects", "references"):
            if tag == "references":
                x, y = a[tag], b[tag]
            elif tag == "sections":
                x = {s["id"]: a["text"][s["start"] : s["end"]] for s in a[tag]}
                y = {s["id"]: b["text"][s["start"] : s["end"]] for s in b[tag]}
            else:
                x = {
                    o["labels"][0] if o["labels"] else o["object_id"]: a["text"][
                        o["start"] : o["end"]
                    ]
                    for o in a[tag]
                }
                y = {
                    o["labels"][0] if o["labels"] else o["object_id"]: b["text"][
                        o["start"] : o["end"]
                    ]
                    for o in b[tag]
                }
            for key in sorted(set(x) | set(y)):
                if x.get(key) != y.get(key):
                    records.append(
                        {
                            "kind": "difference",
                            "category": tag,
                            "key": key,
                            "status": "added"
                            if key not in x
                            else "removed"
                            if key not in y
                            else "changed",
                            "left": x.get(key),
                            "right": y.get(key),
                        }
                    )
        return self.page(left, ["compare", right, max_chars], records, max_chars, cursor)
