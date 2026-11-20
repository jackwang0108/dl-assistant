"""Verified compile PDF rasterization and bounded visual comparisons."""

import math
import re

import pymupdf
from PIL import Image, ImageChops

from .models import OverleafError, checksum, digest

PDF_ERRORS = (OSError, ValueError, RuntimeError, pymupdf.mupdf.FzErrorBase)


def validate_pdf(data):
    try:
        with pymupdf.open(stream=data, filetype="pdf") as pdf:
            if not pdf.is_pdf or pdf.needs_pass or not len(pdf):
                raise ValueError()
            return {"pages": len(pdf), "format_valid": True}
    except PDF_ERRORS:
        raise OverleafError("INVALID_PDF", "Output is not a readable PDF") from None


def pages(spec, count, limit=10):
    result = set()
    for piece in spec.split(","):
        m = re.fullmatch(r"\s*(\d+)(?:\s*-\s*(\d+))?\s*", piece)
        if not m:
            raise OverleafError("INVALID_PAGES", "Use 1-based pages such as 1-3,5")
        start, end = int(m[1]), int(m[2] or m[1])
        if not 1 <= start <= end <= count or end - start + 1 > limit:
            raise OverleafError(
                "INVALID_PAGES", "Page range is invalid or exceeds the operation limit"
            )
        result.update(range(start, end + 1))
        if len(result) > limit:
            raise OverleafError("PAGE_LIMIT", "Select at most ten rendered pages")
    return sorted(result)


def render(store, record, pdf_path, spec, dpi=150, bbox=None):
    if not 36 <= dpi <= 400:
        raise OverleafError("INVALID_DPI", "DPI must be 36–400")
    result = []
    with pymupdf.open(pdf_path) as pdf:
        for number in pages(spec, len(pdf)):
            p = pdf[number - 1]
            rect = p.rect
            if bbox is not None:
                if (
                    len(bbox) != 4
                    or any(not math.isfinite(x) for x in bbox)
                    or bbox[2] <= bbox[0]
                    or bbox[3] <= bbox[1]
                ):
                    raise OverleafError(
                        "INVALID_BBOX", "Use finite positive-area xyxy PDF coordinates"
                    )
                rect = rect & pymupdf.Rect(bbox)
                if rect.is_empty:
                    raise OverleafError("INVALID_BBOX", "Crop is outside the PDF page")
            if rect.width * rect.height * (dpi / 72) ** 2 > 30_000_000:
                raise OverleafError(
                    "PIXEL_LIMIT", "Render exceeds 30 million pixels; crop or lower DPI"
                )
            name = (
                "page-"
                + digest([record["outputs"]["output.pdf"]["sha256"], number, dpi, list(rect)])
                + ".png"
            )
            path = store.directory(record["project_id"], record["compile_id"]) / name
            pix = p.get_pixmap(clip=rect, dpi=dpi)
            store.write(path, pix.tobytes("png"))
            result.append(
                {
                    "page": number,
                    "bbox": list(rect),
                    "dpi": dpi,
                    "width": pix.width,
                    "height": pix.height,
                    "path": str(path),
                    "sha256": checksum(path),
                    "provenance": "original_compile_pdf",
                }
            )
    return result


def compare(store, left, right, left_pdf, right_pdf, selected="1-3"):
    with pymupdf.open(left_pdf) as a, pymupdf.open(right_pdf) as b:
        count = min(len(a), len(b))
        numbers = pages(selected, max(len(a), len(b)), limit=10)
        changes = [{"kind": "page_count", "left": len(a), "right": len(b)}]
        for number in numbers:
            if number > count:
                changes.append({"page": number, "status": "page_added_or_removed"})
                continue
            left_page = render(store, left, left_pdf, str(number), dpi=72)[0]
            right_page = render(store, right, right_pdf, str(number), dpi=72)[0]
            with Image.open(left_page["path"]) as aa, Image.open(right_page["path"]) as bb:
                if aa.size != bb.size:
                    status = "page_dimensions_changed"
                    region = None
                else:
                    region = ImageChops.difference(aa.convert("RGB"), bb.convert("RGB")).getbbox()
                    status = "visual_change" if region else "same_rendered_pixels"
            changes.append(
                {
                    "page": number,
                    "status": status,
                    "changed_pixel_bbox": region,
                    "left_image": left_page["path"],
                    "right_image": right_page["path"],
                    "meaning": "visual_difference_not_scientific_or_editorial_judgment",
                }
            )
    return changes
