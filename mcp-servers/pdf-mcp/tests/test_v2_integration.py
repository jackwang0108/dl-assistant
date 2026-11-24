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


def test_rotated_cropbox_aligns_search_read_and_original_image(service, tmp_path):
    path = tmp_path / "rotation.pdf"
    with pymupdf.open() as pdf:
        page = pdf.new_page(width=600, height=400)
        page.insert_text((475, 150), "rotated-evidence")
        for x in (150, 220, 290):
            page.draw_line((x, 100), (x, 180))
        for y in (100, 140, 180):
            page.draw_line((150, y), (290, y))
        for x, y, label in ((155, 120, "A1"), (225, 120, "B1"), (155, 155, "A2"), (225, 155, "B2")):
            page.insert_text((x, y), label)
        page.set_cropbox(pymupdf.Rect(25, 40, 575, 350))
        page.set_rotation(90)
        pdf.save(path)
    doc = service.open(str(path))["document_id"]
    match = service.search(doc, "rotated-evidence")["items"][1]
    assert match["bbox"][1] == pytest.approx(450)
    cropped = service.read(doc, match_ref=match["match_ref"], padding_points=10)["items"]
    crop = next(item for item in cropped if item["kind"] == "original_page_crop")
    assert any(item.get("text") == "rotated-evidence" for item in cropped)
    manual_crop = service.render(doc, "1", bbox=crop["bbox"])["items"][0]
    assert manual_crop["sha256"] == crop["sha256"]
    assert min(pymupdf.Pixmap(crop["image_path"]).samples) < 100
    region = service.read(doc, "1", bbox=crop["bbox"])["items"]
    assert any(item.get("text") == "rotated-evidence" for item in region)
    table = next(item for item in service.objects(doc, "table")["items"] if item["kind"] == "table")
    assert table["bbox"] == pytest.approx([170, 125, 250, 265])
    assert any(
        "A1" in item.get("text", "") for item in service.read(doc, "1", bbox=table["bbox"])["items"]
    )


def test_bookmark_and_pages_are_intersected_for_read_and_search(service, text_pdf):
    doc = service.open(text_pdf)["document_id"]
    selected = service.read(doc, pages="1", section="Introduction")["items"]
    assert selected[0]["selected_pages"] == [1]
    assert {item["page"] for item in selected if "page" in item} == {1}
    empty = service.read(doc, pages="3", section="Introduction")["items"]
    assert empty[0]["selected_pages"] == []
    assert not any(item["kind"] == "text" for item in empty)
    summary = service.search(doc, "experiments", pages="1", section="Introduction")["items"][0]
    assert summary["total_matches"] == 0 and summary["selected_pages"] == [1]


def test_search_coverage_keeps_blank_and_failed_pages(service, tmp_path, monkeypatch):
    path = tmp_path / "coverage.pdf"
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((30, 30), "evidence")
        pdf.new_page()
        pdf.new_page()
        pdf.save(path)
    doc = service.open(str(path))["document_id"]
    get_text = pymupdf.Page.get_text

    def extract(page, *args, **kwargs):
        if page.number == 2:
            raise RuntimeError("test extraction failure")
        return get_text(page, *args, **kwargs)

    monkeypatch.setattr(pymupdf.Page, "get_text", extract)
    summary = service.search(doc, "missing")["items"][0]
    assert summary["total_matches"] == 0 and summary["searched_pages"] == 3
    assert summary["selected_pages"] == [1, 2, 3]
    assert summary["pages_with_searchable_text"] == [1]
    assert summary["pages_without_searchable_text"] == [2]
    assert summary["pages_extraction_failed"] == [3]


