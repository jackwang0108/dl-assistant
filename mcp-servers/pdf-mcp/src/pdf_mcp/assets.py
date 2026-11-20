"""Explicit source-image retrieval; an HTML image URL is not an already acquired figure."""

import hashlib
import io
from pathlib import Path
from urllib.parse import urlsplit

import pymupdf
from PIL import Image

from .models import Limits, PdfError, digest
from .native import PDF_EXCEPTIONS


def images(service, doc, obj, dpi):
    results = []
    for asset in obj.get("assets", [])[:8]:
        value = dict(asset)
        try:
            source = asset["source"]
            if urlsplit(source).scheme in ("http", "https"):
                data, _ = service.downloader.fetch(
                    source, Limits(max_bytes=10_000_000, max_seconds=30, max_requests=4)
                )
            else:
                original = doc["origin"].get("local_path")
                if not original:
                    raise PdfError("ASSET_UNAVAILABLE", "No local source base path")
                base = Path(original).parent.resolve()
                path = (base / source).resolve()
                if (
                    not path.is_relative_to(base)
                    or not path.is_file()
                    or path.stat().st_size > 10_000_000
                ):
                    raise PdfError(
                        "ASSET_UNAVAILABLE",
                        "Local asset is missing, oversized or outside source directory",
                    )
                data = path.read_bytes()
            if data.lstrip().startswith(b"%PDF"):
                with pymupdf.open(stream=data, filetype="pdf") as pdf:
                    if not pdf.page_count or pdf.needs_pass:
                        raise PdfError("ASSET_UNAVAILABLE", "Unreadable image PDF")
                    page = pdf[0]
                    if page.rect.width * page.rect.height * (dpi / 72) ** 2 > 30_000_000:
                        raise PdfError("PIXEL_LIMIT", "Image exceeds pixel budget")
                    pix = page.get_pixmap(dpi=dpi)
                    value["source_pdf_pages"] = pdf.page_count
            else:
                with Image.open(io.BytesIO(data)) as source_image:
                    if source_image.width * source_image.height > 30_000_000:
                        raise PdfError("PIXEL_LIMIT", "Image exceeds pixel budget")
                pix = pymupdf.Pixmap(data)
            if pix.width * pix.height > 30_000_000:
                raise PdfError("PIXEL_LIMIT", "Image exceeds pixel budget")
            if pix.n - pix.alpha > 3:
                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
            target = (
                service.store.root
                / "images-v2"
                / (
                    doc["document_id"]
                    + "-"
                    + digest([source, hashlib.sha256(data).hexdigest(), dpi])
                    + ".png"
                )
            )
            service.store.save_image(target, pix.tobytes("png"))
            value.update(
                image_status="ready",
                image_path=str(target),
                view="source_asset_not_certified_compiled_figure",
            )
        except PdfError as error:
            value.update(image_status="unavailable", error=error.result()["error"])
        except (*PDF_EXCEPTIONS, Image.DecompressionBombError) as error:
            value.update(image_status="invalid_or_unsupported_image", reason=type(error).__name__)
        results.append(value)
    return results
