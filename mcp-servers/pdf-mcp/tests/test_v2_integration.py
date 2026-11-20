import io
import os
from pathlib import Path

import httpx
import pymupdf
import pytest
from PIL import Image

from pdf_mcp.acquire import Downloader
from pdf_mcp.models import PdfError
from pdf_mcp.service import Service


@pytest.fixture
def service(tmp_path):
    return Service(tmp_path / "cache")


def all_items(first, follow):
    items = list(first["items"])
    while first["next_cursor"]:
        first = follow(first["next_cursor"])
        items.extend(first["items"])
    return items


def test_open_restart_changed_same_mtime_and_immutable_original(service, text_pdf, tmp_path):
    doc = service.open(text_pdf)
    restarted = Service(service.store.root)
    assert restarted.info(doc["document_id"])["page_count"] == 3
    path = Path(text_pdf)
    stamp = path.stat().st_mtime
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((40, 40), "Replacement")
        pdf.save(tmp_path / "replacement.pdf")
    path.write_bytes((tmp_path / "replacement.pdf").read_bytes())
    os.utime(path, (stamp, stamp))
    changed = service.open(text_pdf)
    assert doc["document_id"] != changed["document_id"]
    original = service.read(doc["document_id"], pages="1")
    assert any("introduce" in i.get("text", "") for i in original["items"])


def test_two_pdfs_and_two_crops_do_not_overwrite(service, text_pdf, tmp_path):
    doc = service.open(text_pdf)["document_id"]
    one = service.render(doc, "1", [0, 0, 50, 50], 72)["items"][0]
    two = service.render(doc, "1", [50, 50, 150, 150], 72)["items"][0]
    assert one["image_path"] != two["image_path"]
    assert pymupdf.Pixmap(one["image_path"]).width == 50
    assert pymupdf.Pixmap(two["image_path"]).width == 100
    three = service.render(doc, "1", [0, 0, 50, 50], 144)["items"][0]
    assert three["image_path"] != one["image_path"] and three["width"] == 100
    negative = service.render(doc, "1", [-20, 0, 50, 50], 72)["items"][0]
    assert negative["bbox"] == [0, 0, 50, 50] and negative["width"] == 50
    Path(one["image_path"]).write_bytes(b"broken PNG")
    assert (
        pymupdf.Pixmap(service.render(doc, "1", [0, 0, 50, 50], 72)["items"][0]["image_path"]).width
        == 50
    )


@pytest.mark.parametrize(
    "bbox", [[0, 0, 0, 50], [0, 0, float("nan"), 50], [9999, 0, 10000, 50], [1, 2, 3]]
)
def test_bad_regions_rejected(service, text_pdf, bbox):
    doc = service.open(text_pdf)["document_id"]
    with pytest.raises(PdfError):
        service.render(doc, "1", bbox)


def test_shared_page_bookmarks_do_not_make_first_section_empty(service, tmp_path):
    path = tmp_path / "shared.pdf"
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text((40, 40), "First and second sections on one page.")
        pdf.set_toc([[1, "First", 1], [1, "Second", 1]])
        pdf.save(path)
    doc = service.open(str(path))["document_id"]
    result = service.read(doc, section="First")
    assert any("First and second" in i.get("text", "") for i in result["items"])
    assert result["items"][0]["coverage"] == "candidate_pages_including_shared_boundary_pages"


def test_page_limits_are_reported_not_silently_truncated(service, tmp_path):
    path = tmp_path / "many.pdf"
    with pymupdf.open() as pdf:
        for _ in range(501):
            pdf.new_page()
        pdf.save(path)
    doc = service.open(str(path))["document_id"]
    with pytest.raises(PdfError) as error:
        service.read(doc, "1-501")
    assert error.value.code == "PAGE_LIMIT"


