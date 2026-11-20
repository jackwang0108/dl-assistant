"""Fixed-source reading, bounded outputs and explicitly requested structure recognition."""

import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import regex

from . import assets, native
from .acquire import Downloader
from .models import Limits, PdfError, checksum, page_numbers
from .paging import bounded
from .store import Store
from .structured import parse_structured


class Service:
    def __init__(self, cache_dir=None, downloader=None):
        self.store = Store(cache_dir)
        self.downloader = downloader or Downloader()

    def capabilities(self):
        return {
            "api_version": 2,
            "formats": ["pdf", "html", "xml"],
            "default_pdf_mode": "native_text_and_original_page; no model download",
            "structure_engine": "docling",
            "structure_python": os.getenv("PDF_MCP_STRUCTURE_PYTHON", sys.executable),
            "model_download_default": False,
            "external_api_calls": False,
            "download_transport": "explicit_trusted_proxy"
            if self.downloader.proxy_url
            else "public_dns_pinned",
            "coordinate_system": "top_left_pdf_points_xyxy",
            "limitations": [
                "Native PDF text order is unverified; use structure parsing or original pages.",
                "OCR, inferred formulas, tables and section boundaries require verification.",
                "HTML/XML may represent a different version; identifiers do not prove equivalence to another PDF.",
            ],
        }

    def open(self, source, source_format="auto", limits=None, identity_basis=None):
        limits = limits or Limits()
        remote = source.startswith(("http://", "https://"))
        if remote:
            data, origin = self.downloader.fetch(source, limits)
        else:
            path = Path(source).expanduser().resolve()
            if not path.is_file():
                raise PdfError("SOURCE_NOT_FOUND", "Source file does not exist")
            if path.stat().st_size > limits.max_bytes:
                raise PdfError("SOURCE_SIZE", "Source exceeds byte budget")
            with path.open("rb") as stream:
                data = stream.read(limits.max_bytes + 1)
            origin = {"local_path": str(path)}
        if len(data) > limits.max_bytes:
            raise PdfError("SOURCE_SIZE", "Source exceeds byte budget")
        format_ = source_format
        if format_ == "auto":
            if data[:1024].lstrip().startswith(b"%PDF"):
                format_ = "pdf"
            elif re.search(rb"<(?:[\w-]+:)?article(?:\s|>)", data[:100000]) and (
                data.lstrip().startswith(b"<?xml") or source.lower().endswith((".xml", ".nxml"))
            ):
                format_ = "xml"
            elif re.search(
                rb"<(?:!doctype\s+html|html|article)(?:\s|>)", data[:100000], re.IGNORECASE
            ):
                format_ = "html"
            else:
                raise PdfError(
                    "INVALID_FORMAT", "Expected a readable PDF, article HTML or JATS XML"
                )
        payload = {
            "format": format_,
            "origin": origin,
            "identity_status": "unverified",
            "identity_basis": identity_basis,
            "page_count": None,
            "diagnostics": [],
        }
        if format_ == "pdf":
            with tempfile.NamedTemporaryFile(suffix=".pdf", dir=self.store.root) as temporary:
                temporary.write(data)
                temporary.flush()
                with native.open_pdf(temporary.name) as pdf:
                    if len(pdf) > limits.max_pages:
                        raise PdfError(
                            "PAGE_LIMIT", "Document exceeds page limit", page_count=len(pdf)
                        )
                    payload.update(
                        page_count=len(pdf),
                        metadata=pdf.metadata or {},
                        sections=[
                            {
                                "id": f"toc:{i + 1}",
                                "level": e[0],
                                "title": e[1],
                                "page": e[2],
                                "boundary_basis": "bookmark_page_range_not_exact_section",
                            }
                            for i, e in enumerate(pdf.get_toc())
                        ],
                    )
        elif format_ in ("html", "xml"):
            # Reject ordinary login/error pages instead of claiming an empty article was parsed.
            structured = parse_structured(data, format_, origin.get("final_url"))
            if format_ == "html" and not re.search(
                rb"<article(?:\s|>)|ltx_document", data, re.IGNORECASE
            ):
                raise PdfError("NO_ARTICLE", "HTML has no article container")
            payload.update(structured)
        else:
            raise PdfError("INVALID_FORMAT", "Supported formats: auto, pdf, html, xml")
        doc = self.store.save(data, payload)
        return {
            "document_id": doc["document_id"],
            "format": doc["format"],
            "sha256": doc["sha256"],
            "page_count": doc["page_count"],
            "title": doc.get("metadata", {}).get("title", "")[:1000],
            "identity_status": "unverified",
            "sections": len(doc["sections"]),
            "diagnostic_count": len(doc["diagnostics"]),
            "content_warning": "Document title and metadata are untrusted content.",
        }

    def info(self, document_id):
        doc = self.store.get(document_id)
        return {
            k: doc.get(k)
            for k in (
                "document_id",
                "format",
                "sha256",
                "origin",
                "identity_status",
                "identity_basis",
                "metadata",
                "page_count",
                "sections",
                "diagnostics",
            )
        } | {
            "content_bytes": Path(doc["path"]).stat().st_size,
            "reading_mode": "native_text_unverified_order"
            if doc["format"] == "pdf"
            else "source_structure",
            "content_warning": "Document content, metadata and links are untrusted data.",
        }

    def data(self, doc, parse_id=None, pages=None, bbox=None):
        if parse_id:
            data = self.store.get_parse(doc["document_id"], parse_id)
            if pages is not None and not set(pages).issubset(data["pages_processed"]):
                raise PdfError(
                    "PARSE_SCOPE_MISMATCH",
                    "Requested pages were not processed by this parse_id",
                    pages_processed=data["pages_processed"],
                )
            data["blocks"] = [b for b in data["blocks"] if pages is None or b["page"] in pages]
            return data
        if doc["format"] != "pdf":
            if pages is not None or bbox is not None:
                raise PdfError(
                    "NO_PAGE_MAPPING", "Structured source has no certified PDF page mapping"
                )
            return doc
        pages = pages if pages is not None else page_numbers(None, doc["page_count"])
        records = native.page_records(doc, pages, bbox)
        failures = [p["diagnostic"] for p in records if p.get("diagnostic")]
        return {
            "blocks": [b for p in records for b in p["blocks"]],
            "sections": doc["sections"],
            "objects": [],
            "references": [],
            "diagnostics": failures
            + [
                {
                    "code": "READING_ORDER_UNVERIFIED",
                    "message": "PDF object order may differ from reading order; parse structure or inspect original page.",
                }
            ],
            "coverage": "partial" if failures else "native_text_layer_only",
        }

    def page_info(self, document_id, pages=None, max_chars=24000, cursor=None):
        doc = self.pdf(document_id)
        numbers = page_numbers(pages, doc["page_count"], maximum=50)
        records = native.page_records(doc, numbers)
        for record in records:
            record.pop("blocks")
            record.pop("spans")
        return bounded(document_id, records, ["page_info", pages], max_chars, cursor)

    def pdf(self, document_id):
        doc = self.store.get(document_id)
        if doc["format"] != "pdf":
            raise PdfError("PDF_REQUIRED", "This operation requires a PDF snapshot")
        return doc

    def outline(self, document_id, parse_id=None, max_chars=24000, cursor=None):
        doc = self.store.get(document_id)
        data = self.store.get_parse(document_id, parse_id) if parse_id else doc
        return bounded(
            document_id,
            [{"kind": "section", **s} for s in data["sections"]],
            ["outline", parse_id],
            max_chars,
            cursor,
        )

    @staticmethod
    def select_section(data, section):
        sections = data["sections"]
        exact = [s for s in sections if s["id"] == section or s["title"] == section]
        candidates = exact or [s for s in sections if section.casefold() in s["title"].casefold()]
        if len(candidates) != 1:
            raise PdfError(
                "SECTION_AMBIGUOUS" if candidates else "SECTION_NOT_FOUND",
                "Select a unique section ID from the outline",
                candidates=candidates[:20],
            )
        return candidates[0]

    def read(
        self,
        document_id,
        pages=None,
        section=None,
        parse_id=None,
        bbox=None,
        include_referenced=True,
        max_chars=24000,
        cursor=None,
    ):
        doc = self.store.get(document_id)
        numbers = (
            page_numbers(pages, doc["page_count"])
            if doc["format"] == "pdf" and pages is not None
            else None
        )
        if bbox is not None and parse_id:
            raise PdfError("INVALID_INPUT", "Region reads use native PDF text; omit parse_id")
        if bbox is not None and numbers is None:
            raise PdfError("INVALID_INPUT", "Select explicit pages for region reading")
        if doc["format"] == "pdf" and not parse_id and section:
            selected = self.select_section(doc, section)
            start = selected["page"]
            if start < 1:
                raise PdfError("NO_PAGE_MAPPING", "Bookmark has no valid page")
            index = doc["sections"].index(selected)
            following = next(
                (s for s in doc["sections"][index + 1 :] if s["level"] <= selected["level"]), None
            )
            # The next heading's page can contain the end of this section. Include it.
            end = following["page"] if following else doc["page_count"]
            numbers = page_numbers(f"{start}-{max(start, end)}", doc["page_count"])
            data = self.data(doc, pages=numbers, bbox=bbox)
            blocks = data["blocks"]
            section_record = {
                "kind": "selection",
                "section": selected,
                "coverage": "candidate_pages_including_shared_boundary_pages",
            }
        else:
            data = self.data(doc, parse_id, numbers, bbox)
            blocks = data["blocks"]
            section_record = None
            if section:
                selected = self.select_section(data, section)
                if doc["format"] in ("html", "xml"):
                    blocks = [b for b in blocks if selected["id"] in b["section_ids"]]
                else:
                    start = next(
                        (i for i, b in enumerate(blocks) if b.get("section_id") == selected["id"]),
                        None,
                    )
                    if start is None:
                        raise PdfError(
                            "SECTION_OUTSIDE_SELECTION", "Section is outside parsed pages"
                        )
                    higher = {
                        s["id"]
                        for s in data["sections"]
                        if s.get("level", 1) <= selected.get("level", 1)
                    }
                    end = next(
                        (
                            i
                            for i in range(start + 1, len(blocks))
                            if blocks[i].get("section_id") in higher
                        ),
                        len(blocks),
                    )
                    blocks = blocks[start:end]
                section_record = {
                    "kind": "selection",
                    "section": selected,
                    "coverage": data.get("coverage"),
                }
        if bbox is not None and numbers is None:
            raise PdfError("INVALID_INPUT", "Select explicit pages for region reading")
        attachments = []
        if include_referenced and section and doc["format"] != "pdf":
            aliases = {alias for block in blocks for alias in block.get("source_aliases", [])}
            targets = {
                target for block in blocks for target in block.get("reference_targets", [])
            } - aliases
            for obj in data["objects"] + data["references"]:
                if targets.intersection(obj.get("source_aliases", [])):
                    attachments.append({**obj, "relationship": "directly_referenced"})
        records = (
            ([section_record] if section_record else [])
            + [
                {
                    "kind": "coverage",
                    "status": data.get("coverage"),
                    "diagnostics": data.get("diagnostics", []),
                    "direct_reference_attachment": "source_links"
                    if doc["format"] != "pdf"
                    else "not_guaranteed_for_pdf",
                }
            ]
            + attachments
            + blocks
        )
        return bounded(
            document_id,
            records,
            ["read", pages, section, parse_id, bbox, include_referenced],
            max_chars,
            cursor,
        )

    def search(
        self,
        document_id,
        query,
        mode="literal",
        pages=None,
        section=None,
        parse_id=None,
        max_chars=24000,
        cursor=None,
    ):
        if not query or len(query) > 4000 or mode not in ("literal", "regex", "and", "or"):
            raise PdfError("INVALID_QUERY", "Provide a nonempty bounded query and supported mode")
        doc = self.store.get(document_id)
        numbers = (
            page_numbers(pages, doc["page_count"])
            if doc["format"] == "pdf" and (pages is not None or not parse_id)
            else None
        )
        data = (
            self.data(doc, parse_id, numbers)
            if doc["format"] == "pdf"
            else self.data(doc, parse_id)
        )
        blocks = data["blocks"]
        if section:
            selected = self.select_section(data, section)
            if doc["format"] == "pdf":
                if not parse_id:
                    index = data["sections"].index(selected)
                    end = next(
                        (
                            s["page"]
                            for s in data["sections"][index + 1 :]
                            if s["level"] <= selected["level"]
                        ),
                        doc["page_count"],
                    )
                    blocks = [b for b in blocks if selected["page"] <= b["page"] <= end]
                else:
                    start = next(
                        (i for i, b in enumerate(blocks) if b.get("section_id") == selected["id"]),
                        None,
                    )
                    if start is None:
                        raise PdfError(
                            "SECTION_OUTSIDE_SELECTION", "Section is outside selected parsed pages"
                        )
                    higher = {
                        s["id"]
                        for s in data["sections"]
                        if s.get("level", 1) <= selected.get("level", 1)
                    }
                    end = next(
                        (
                            i
                            for i in range(start + 1, len(blocks))
                            if blocks[i].get("section_id") in higher
                        ),
                        len(blocks),
                    )
                    blocks = blocks[start:end]
            else:
                blocks = [b for b in blocks if selected["id"] in b.get("section_ids", [])]
        terms = re.split(r"[\s,]+", query.strip()) if mode in ("and", "or") else [query]
        records, locations, count = [], set(), 0
        search_started = time.monotonic()
        try:
            pattern = regex.compile(
                query if mode == "regex" else "|".join(regex.escape(t) for t in terms), regex.I
            )
            grouped = {}
            for b in blocks:
                grouped.setdefault(
                    b["page"] if b["page"] is not None else tuple(b.get("section_ids", [])), []
                ).append(b)
            for group in grouped.values():
                if mode == "and" and not all(
                    any(t.casefold() in b["text"].casefold() for b in group) for t in terms
                ):
                    continue
                for block in group:
                    if time.monotonic() - search_started > 5:
                        raise PdfError(
                            "SEARCH_TIMEOUT", "Search time budget exceeded; narrow the page range"
                        )
                    for match in pattern.finditer(block["text"], timeout=0.1):
                        count += 1
                        locations.add(block["page"])
                        records.append(
                            {
                                "kind": "match",
                                "block_id": block["block_id"],
                                "page": block["page"],
                                "bbox": block["bbox"],
                                "position": match.start(),
                                "excerpt": block["text"][
                                    max(0, match.start() - 100) : match.end() + 100
                                ],
                                "provenance": block["provenance"],
                            }
                        )
                        if count > 50000:
                            raise PdfError(
                                "SEARCH_LIMIT", "Too many matches; narrow the query or page range"
                            )
        except (regex.error, TimeoutError):
            raise PdfError("QUERY_FAILED", "Invalid or timed-out regular expression") from None
        records.insert(
            0,
            {
                "kind": "search_summary",
                "total_matches": count,
                "pages_with_matches": sorted(p for p in locations if p is not None),
                "searched_pages": len({b["page"] for b in blocks if b["page"] is not None}),
                "coverage": data.get("coverage"),
                "zero_matches_does_not_prove_absence": True,
            },
        )
        return bounded(
            document_id,
            records,
            ["search", query, mode, pages, section, parse_id],
            max_chars,
            cursor,
        )

    def objects(
        self, document_id, kind=None, pages=None, parse_id=None, max_chars=24000, cursor=None
    ):
        doc = self.store.get(document_id)
        if doc["format"] == "pdf" and not parse_id:
            if kind in ("figure", "equation"):
                raise PdfError(
                    "STRUCTURE_PARSE_REQUIRED",
                    "Native extraction detects bitmaps/tables; use pdf_parse for logical figures and equations, or inspect the original page",
                )
            numbers = page_numbers(pages, doc["page_count"], maximum=50)
            objects, diagnostics = native.native_objects(doc, numbers, kind)
        else:
            data = self.store.get_parse(document_id, parse_id) if parse_id else doc
            objects, diagnostics = data["objects"], data.get("diagnostics", [])
            if pages is not None:
                if doc["format"] != "pdf":
                    raise PdfError(
                        "NO_PAGE_MAPPING", "Structured source has no certified PDF page mapping"
                    )
                numbers = page_numbers(pages, doc["page_count"])
                if not set(numbers).issubset(data["pages_processed"]):
                    raise PdfError(
                        "PARSE_SCOPE_MISMATCH", "Requested objects are outside this parse_id"
                    )
                objects = [o for o in objects if o["page"] in numbers]
        records = [
            {
                "kind": "operation_status",
                "status": "partial"
                if diagnostics
                else "completed_detection_not_proof_of_exhaustiveness",
                "diagnostics": diagnostics,
            }
        ]
        records += [o for o in objects if kind is None or o["kind"] == kind]
        return bounded(document_id, records, ["objects", kind, pages, parse_id], max_chars, cursor)

    def get_object(
        self,
        document_id,
        object_id,
        parse_id=None,
        view="metadata",
        dpi=160,
        max_chars=24000,
        cursor=None,
    ):
        doc = self.store.get(document_id)
        if doc["format"] == "pdf" and not parse_id:
            match = re.match(r"(?:image|table):(\d+):", object_id)
            if not match:
                raise PdfError(
                    "OBJECT_NOT_FOUND", "List objects first or supply the corresponding parse_id"
                )
            numbers = page_numbers(match[1], doc["page_count"])
            objects, _ = native.native_objects(
                doc, numbers, "image" if object_id.startswith("image:") else "table"
            )
        else:
            objects = (self.store.get_parse(document_id, parse_id) if parse_id else doc)["objects"]
        matches = [
            o
            for o in objects
            if o["object_id"] == object_id or object_id in o.get("source_aliases", [])
        ]
        if len(matches) != 1:
            raise PdfError(
                "OBJECT_NOT_FOUND" if not matches else "OBJECT_AMBIGUOUS",
                "Select a unique object ID",
            )
        result = dict(matches[0])
        if not 36 <= dpi <= 400:
            raise PdfError("INVALID_DPI", "DPI must be 36–400")
        if view == "image":
            if doc["format"] != "pdf":
                result["assets"] = assets.images(self, doc, result, dpi)
                result["image_status"] = (
                    "ready"
                    if result["assets"]
                    and all(a.get("image_status") == "ready" for a in result["assets"])
                    else "partial_or_unavailable"
                )
            elif result["kind"] == "image":
                result["image"] = native.extract_bitmap(self.store, doc, result)
            else:
                result["image"] = native.render(
                    self.store, doc, result["page"], result["bbox"], dpi
                )
        return bounded(
            document_id, [result], ["object", object_id, parse_id, view, dpi], max_chars, cursor
        )

    def render(self, document_id, pages, bbox=None, dpi=150, max_chars=24000, cursor=None):
        doc = self.pdf(document_id)
        numbers = page_numbers(pages, doc["page_count"], maximum=10)
        return bounded(
            document_id,
            [native.render(self.store, doc, n, bbox, dpi) for n in numbers],
            ["render", pages, bbox, dpi],
            max_chars,
            cursor,
        )

    def diagnostics(self, document_id, parse_id=None, max_chars=24000, cursor=None):
        doc = self.store.get(document_id)
        data = self.store.get_parse(document_id, parse_id) if parse_id else doc
        diagnostics = data.get("diagnostics", [])
        if doc["format"] == "pdf" and not parse_id:
            diagnostics = diagnostics + [
                {
                    "code": "NO_STRUCTURE_PARSE",
                    "message": "Raw text, bookmarks and bitmap extraction do not recover complete article structure.",
                }
            ]
        return bounded(document_id, diagnostics, ["diagnostics", parse_id], max_chars, cursor)

    def references(self, document_id, parse_id=None, max_chars=24000, cursor=None):
        doc = self.store.get(document_id)
        data = self.store.get_parse(document_id, parse_id) if parse_id else doc
        records = [
            {
                "kind": "reference_status",
                "status": "source_bibliography"
                if doc["format"] != "pdf"
                else "not_structurally_extracted_use_source_or_locate_references_pages",
                "external_identity": "unverified",
            }
        ] + data.get("references", [])
        return bounded(document_id, records, ["references", parse_id], max_chars, cursor)

    def links(self, document_id, pages=None, max_chars=24000, cursor=None):
        doc = self.pdf(document_id)
        records = []
        with native.open_pdf(doc["path"]) as pdf:
            for number in page_numbers(pages, doc["page_count"]):
                for link in pdf[number - 1].get_links():
                    records.append(
                        {
                            "page": number,
                            "bbox": list(link["from"]),
                            "uri": link.get("uri"),
                            "target_page": link["page"] + 1 if link.get("page", -1) >= 0 else None,
                            "kind": "link",
                            "trust": "unverified_external_content",
                        }
                    )
        return bounded(document_id, records, ["links", pages], max_chars, cursor)

    def source_candidates(self, document_id, arxiv_id=None, pmcid=None):
        self.store.get(document_id)
        candidates = []
        if arxiv_id:
            if not re.fullmatch(
                r"(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})v[1-9]\d*", arxiv_id
            ):
                raise PdfError(
                    "VERSION_REQUIRED", "Supply the exact arXiv revision, e.g. 2404.14219v1"
                )
            candidates.append(
                {
                    "source": "https://arxiv.org/html/" + arxiv_id,
                    "format": "html",
                    "status": "candidate_not_fetched",
                    "version": arxiv_id,
                    "identity_status": "not_matched_to_pdf",
                }
            )
        if pmcid:
            if not re.fullmatch(r"PMC\d+", pmcid):
                raise PdfError("INVALID_IDENTIFIER", "Use a PMC identifier such as PMC123456")
            candidates.append(
                {
                    "source": f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/",
                    "format": "html",
                    "status": "candidate_not_fetched",
                    "identity_status": "not_matched_to_pdf",
                    "jats_availability_manifest": f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={pmcid}",
                    "message": "The OA manifest locates permitted downloads; it is not itself article JATS.",
                }
            )
        return {
            "document_id": document_id,
            "candidates": candidates,
            "policy": "Check identity, exact revision and missing content before using another representation; do not merge it into this PDF snapshot.",
            "official_sources": [
                "https://info.arxiv.org/about/accessible_HTML.html",
                "https://pmc.ncbi.nlm.nih.gov/tools/openftlist/",
            ],
        }

    def parse(
        self, document_id, pages, ocr=False, formulas=False, allow_model_download=False, timeout=120
    ):
        doc = self.pdf(document_id)
        numbers = page_numbers(pages, doc["page_count"], maximum=20)
        if not 5 <= timeout <= 600:
            raise PdfError("INVALID_TIMEOUT", "Parser timeout must be 5–600 seconds")
        with native.open_pdf(doc["path"]) as pdf:
            for number in numbers:
                # The formula stage can rasterize at 2x; reject oversized input
                # before starting model code or allocating its page images.
                if pdf[number - 1].rect.width * pdf[number - 1].rect.height * 4 > 30_000_000:
                    raise PdfError(
                        "PIXEL_LIMIT",
                        "Selected page is too large for structure recognition; inspect a bounded original-page region",
                    )
        executable = os.getenv("PDF_MCP_STRUCTURE_PYTHON", sys.executable)
        try:
            probe = subprocess.run(
                [
                    executable,
                    "-c",
                    "from importlib.metadata import version; print(version('docling'))",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise PdfError(
                "PARSER_UNAVAILABLE", "Could not query configured parser Python"
            ) from None
        if probe.returncode:
            raise PdfError(
                "PARSER_UNAVAILABLE",
                "Install pdf-mcp[structure] or configure PDF_MCP_STRUCTURE_PYTHON",
            )
        model_cache = os.getenv(
            "PDF_MCP_MODEL_CACHE", str(self.store.root / "models" / "huggingface")
        )
        profile = {
            "engine": "docling",
            "engine_version": probe.stdout.strip(),
            "model_cache": model_cache,
            "model_signature": self.model_signature(model_cache),
            "python": executable,
            "pages": numbers,
            "ocr": ocr,
            "formulas": formulas,
            "worker_sha256": checksum(Path(__file__).with_name("worker.py")),
        }
        cached = self.store.find_parse(document_id, profile)
        if cached:
            return {
                "document_id": document_id,
                "parse_id": cached["parse_id"],
                "cache_state": "hit",
                "coverage": cached["coverage"],
                "pages_processed": cached["pages_processed"],
                "engine_version": cached["engine_version"],
                "diagnostics": cached["diagnostics"],
            }
        with tempfile.TemporaryDirectory(dir=self.store.root / "jobs-v2") as temporary:
            folder = Path(temporary)
            request = {
                "path": doc["path"],
                "pages": numbers,
                "ocr": ocr,
                "formulas": formulas,
                "allow_model_download": allow_model_download,
                "timeout": timeout,
                "model_cache": model_cache,
            }
            (folder / "request.json").write_text(json.dumps(request))
            command = [
                executable,
                str(Path(__file__).with_name("worker.py")),
                str(folder / "request.json"),
                str(folder / "result.json"),
            ]
            started = time.monotonic()
            with (folder / "log").open("wb") as log:
                try:
                    process = subprocess.Popen(
                        command, stdout=log, stderr=log, start_new_session=True
                    )
                except OSError:
                    raise PdfError(
                        "PARSER_UNAVAILABLE",
                        "Install the structure extra or configure PDF_MCP_STRUCTURE_PYTHON",
                    ) from None
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    if os.name == "posix":
                        os.killpg(process.pid, signal.SIGKILL)
                    else:
                        process.kill()
                    process.wait()
                    raise PdfError(
                        "PARSER_TIMEOUT",
                        "Structure recognition exceeded its wall-time budget; original PDF remains readable",
                    ) from None
            result_path = folder / "result.json"
            if process.returncode or not result_path.is_file():
                raise PdfError(
                    "PARSER_FAILED",
                    "Structure worker exited without a valid result",
                    exit_code=process.returncode,
                )
            if result_path.stat().st_size > 50_000_000:
                raise PdfError("PARSER_SIZE", "Parsed result exceeds size limit")
            try:
                result = json.loads(result_path.read_text())
            except (ValueError, UnicodeError):
                raise PdfError(
                    "PARSER_INVALID_RESULT", "Structure worker returned invalid JSON"
                ) from None
            if not isinstance(result, dict):
                raise PdfError(
                    "PARSER_INVALID_RESULT", "Structure worker returned a non-object result"
                )
            if "error" in result:
                error = result["error"]
                raise PdfError(error["code"], error["message"], reason=error.get("reason"))
            if any(
                not isinstance(result.get(key), list)
                for key in (
                    "blocks",
                    "objects",
                    "sections",
                    "references",
                    "diagnostics",
                    "pages_processed",
                )
            ) or not all(key in result for key in ("coverage", "engine_version")):
                raise PdfError(
                    "PARSER_INVALID_RESULT", "Structure worker result is missing required fields"
                )
            if any(page not in numbers for page in result["pages_processed"]) or any(
                block.get("page") not in numbers for block in result["blocks"]
            ):
                raise PdfError(
                    "PARSER_INVALID_RESULT",
                    "Structure worker returned content outside selected pages",
                )
            missing = sorted(set(numbers) - set(result["pages_processed"]))
            if missing:
                result["diagnostics"].append({"code": "PAGES_NOT_PROCESSED", "pages": missing})
                result["coverage"] = "partial"
        profile["model_signature"] = self.model_signature(model_cache)
        parsed = self.store.save_parse(document_id, profile, result)
        return {
            "document_id": document_id,
            "parse_id": parsed["parse_id"],
            "cache_state": "miss",
            "pages_processed": result["pages_processed"],
            "coverage": result["coverage"],
            "engine_version": result["engine_version"],
            "total_seconds": round(time.monotonic() - started, 3),
            "diagnostics": result["diagnostics"],
        }

    @staticmethod
    def model_signature(cache):
        """Track model revisions/configuration and weight file metadata without rereading GBs on each call."""
        root = Path(cache)
        records = []
        for repository in sorted((root / "hub").glob("*docling*")):
            for path in sorted(repository.rglob("*")):
                if not path.is_file() or path.name.endswith((".lock", ".incomplete")):
                    continue
                stat = path.stat()
                config_sha = (
                    checksum(path)
                    if (path.suffix == ".json" or "refs" in path.parts) and stat.st_size < 5_000_000
                    else None
                )
                records.append(
                    [str(path.relative_to(root)), stat.st_size, stat.st_mtime_ns, config_sha]
                )
        from .models import digest

        return digest(records)
