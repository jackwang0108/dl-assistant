"""Opt-in real network and prepared-model validation."""

import os
from pathlib import Path

import pytest

from pdf_mcp.service import Service

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.getenv("PDF_MCP_RUN_LIVE") != "1", reason="Set PDF_MCP_RUN_LIVE=1"),
]


def test_real_fixed_revision_html_and_pdf(tmp_path):
    service = Service(tmp_path / "cache")
    source = service.open("https://arxiv.org/html/2404.14219v1")
    assert source["format"] == "html" and "Phi-3" in source["title"]
    doc = service.store.get(source["document_id"])
    assert doc["objects"] and any(b.get("math") for b in doc["blocks"])
    assert doc["origin"]["final_url"] == "https://arxiv.org/html/2404.14219v1"
    figure = next(o for o in doc["objects"] if o.get("assets"))
    images = service.get_object(source["document_id"], figure["object_id"], view="image")["items"][
        0
    ]
    assert images["assets"] and all(a.get("image_status") == "ready" for a in images["assets"])
    pdf = service.open("https://arxiv.org/pdf/2404.14219v1")
    assert pdf["format"] == "pdf" and pdf["identity_status"] == "unverified"
    assert service.render(pdf["document_id"], "1")["items"][0]["image_path"]


@pytest.mark.skipif(
    not os.getenv("PDF_MCP_STRUCTURE_PYTHON"), reason="Requires prepared Docling environment"
)
def test_real_docling_worker_and_cache(tmp_path):
    source = (
        Path(os.getenv("PDF_MCP_BENCH_DATA", "benchmark-data"))
        / "1706.03762v7.pdf"
    )
    if not source.is_file():
        pytest.skip("Download benchmark PDF first")
    service = Service(tmp_path / "cache")
    doc = service.open(str(source))["document_id"]
    parsed = service.parse(doc, "3", timeout=120)
    assert parsed["pages_processed"] == [3]
    objects = service.objects(doc, parse_id=parsed["parse_id"])["items"]
    figure = next(o for o in objects if o.get("kind") == "figure")
    assert "Transformer" in figure["caption"] and figure["page"] == 3 and figure["bbox"]
    image = service.get_object(doc, figure["object_id"], parsed["parse_id"], view="image")["items"][
        0
    ]["image"]
    assert Path(image["image_path"]).is_file()
    assert service.parse(doc, "3", timeout=120)["cache_state"] == "hit"
    assert service.read(doc, parse_id=parsed["parse_id"])["items"]


@pytest.mark.skipif(
    not os.getenv("PDF_MCP_STRUCTURE_PYTHON"), reason="Requires prepared Docling environment"
)
def test_real_formula_missing_text_is_explicit(tmp_path):
    source = (
        Path(os.getenv("PDF_MCP_BENCH_DATA", "benchmark-data"))
        / "1512.03385v1.pdf"
    )
    if not source.is_file():
        pytest.skip("Download benchmark PDF first")
    service = Service(tmp_path / "cache")
    doc = service.open(str(source))["document_id"]
    parsed = service.parse(doc, "3", timeout=120)
    equations = [
        o
        for o in service.objects(doc, parse_id=parsed["parse_id"])["items"]
        if o.get("kind") == "equation"
    ]
    assert equations and all(
        o["formula_status"] == "not_recognized_use_original_region" for o in equations
    )
    assert any(d["code"] == "FORMULA_NOT_RECOGNIZED" for d in parsed["diagnostics"])


@pytest.mark.skipif(
    os.getenv("PDF_MCP_RUN_MODEL_LIVE") != "1",
    reason="Explicit prepared OCR/formula models required",
)
def test_real_scanned_page_ocr_without_network(tmp_path):
    import io

    import pymupdf
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (1200, 400), "white")
    ImageDraw.Draw(image).text(
        (50, 70), "SCANNED TEXT: research evidence matters", fill="black", font_size=42
    )
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    path = tmp_path / "scan.pdf"
    with pymupdf.open() as pdf:
        p = pdf.new_page(width=600, height=200)
        p.insert_image(p.rect, stream=buffer.getvalue())
        pdf.save(path)
    service = Service(tmp_path / "cache")
    doc = service.open(str(path))["document_id"]
    assert service.page_info(doc, "1")["items"][0]["text_status"] == "no_text_layer"
    parsed = service.parse(doc, "1", ocr=True, timeout=180)
    payload = service.store.get_parse(doc, parsed["parse_id"])
    assert any("research evidence matters" in b["text"] for b in payload["blocks"])


@pytest.mark.skipif(
    os.getenv("PDF_MCP_RUN_MODEL_LIVE") != "1",
    reason="Explicit prepared OCR/formula models required",
)
def test_real_formula_recognition_requires_visual_check(tmp_path):
    source = (
        Path(os.getenv("PDF_MCP_BENCH_DATA", "benchmark-data"))
        / "1512.03385v1.pdf"
    )
    if not source.is_file():
        pytest.skip("Download benchmark PDF first")
    service = Service(tmp_path / "cache")
    doc = service.open(str(source))["document_id"]
    parsed = service.parse(doc, "3", formulas=True, timeout=180)
    equations = [
        o
        for o in service.store.get_parse(doc, parsed["parse_id"])["objects"]
        if o["kind"] == "equation"
    ]
    assert len(equations) >= 2
    assert all(
        o["formula_status"] == "model_recognition_unverified" and o["text"] for o in equations
    )
    assert r"\begin{matrix}" not in equations[0]["text"]
    assert any(d["code"] == "FORMULA_REQUIRES_VISUAL_CHECK" for d in parsed["diagnostics"])
    assert service.get_object(doc, equations[0]["object_id"], parsed["parse_id"], view="image")[
        "items"
    ][0]["image"]["image_path"]


@pytest.mark.skipif(
    not os.getenv("PDF_MCP_STRUCTURE_PYTHON"), reason="Requires prepared Docling environment"
)
def test_real_docling_table_cells_match_known_pdf(tmp_path, table_pdf):
    service = Service(tmp_path / "cache")
    doc = service.open(table_pdf)["document_id"]
    parsed = service.parse(doc, "1", timeout=120)
    tables = [
        o
        for o in service.store.get_parse(doc, parsed["parse_id"])["objects"]
        if o["kind"] == "table"
    ]
    assert tables and tables[0]["bbox"] and tables[0]["page"] == 1
    text = [cell["text"] for cell in tables[0]["cells"]]
    assert all(value in text for value in ["A1", "B1", "C1", "A4", "B4", "C4"])
    assert tables[0]["rows"] == 4 and tables[0]["columns"] == 3