def test_native_text_locations_region_and_scan_quality(service, text_pdf, tmp_path):
    doc = service.open(text_pdf)["document_id"]
    result = service.read(doc, "1", bbox=[0, 95, 500, 160])
    body = [i for i in result["items"] if i.get("kind") == "text"]
    assert body and all("Introduction" not in i["text"] for i in body)
    assert body[0]["bbox"] and body[0]["provenance"] == "pdf_text_layer"
    path = tmp_path / "scan.pdf"
    bitmap = io.BytesIO()
    Image.new("RGB", (100, 100), "white").save(bitmap, format="PNG")
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_image(page.rect, stream=bitmap.getvalue())
        pdf.save(path)
    scan = service.open(str(path))["document_id"]
    assert service.page_info(scan, "1")["items"][0]["text_status"] == "no_text_layer"


def test_two_images_limit_continuation_and_retrieval(service, tmp_path):
    path = tmp_path / "images.pdf"
    bitmap = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(bitmap, format="PNG")
    with pymupdf.open() as pdf:
        for _ in range(2):
            pdf.new_page().insert_image(pymupdf.Rect(10, 10, 40, 40), stream=bitmap.getvalue())
        pdf.save(path)
    doc = service.open(str(path))["document_id"]
    records = all_items(
        service.objects(doc, "image", max_chars=2000),
        lambda c: service.objects(doc, "image", max_chars=2000, cursor=c),
    )
    objects = [r for r in records if r.get("kind") == "image"]
    assert len(objects) == 2
    images = [
        service.get_object(doc, o["object_id"], view="image")["items"][0]["image"] for o in objects
    ]
    assert images[0]["image_path"] != images[1]["image_path"]
    assert all(pymupdf.Pixmap(i["image_path"]).width == 10 for i in images)


def test_table_cells_and_detection_failure_are_distinct(service, table_pdf, monkeypatch):
    doc = service.open(table_pdf)["document_id"]
    tables = service.objects(doc, "table")["items"]
    table = next(t for t in tables if t.get("kind") == "table")
    assert table["cells"][0] == ["A1", "B1", "C1"]
    assert service.get_object(doc, table["object_id"], view="image")["items"][0]["image"][
        "image_path"
    ]

    def broken(self, *a, **kw):
        raise RuntimeError("failed")

    monkeypatch.setattr(pymupdf.Page, "find_tables", broken)
    result = service.objects(doc, "table")["items"][0]
    assert (
        result["status"] == "partial"
        and result["diagnostics"][0]["code"] == "TABLE_DETECTION_FAILED"
    )


def test_search_locations_and_section_counts(service, multi_section_pdf):
    doc = service.open(multi_section_pdf)["document_id"]
    result = service.search(doc, "alpha beta", mode="and")
    assert result["items"][0]["pages_with_matches"] == [1, 4]
    assert all(m["bbox"] for m in result["items"][1:])
    result = service.search(doc, "alpha", section="Methods")
    assert result["items"][0]["searched_pages"] == 4
    assert 0 not in result["items"][0]["pages_with_matches"]
    with pytest.raises(PdfError):
        service.search(doc, "[bad", mode="regex")


def test_html_section_attaches_outside_figure_and_reference(service, tmp_path):
    path = tmp_path / "source.html"
    path.write_text(
        '<article><section id="S1"><h2>Method</h2><p>See <a href="#F1">Figure</a> twice <a href="#F1">Figure</a> and <a href="#R1">[1]</a>.</p></section><section id="S2"><h2>Other</h2><figure id="F1"><img src="fig.png"><figcaption>Caption</figcaption></figure></section><li class="ltx_bibitem" id="R1">Reference</li></article>'
    )
    Image.new("RGB", (10, 10), "red").save(tmp_path / "fig.png")
    doc = service.open(str(path))["document_id"]
    result = service.read(doc, section="S1")
    attached = [i for i in result["items"] if i.get("relationship") == "directly_referenced"]
    assert len(attached) == 2 and sum(i["kind"] == "figure" for i in attached) == 1
    figure = next(i for i in attached if i["kind"] == "figure")
    image = service.get_object(doc, figure["object_id"], view="image")["items"][0]
    assert image["assets"][0]["image_status"] == "ready"
    assert service.references(doc)["items"][1]["reference_key"] == "R1"
    assert service.search(doc, "Reference")["items"][0]["total_matches"] == 1
    with pytest.raises(PdfError):
        service.render(doc, "1")


