"""PDF page geometry, raw text and verifiable raster output; no claimed semantic recovery."""

import math

import pymupdf

from .models import PdfError, checksum, digest

PDF_EXCEPTIONS = (OSError, ValueError, RuntimeError, pymupdf.mupdf.FzErrorBase)


def open_pdf(path):
    try:
        document = pymupdf.open(path)
        if not document.is_pdf or not document.page_count or document.needs_pass:
            document.close()
            raise PdfError("INVALID_PDF", "A readable, unencrypted PDF is required")
        return document
    except PDF_EXCEPTIONS:
        raise PdfError("INVALID_PDF", "File could not be opened as PDF") from None


def rectangle(page, bbox):
    if bbox is None:
        return page.rect
    if (
        len(bbox) != 4
        or any(not math.isfinite(v) for v in bbox)
        or bbox[2] <= bbox[0]
        or bbox[3] <= bbox[1]
    ):
        raise PdfError("INVALID_BBOX", "Use finite [x0,y0,x1,y1] with positive area")
    rect = pymupdf.Rect(bbox) & page.rect
    if rect.is_empty:
        raise PdfError("INVALID_BBOX", "Region is outside the page")
    return rect


def page_records(doc, pages, bbox=None):
    result = []
    with open_pdf(doc["path"]) as pdf:
        for number in pages:
            page = pdf[number - 1]
            rect = rectangle(page, bbox)
            try:
                data = page.get_text(
                    "dict",
                    clip=rect,
                    sort=False,
                    flags=pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES,
                )
            except PDF_EXCEPTIONS as error:
                result.append(
                    {
                        "page": number,
                        "text_status": "extraction_failed",
                        "blocks": [],
                        "spans": [],
                        "diagnostic": {
                            "code": "TEXT_EXTRACTION_FAILED",
                            "page": number,
                            "reason": type(error).__name__,
                        },
                    }
                )
                continue
            texts, fonts = [], []
            for block in data["blocks"]:
                if block["type"] != 0:
                    continue
                text = "\n".join(
                    "".join(s["text"] for s in line["spans"]) for line in block["lines"]
                )
                if not text.strip():
                    continue
                ident = f"page:{number}:block:{block['number']}"
                texts.append(
                    {
                        "block_id": ident,
                        "kind": "text",
                        "page": number,
                        "bbox": list(block["bbox"]),
                        "text": text,
                        "provenance": "pdf_text_layer",
                        "section_ids": [],
                        "reference_targets": [],
                    }
                )
                for line in block["lines"]:
                    for span in line["spans"]:
                        fonts.append(
                            {
                                "size": span["size"],
                                "font": span["font"],
                                "bbox": span["bbox"],
                                "text": span["text"],
                            }
                        )
            joined = "\n".join(t["text"] for t in texts)
            unusual = sum(c == "\ufffd" or (ord(c) < 32 and c not in "\n\t\r") for c in joined)
            image_count = len(page.get_images())
            quality = (
                "no_text_layer"
                if not joined.strip()
                else "suspicious_text"
                if unusual / max(len(joined), 1) > 0.02
                else "text_layer_available"
            )
            result.append(
                {
                    "page": number,
                    "page_label": page.get_label(),
                    "width": page.rect.width,
                    "height": page.rect.height,
                    "rotation": page.rotation,
                    "bbox": list(rect),
                    "text_status": quality,
                    "chars": len(joined),
                    "embedded_images": image_count,
                    "reading_order": "pdf_object_order_unverified",
                    "blocks": texts,
                    "spans": fonts,
                }
            )
    return result


