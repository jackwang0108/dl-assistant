"""Isolated Docling process. Reads a fixed local PDF; external services stay disabled."""

import json
import os
import socket
import sys
import time
from pathlib import Path


class ModelNetworkDisabled(RuntimeError):
    pass


def deny_network(*args, **kwargs):
    raise ModelNetworkDisabled("Prepare models explicitly before offline parsing")


def convert(request):
    from importlib.metadata import version

    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    options = PdfPipelineOptions(
        do_ocr=request["ocr"],
        do_table_structure=True,
        do_formula_enrichment=request["formulas"],
        document_timeout=request["timeout"],
        enable_remote_services=False,
    )
    # The upstream default expands formula crops by 18%; on a two-column paper
    # that can include unrelated neighbouring text. Keep the detected region.
    if request["formulas"]:
        options.code_formula_options = options.code_formula_options.model_copy(
            update={"expansion_factor": 0.0, "extract_code": False}
        )
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )
    blocks, objects, sections, diagnostics, pages_done = [], [], [], [], []
    # One converter is reused across selected contiguous ranges to avoid reloading models.
    ranges = []
    for page in request["pages"]:
        if ranges and page == ranges[-1][1] + 1:
            ranges[-1][1] = page
        else:
            ranges.append([page, page])
    started = time.monotonic()
    for first, last in ranges:
        result = converter.convert(
            Path(request["path"]), page_range=(first, last), raises_on_error=False
        )
        status = result.status.value
        if status != "success":
            diagnostics.append(
                {
                    "code": "PARSE_PARTIAL" if "partial" in status else "PARSE_FAILED",
                    "pages": [first, last],
                    "status": status,
                    "errors": [str(e)[:500] for e in result.errors],
                }
            )
        document = result.document
        for item, level in document.iterate_items():
            provenance = getattr(item, "prov", [])
            if not provenance:
                continue
            for position in provenance:
                page = document.pages.get(position.page_no)
                if not page:
                    continue
                bbox = position.bbox.to_top_left_origin(page.size.height)
                label = item.label.value
                kind = (
                    "heading"
                    if label in ("section_header", "title")
                    else "table"
                    if label == "table"
                    else "figure"
                    if label == "picture"
                    else "equation"
                    if label == "formula"
                    else "text"
                )
                text = getattr(item, "text", "")
                block = {
                    "block_id": f"block:{len(blocks) + 1}",
                    "kind": kind,
                    "text": text,
                    "page": position.page_no,
                    "bbox": [bbox.l, bbox.t, bbox.r, bbox.b],
                    "section_ids": [],
                    "source_aliases": [],
                    "reference_targets": [],
                    "provenance": "docling_inferred_structure",
                    "source_ref": item.self_ref,
                }
                if kind == "heading":
                    section_id = f"section:{len(sections) + 1}"
                    sections.append(
                        {
                            "id": section_id,
                            "title": text,
                            "level": getattr(item, "level", level),
                            "page": position.page_no,
                            "bbox": block["bbox"],
                            "boundary_basis": "layout_model_inference",
                        }
                    )
                    block["section_id"] = section_id
                if kind in ("figure", "table", "equation"):
                    block["object_id"] = f"object:{len(objects) + 1}"
                    block["caption"] = (
                        item.caption_text(document) if hasattr(item, "caption_text") else ""
                    )
                    if kind == "table":
                        block["cells"] = [c.model_dump(mode="json") for c in item.data.table_cells]
                        block["rows"], block["columns"] = item.data.num_rows, item.data.num_cols
                    if kind == "equation":
                        block["formula_status"] = (
                            "model_recognition_unverified"
                            if request["formulas"]
                            else "not_recognized_use_original_region"
                        )
                    if kind == "equation" and not text:
                        diagnostics.append(
                            {
                                "code": "FORMULA_NOT_RECOGNIZED",
                                "object_id": block["object_id"],
                                "page": position.page_no,
                                "message": "Formula region detected but text not recovered; inspect original crop or enable formula recognition.",
                            }
                        )
                    elif kind == "equation" and request["formulas"]:
                        diagnostics.append(
                            {
                                "code": "FORMULA_REQUIRES_VISUAL_CHECK",
                                "object_id": block["object_id"],
                                "page": position.page_no,
                                "message": "Recognized LaTeX is model output, not the author's original source; compare with the original region.",
                            }
                        )
                    objects.append(block)
                blocks.append(block)
        for number in document.pages:
            if first <= number <= last:
                pages_done.append(number)
    return {
        "blocks": blocks,
        "objects": objects,
        "sections": sections,
        "references": [],
        "diagnostics": diagnostics,
        "pages_processed": sorted(set(pages_done)),
        "reading_order": "docling_inferred_unverified",
        "engine_version": version("docling"),
        "seconds": round(time.monotonic() - started, 3),
        "coverage": "partial" if diagnostics else "inferred_structure_not_independently_verified",
    }


def main():
    request = json.loads(Path(sys.argv[1]).read_text())
    target = Path(sys.argv[2])
    # Model files may be downloaded only when explicitly requested.
    if not request.get("allow_model_download", False):
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        socket.socket.connect = deny_network
        socket.socket.connect_ex = deny_network
        socket.create_connection = deny_network
    else:
        proxy = os.getenv("PDF_MCP_PROXY_URL")
        if proxy:
            os.environ["HTTP_PROXY"] = proxy
            os.environ["HTTPS_PROXY"] = proxy
            os.environ["ALL_PROXY"] = proxy
    os.environ["HF_HOME"] = request["model_cache"]
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    try:
        result = convert(request)
    except Exception as error:  # noqa: BLE001 - worker converts model failures into structured results
        code = "PARSER_FAILED"
        if isinstance(error, ImportError):
            code = "PARSER_UNAVAILABLE"
        elif isinstance(error, (ModelNetworkDisabled, FileNotFoundError)) or any(
            word in str(error).lower()
            for word in (
                "offline",
                "local cache",
                "not found in the cached",
                "couldn't connect",
                "not available locally",
            )
        ):
            code = "MODEL_NOT_READY"
        result = {
            "error": {
                "code": code,
                "message": "Docling conversion failed; inspect parser installation and model readiness",
                "reason": type(error).__name__,
            }
        }
    target.write_text(json.dumps(result))


if __name__ == "__main__":
    main()
