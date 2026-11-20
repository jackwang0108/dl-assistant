"""Source images and explicit original-PDF crops; TeX compilation is container-only."""

import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
from pathlib import Path

import pymupdf

from .acquire import contained, sha
from .models import TexError
from .storage import digest


def valid_cached_image(path):
    try:
        pix = pymupdf.Pixmap(path)
        return 0 < pix.width * pix.height <= 30_000_000
    except (OSError, ValueError, RuntimeError, pymupdf.mupdf.FzErrorBase):
        return False


def save_image(pixmap, target):
    with tempfile.TemporaryDirectory(dir=target.parent) as temporary:
        staged = Path(temporary) / "image.png"
        pixmap.save(staged)
        os.replace(staged, target)


def source_images(storage, doc, obj, dpi=160):
    if not 36 <= dpi <= 400:
        raise TexError("INVALID_INPUT", "DPI must be between 36 and 400")
    root = storage.source_root(doc["document_id"])
    result = []
    for asset in obj["assets"]:
        if asset["status"] != "resolved":
            result.append({**asset, "image_status": asset["status"]})
            continue
        path = contained(root, asset["paths"][0])
        suffix = path.suffix.lower()
        item = {**asset, "path": str(path), "view": "source_asset_not_compiled_figure"}
        if suffix in (".png", ".jpg", ".jpeg"):
            try:
                pix = pymupdf.Pixmap(path)
                if pix.width * pix.height > 30_000_000:
                    raise ValueError("Excessive pixels")
                item.update(image_path=str(path), image_status="ready")
            except (OSError, ValueError, RuntimeError, pymupdf.mupdf.FzErrorBase):
                item.update(image_status="invalid_image")
        elif suffix == ".pdf":
            key = digest([doc["document_id"], sha(path), dpi, 0])
            target = storage.root / "renders" / (key + ".png")
            target.parent.mkdir(exist_ok=True)
            try:
                with pymupdf.open(path) as pdf:
                    if not pdf.is_pdf or pdf.page_count < 1:
                        raise ValueError()
                    page = pdf[0]
                    if page.rect.width * page.rect.height * (dpi / 72) ** 2 > 30_000_000:
                        raise ValueError()
                    if not valid_cached_image(target):
                        save_image(page.get_pixmap(dpi=dpi), target)
                    item.update(
                        image_path=str(target),
                        image_status="ready",
                        page=1,
                        total_pages=pdf.page_count,
                    )
            except (OSError, ValueError, RuntimeError, pymupdf.mupdf.FzErrorBase):
                item.update(image_status="rasterization_failed")
        else:
            item.update(image_status="unsupported_format")
        result.append(item)
    return result


def attach_pdf(storage, document_id, path, basis=None):
    storage.get(document_id)
    path = Path(path).expanduser()
    if not path.is_file():
        raise TexError("PDF_NOT_FOUND", "PDF file does not exist")
    try:
        with pymupdf.open(path) as pdf:
            if not pdf.is_pdf or pdf.page_count < 1 or pdf.needs_pass:
                raise TexError("INVALID_PDF", "Readable PDF required")
            count = pdf.page_count
    except (OSError, ValueError, RuntimeError, pymupdf.mupdf.FzErrorBase):
        raise TexError("INVALID_PDF", "Readable PDF required") from None
    checksum = sha(path)
    folder = storage.root / "pdf"
    folder.mkdir(exist_ok=True)
    target = folder / (checksum + ".pdf")
    if not target.exists():
        shutil.copyfile(path, target)
    value = {
        "pdf_ref": checksum,
        "document_id": document_id,
        "sha256": checksum,
        "pages": count,
        "path": str(target),
        "identity_status": "unverified",
        "identity_basis": basis,
    }
    with storage.db() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS pdfs (id TEXT, doc TEXT, payload TEXT, PRIMARY KEY(id,doc))"
        )
        db.execute(
            "INSERT OR REPLACE INTO pdfs VALUES(?,?,?)", (checksum, document_id, json.dumps(value))
        )
    return value