def test_parsed_section_can_be_read_inside_page_filter_and_match_keeps_parse_id(service, text_pdf):
    doc = service.open(text_pdf)["document_id"]
    method = {"id": "sec:m", "title": "Method", "level": 1, "page": 1}
    raw_match = service.search(doc, "experiments", pages="2")["items"][1]
    payload = {
        "sections": [method],
        "pages_processed": [1, 2],
        "coverage": "partial",
        "diagnostics": [{"code": "PAGES_NOT_PROCESSED", "pages": [3]}],
        "blocks": [
            {"block_id": "heading", "page": 1, "text": "Method", "section_id": "sec:m"},
            {
                "block_id": "result",
                "kind": "text",
                "page": 2,
                "text": "Model experiment",
                "bbox": raw_match["bbox"],
                "provenance": "docling_inferred_structure",
            },
        ],
    }
    parse_id = service.store.save_parse(doc, {"test": "partial"}, payload)["parse_id"]
    items = service.read(doc, pages="2", section="Method", parse_id=parse_id)["items"]
    assert items[0]["selected_pages"] == [2]
    assert items[-1]["block_id"] == "result"
    summary, match = service.search(doc, "experiment", parse_id=parse_id)["items"]
    assert summary["pages_not_processed"] == [3]
    items = service.read(doc, match_ref=match["match_ref"])["items"]
    assert items[0]["parse_id"] == parse_id
    assert any(i["kind"] == "original_page_crop" for i in items)
    assert any(i.get("provenance") == "docling_inferred_structure" for i in items[1:])


@pytest.mark.parametrize("format_", ["html", "xml"])
def test_structured_match_uses_source_neighbors_links_and_snapshot(service, tmp_path, format_):
    source = tmp_path / f"source.{format_}"
    if format_ == "html":
        text = """<article><section id="method"><h2>Method</h2><p id="context">Before</p>
        <p id="passage">Latency <a href="#figure">Figure</a> <a href="#bib">[1]</a></p></section>
        <section id="other"><h2>Other</h2><p>Unrelated</p>
        <figure id="figure"><figcaption>Chart</figcaption></figure></section>
        <li class="ltx_bibitem" id="bib">Reference</li></article>"""
    else:
        text = """<?xml version="1.0"?><article><body><sec id="method"><title>Method</title>
        <p id="context">Before</p><p id="passage">Latency <xref rid="figure">Figure</xref>
        <xref rid="bib">[1]</xref></p></sec><sec id="other"><title>Other</title>
        <p>Unrelated</p><fig id="figure"><caption>Chart</caption></fig></sec></body>
        <back><ref-list><ref id="bib"><mixed-citation>Reference</mixed-citation></ref></ref-list>
        </back></article>"""
    source.write_text(text)
    doc = service.open(str(source))["document_id"]
    for operation in (
        lambda: service.search(doc, "Latency", pages="99"),
        lambda: service.read(doc, pages="99"),
    ):
        with pytest.raises(PdfError) as invalid:
            operation()
        assert invalid.value.code == "NO_PAGE_MAPPING"
    match = service.search(doc, "Latency", section="method")["items"][1]
    assert match["source_id"] == "passage" and match["section_ids"] == ["method"]
    opts = {"match_ref": match["match_ref"], "context_blocks": 3, "max_chars": 2000}
    first = service.read(doc, **opts)
    assert first["next_cursor"]
    items = all_items(first, lambda cursor: service.read(doc, **opts, cursor=cursor))
    assert any(i.get("source_id") == "context" for i in items)
    assert {i["kind"] for i in items if i.get("relationship") == "directly_referenced"} == {
        "figure",
        "reference",
    }
    assert all(i.get("text") != "Unrelated" for i in items)
    with pytest.raises(PdfError) as cursor_error:
        service.read(doc, **{**opts, "context_blocks": 1}, cursor=first["next_cursor"])
    assert cursor_error.value.code == "INVALID_CURSOR"
    source.write_text(text.replace("Latency", "Throughput"))
    revised = service.open(str(source))["document_id"]
    with pytest.raises(PdfError) as snapshot_error:
        service.read(revised, **opts)
    assert snapshot_error.value.code == "INVALID_MATCH_REF"


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