def native_objects(doc, pages, kind=None):
    objects, diagnostics = [], []
    with open_pdf(doc["path"]) as pdf:
        for number in pages:
            page = pdf[number - 1]
            if kind in (None, "image"):
                for index, image in enumerate(page.get_images(full=True)):
                    xref = image[0]
                    try:
                        regions = page.get_image_rects(xref)
                    except PDF_EXCEPTIONS as error:
                        diagnostics.append(
                            {
                                "code": "IMAGE_LOCATION_FAILED",
                                "page": number,
                                "index": index,
                                "reason": type(error).__name__,
                            }
                        )
                        continue
                    for occurrence, rect in enumerate(regions):
                        objects.append(
                            {
                                "object_id": f"image:{number}:{index}:{occurrence}",
                                "kind": "image",
                                "page": number,
                                "bbox": list(rect),
                                "xref": xref,
                                "width": image[2],
                                "height": image[3],
                                "source_aliases": [],
                                "text": "",
                                "caption": None,
                                "section_ids": [],
                                "reference_targets": [],
                                "provenance": "embedded_bitmap_not_complete_figure",
                            }
                        )
            if kind in (None, "table"):
                try:
                    tables = page.find_tables()
                    for index, table in enumerate(tables.tables):
                        try:
                            cells = table.extract()
                        except PDF_EXCEPTIONS as error:
                            diagnostics.append(
                                {
                                    "code": "TABLE_EXTRACTION_FAILED",
                                    "page": number,
                                    "index": index,
                                    "reason": type(error).__name__,
                                }
                            )
                            continue
                        objects.append(
                            {
                                "object_id": f"table:{number}:{index}",
                                "kind": "table",
                                "page": number,
                                "bbox": list(table.bbox),
                                "cells": cells,
                                "rows": table.row_count,
                                "columns": table.col_count,
                                "text": "\n".join(
                                    " | ".join(c or "" for c in row) for row in cells
                                ),
                                "source_aliases": [],
                                "section_ids": [],
                                "reference_targets": [],
                                "provenance": "table_detector_unverified_cells",
                            }
                        )
                except PDF_EXCEPTIONS as error:
                    diagnostics.append(
                        {
                            "code": "TABLE_DETECTION_FAILED",
                            "page": number,
                            "reason": type(error).__name__,
                        }
                    )
    return objects, diagnostics


def render(store, doc, page_number, bbox=None, dpi=150):
    if not 36 <= dpi <= 400:
        raise PdfError("INVALID_DPI", "DPI must be 36–400")
    with open_pdf(doc["path"]) as pdf:
        if not 1 <= page_number <= len(pdf):
            raise PdfError("INVALID_PAGES", "Render page is outside the document")
        page = pdf[page_number - 1]
        rect = rectangle(page, bbox)
        if rect.width * rect.height * (dpi / 72) ** 2 > 30_000_000:
            raise PdfError("PIXEL_LIMIT", "Render exceeds 30 million pixels; crop or lower DPI")
        name = doc["document_id"] + "-" + digest([page_number, list(rect), dpi]) + ".png"
        path = store.root / "images-v2" / name
        try:
            pix = pymupdf.Pixmap(path) if store.image_valid(path) else None
        except PDF_EXCEPTIONS:
            pix = None
        if pix is None:
            pix = page.get_pixmap(clip=rect, dpi=dpi)
            store.save_image(path, pix.tobytes("png"))
        return {
            "page": page_number,
            "bbox": list(rect),
            "coordinate_system": "top_left_pdf_points_xyxy",
            "dpi": dpi,
            "width": pix.width,
            "height": pix.height,
            "image_path": str(path),
            "sha256": checksum(path),
            "provenance": "original_pdf_render",
        }


def extract_bitmap(store, doc, obj):
    if obj.get("width", 0) * obj.get("height", 0) > 30_000_000:
        raise PdfError("PIXEL_LIMIT", "Embedded image exceeds pixel budget")
    with open_pdf(doc["path"]) as pdf:
        try:
            pix = pymupdf.Pixmap(pdf, obj["xref"])
            if pix.width * pix.height > 30_000_000:
                raise PdfError("PIXEL_LIMIT", "Embedded image exceeds pixel budget")
            if pix.n - pix.alpha > 3:
                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
            mask = pdf.extract_image(obj["xref"]).get("smask", 0)
            if mask and not pix.alpha:
                pix = pymupdf.Pixmap(pix, pymupdf.Pixmap(pdf, mask))
            path = (
                store.root
                / "images-v2"
                / (doc["document_id"] + "-" + digest(obj["object_id"]) + ".png")
            )
            store.save_image(path, pix.tobytes("png"))
            return {
                "image_path": str(path),
                "width": pix.width,
                "height": pix.height,
                "provenance": "embedded_bitmap_not_complete_figure",
            }
        except PDF_EXCEPTIONS:
            raise PdfError(
                "IMAGE_EXTRACTION_FAILED", "Could not extract this embedded bitmap"
            ) from None