def render_object(
    storage, document_id, obj, pdf_ref=None, page=None, bbox=None, dpi=160, method="pdf"
):
    if not 36 <= dpi <= 400:
        raise TexError("INVALID_INPUT", "DPI must be between 36 and 400")
    image = os.getenv("TEX_MCP_RENDER_IMAGE", "")
    key = digest(
        [
            document_id,
            obj["object_id"],
            pdf_ref,
            page,
            bbox,
            dpi,
            method,
            image if method == "isolated_tex" else None,
        ]
    )
    target = storage.root / "renders" / (key + ".png")
    target.parent.mkdir(exist_ok=True)
    if method == "pdf":
        if pdf_ref is None or page is None or bbox is None or len(bbox) != 4:
            raise TexError(
                "PDF_MAPPING_REQUIRED", "Provide attached PDF, 1-based page and explicit bbox"
            )
        try:
            with storage.db() as db:
                row = db.execute(
                    "SELECT payload FROM pdfs WHERE id=? AND doc=?", (pdf_ref, document_id)
                ).fetchone()
        except sqlite3.OperationalError:
            row = None
        if not row:
            raise TexError("PDF_NOT_FOUND", "PDF is not attached to this document")
        value = json.loads(row[0])
        if sha(value["path"]) != pdf_ref:
            raise TexError("CACHE_CHANGED", "Attached PDF checksum changed")
        with pymupdf.open(value["path"]) as pdf:
            if not 1 <= page <= pdf.page_count:
                raise TexError("INVALID_INPUT", "PDF page out of range")
            rectangle = pymupdf.Rect(bbox)
            if (
                rectangle.is_empty
                or rectangle.is_infinite
                or not pdf[page - 1].rect.contains(rectangle)
            ):
                raise TexError("INVALID_INPUT", "Crop must be a finite rectangle inside the page")
            if rectangle.width * rectangle.height * (dpi / 72) ** 2 > 30_000_000:
                raise TexError("RENDER_BUDGET", "Pixel limit exceeded")
            if not valid_cached_image(target):
                save_image(pdf[page - 1].get_pixmap(clip=rectangle, dpi=dpi), target)
        return {
            "image_path": str(target),
            "method": "original_pdf_crop",
            "mapping": "explicit_user_supplied",
            "pdf_identity_status": value["identity_status"],
            "page": page,
            "bbox": bbox,
            "dpi": dpi,
        }
    if method != "isolated_tex":
        raise TexError("INVALID_INPUT", "Unknown render method")
    if not shutil.which("docker") or "@sha256:" not in image:
        raise TexError(
            "RENDER_UNAVAILABLE",
            "Configure a digest-pinned TEX_MCP_RENDER_IMAGE and working Docker; host TeX execution is disabled",
        )
    doc = storage.get(document_id)
    source = storage.source_root(document_id)
    latex = doc["text"][obj["start"] : obj["end"]]
    preamble = doc["text"][: doc["body_start"]]
    preamble = (
        preamble[: preamble.rfind("\\begin{document}")]
        if "\\begin{document}" in preamble
        else preamble
    )
    # Keep the original class/packages; isolation limits the actual interpreter.
    content = preamble + "\n\\begin{document}\n" + latex + "\n\\end{document}\n"
    with tempfile.TemporaryDirectory(prefix="tex-render-", dir=storage.root) as tmp:
        work = Path(tmp)
        (work / "object.tex").write_text(content)
        command = [
            "docker",
            "run",
            "--rm",
            "--pull=never",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--pids-limit=64",
            "--memory=512m",
            "--cpus=1",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=128m",
            "--env",
            "TEXINPUTS=/source//:",
            "--volume",
            str(source) + ":/source:ro",
            "--volume",
            str(work) + ":/work:rw",
            "--workdir",
            "/work",
            image,
            "pdflatex",
            "-no-shell-escape",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "object.tex",
        ]
        try:
            run = subprocess.run(
                command,
                capture_output=True,
                check=False,
                timeout=35,
                env={
                    k: v
                    for k, v in os.environ.items()
                    if k in ("PATH", "HOME", "DOCKER_HOST", "DOCKER_CONTEXT")
                },
            )
        except subprocess.TimeoutExpired:
            raise TexError("RENDER_TIMEOUT", "Isolated TeX compilation timed out") from None
        pdf_path = work / "object.pdf"
        if run.returncode != 0 or not pdf_path.exists():
            raise TexError("RENDER_FAILED", "Isolated compiler failed", exit_code=run.returncode)
        with pymupdf.open(pdf_path) as pdf:
            if not pdf.page_count:
                raise TexError("RENDER_FAILED", "Compiler produced no pages")
            page_obj = pdf[0]
            if page_obj.rect.width * page_obj.rect.height * (dpi / 72) ** 2 > 30_000_000:
                raise TexError("RENDER_BUDGET", "Pixel limit exceeded")
            save_image(page_obj.get_pixmap(dpi=dpi), target)
    return {
        "image_path": str(target),
        "method": "isolated_tex_reconstruction",
        "dpi": dpi,
        "limitations": ["Reconstruction is not the original published page layout."],
    }