def test_download_wrong_content_and_content_type_are_not_trusted(tmp_path):
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200, content=b"<html>login</html>", headers={"content-type": "application/pdf"}
            )
        )
    )
    service = Service(tmp_path / "cache", Downloader(client, lambda _: ["8.8.8.8"]))
    with pytest.raises(PdfError):
        service.open("https://example.org/paper.pdf")
    assert service.store.stats()["documents"] == 0


def test_explicit_source_candidates_require_revision_and_do_not_claim_identity(service, text_pdf):
    doc = service.open(text_pdf)["document_id"]
    with pytest.raises(PdfError):
        service.source_candidates(doc, "2404.14219")
    sources = service.source_candidates(doc, "2404.14219v1", "PMC123456")["candidates"]
    assert sources[0]["source"] == "https://arxiv.org/html/2404.14219v1"
    assert sources[0]["identity_status"] == "not_matched_to_pdf"


def test_clear_never_deletes_original_or_model_weights(service, text_pdf):
    service.open(text_pdf)
    model = service.store.root / "models" / "weight"
    model.parent.mkdir()
    model.write_bytes(b"weight")
    assert service.store.clear(False)["cleared_documents"] == 1
    assert Path(text_pdf).is_file() and model.is_file()


def test_parser_missing_is_explicit_and_native_reading_remains_available(
    service, text_pdf, monkeypatch
):
    doc = service.open(text_pdf)["document_id"]
    monkeypatch.setenv("PDF_MCP_STRUCTURE_PYTHON", "/missing/python")
    with pytest.raises(PdfError) as error:
        service.parse(doc, "1")
    assert error.value.code == "PARSER_UNAVAILABLE"
    assert service.read(doc, "1")["items"]


def test_valid_but_wrong_cached_png_is_rebuilt(service, text_pdf, tmp_path):
    doc = service.open(text_pdf)["document_id"]
    image = service.render(doc, "1", [0, 0, 50, 50], 72)["items"][0]
    Image.new("RGB", (50, 50), "blue").save(image["image_path"])
    recovered = service.render(doc, "1", [0, 0, 50, 50], 72)["items"][0]
    assert pymupdf.Pixmap(recovered["image_path"]).pixel(1, 1) == (255, 255, 255)
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((40, 40), "Another PDF")
        pdf.save(tmp_path / "other.pdf")
    other = service.open(str(tmp_path / "other.pdf"))["document_id"]
    assert (
        service.render(other, "1", [0, 0, 50, 50], 72)["items"][0]["image_path"]
        != recovered["image_path"]
    )


def fake_parser(tmp_path, body):
    import sys

    executable = tmp_path / "parser-python"
    executable.write_text(
        "#!"
        + sys.executable
        + '\nimport json,sys,time\nfrom pathlib import Path\nif sys.argv[1]=="-c":\n print("test-engine-1");sys.exit()\nrequest=json.loads(Path(sys.argv[2]).read_text())\n'
        + body
        + "\n"
    )
    executable.chmod(0o700)
    return str(executable)


def test_real_worker_boundary_cache_profile_and_partial_pages(
    service, text_pdf, tmp_path, monkeypatch
):
    executable = fake_parser(
        tmp_path,
        'Path(sys.argv[3]).write_text(json.dumps({"blocks":[],"objects":[],"sections":[],"references":[],"diagnostics":[],"pages_processed":[request["pages"][0]],"coverage":"inferred","engine_version":"test-engine-1"}))',
    )
    monkeypatch.setenv("PDF_MCP_STRUCTURE_PYTHON", executable)
    doc = service.open(text_pdf)["document_id"]
    parsed = service.parse(doc, "1-2")
    assert parsed["coverage"] == "partial" and parsed["diagnostics"][0]["pages"] == [2]
    assert service.parse(doc, "1-2")["cache_state"] == "hit"
    assert service.parse(doc, "1")["cache_state"] == "miss"
    other = service.open(str(Path(text_pdf)))["document_id"]
    assert other == doc


def test_worker_timeout_kills_process_and_preserves_pdf(service, text_pdf, tmp_path, monkeypatch):
    executable = fake_parser(tmp_path, "time.sleep(60)")
    monkeypatch.setenv("PDF_MCP_STRUCTURE_PYTHON", executable)
    doc = service.open(text_pdf)["document_id"]
    with pytest.raises(PdfError) as error:
        service.parse(doc, "1", timeout=5)
    assert error.value.code == "PARSER_TIMEOUT"
    assert not list((service.store.root / "jobs-v2").iterdir())
    assert service.read(doc, "1")["items"]


def test_malformed_worker_result_does_not_create_success_record(
    service, text_pdf, tmp_path, monkeypatch
):
    executable = fake_parser(tmp_path, 'Path(sys.argv[3]).write_text("not JSON")')
    monkeypatch.setenv("PDF_MCP_STRUCTURE_PYTHON", executable)
    doc = service.open(text_pdf)["document_id"]
    with pytest.raises(PdfError) as error:
        service.parse(doc, "1")
    assert error.value.code == "PARSER_INVALID_RESULT"
    assert service.store.stats()["parses"] == 0


def test_large_page_pixel_budget_checked_before_render(service, tmp_path):
    path = tmp_path / "large.pdf"
    with pymupdf.open() as pdf:
        pdf.new_page(width=10000, height=10000)
        pdf.save(path)
    doc = service.open(str(path))["document_id"]
    with pytest.raises(PdfError) as error:
        service.render(doc, "1", dpi=400)
    assert error.value.code == "PIXEL_LIMIT"
    with pytest.raises(PdfError) as error:
        service.parse(doc, "1")
    assert error.value.code == "PIXEL_LIMIT"


def test_text_extraction_failure_preserves_other_pages(service, text_pdf, monkeypatch):
    doc = service.open(text_pdf)["document_id"]
    original = pymupdf.Page.get_text

    def failing(self, *args, **kwargs):
        if self.number == 1:
            raise RuntimeError("broken text layer")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(pymupdf.Page, "get_text", failing)
    result = service.read(doc, "1-3")["items"]
    assert result[0]["status"] == "partial"
    assert any(
        d.get("code") == "TEXT_EXTRACTION_FAILED" and d["page"] == 2
        for d in result[0]["diagnostics"]
    )
    assert {b["page"] for b in result if b.get("kind") == "text"} == {1, 3}


def test_model_revision_change_invalidates_parse_cache(service, text_pdf, tmp_path, monkeypatch):
    executable = fake_parser(
        tmp_path,
        'Path(sys.argv[3]).write_text(json.dumps({"blocks":[],"objects":[],"sections":[],"references":[],"diagnostics":[],"pages_processed":request["pages"],"coverage":"inferred","engine_version":"test-engine-1"}))',
    )
    model_root = tmp_path / "models"
    revision = model_root / "hub/models--docling-project--example/refs/main"
    revision.parent.mkdir(parents=True)
    revision.write_text("revision-A")
    monkeypatch.setenv("PDF_MCP_STRUCTURE_PYTHON", executable)
    monkeypatch.setenv("PDF_MCP_MODEL_CACHE", str(model_root))
    doc = service.open(text_pdf)["document_id"]
    first = service.parse(doc, "1")
    assert service.parse(doc, "1")["cache_state"] == "hit"
    revision.write_text("revision-B")
    second = service.parse(doc, "1")
    assert second["cache_state"] == "miss" and second["parse_id"] != first["parse_id"]
