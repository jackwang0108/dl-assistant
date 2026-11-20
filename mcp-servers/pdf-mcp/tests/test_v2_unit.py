import json
import os
import time
from pathlib import Path

import httpx
import pytest

from pdf_mcp.acquire import Downloader, public_addresses
from pdf_mcp.models import Limits, PdfError, page_numbers
from pdf_mcp.paging import bounded
from pdf_mcp.store import Store
from pdf_mcp.structured import parse_structured


@pytest.mark.parametrize(
    "spec", ["", "0", "1-999999999", "3-1", "1-2garbage", "wrong", "1,999", "1-2,wrong"]
)
def test_invalid_page_selections_do_not_silently_read_subset(spec):
    with pytest.raises(PdfError):
        page_numbers(spec, 3)


def test_range_limits_and_order():
    assert page_numbers("3,1-2,2", 4) == [1, 2, 3]
    with pytest.raises(PdfError):
        page_numbers(None, 501)
    with pytest.raises(PdfError):
        page_numbers("1-501", 501)


def test_whole_json_budget_and_lossless_fragments():
    original = [{"kind": "table", "text": '\\"中文\n' * 5000}, {"kind": "body", "text": "done"}]
    records, fragments = [], {}
    page = bounded("doc", original, ["read"], 2000)
    while True:
        assert len(json.dumps(page, ensure_ascii=False)) <= 2000
        for item in page["items"]:
            if item.get("kind") == "record_fragment":
                key = item["record_index"]
                fragments.setdefault(key, []).append(item["text"])
                if item["final"]:
                    records.append(json.loads("".join(fragments[key])))
            else:
                records.append(item)
        if not page["next_cursor"]:
            break
        page = bounded("doc", original, ["read"], 2000, page["next_cursor"])
    assert records == original


def test_cursor_cannot_cross_request():
    result = bounded("doc", [{"text": "x" * 10000}], ["read"], 2000)
    for identity, scope, budget in [
        ("other", ["read"], 2000),
        ("doc", ["other"], 2000),
        ("doc", ["read"], 3000),
    ]:
        with pytest.raises(PdfError):
            bounded(identity, [{}], scope, budget, result["next_cursor"])
    with pytest.raises(PdfError):
        bounded("doc", [{}], [], 2000, "bad cursor")


def test_download_pins_checked_address_and_tls_name():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, content=b"%PDF-fake")

    downloader = Downloader(
        httpx.Client(transport=httpx.MockTransport(handler)), lambda _: ["8.8.8.8"]
    )
    data, origin = downloader.fetch("https://example.org/paper.pdf")
    assert data == b"%PDF-fake" and origin["requests"] == 1
    assert seen[0].url.host == "8.8.8.8"
    assert seen[0].headers["host"] == "example.org"
    assert seen[0].extensions["sni_hostname"] == "example.org"


@pytest.mark.parametrize(
    "url",
    ["file:///etc/passwd", "https://user:password@example.org/x", "https://example.org:9000/x"],
)
def test_download_rejects_unsafe_url(url):
    with pytest.raises(PdfError):
        Downloader(resolver=lambda _: ["8.8.8.8"]).fetch(url)


def test_private_dns_is_rejected(monkeypatch):
    monkeypatch.setattr("socket.getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("127.0.0.1", 0))])
    with pytest.raises(PdfError):
        public_addresses("rebind.example")


def test_every_redirect_destination_is_checked():
    hosts = []

    def resolver(host):
        hosts.append(host)
        if host == "private.example":
            raise PdfError("UNSAFE_URL", "private")
        return ["8.8.8.8"]

    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(302, headers={"location": "https://private.example/secret"})
        )
    )
    with pytest.raises(PdfError):
        Downloader(client, resolver).fetch("https://public.example/x")
    assert hosts == ["public.example", "private.example"]


def test_size_and_http_errors_distinct():
    client = httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, content=b"x" * 2000))
    )
    with pytest.raises(PdfError) as error:
        Downloader(client, lambda _: ["8.8.8.8"]).fetch(
            "https://example.org/x", Limits(max_bytes=1024)
        )
    assert error.value.code == "DOWNLOAD_SIZE"
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(401)))
    with pytest.raises(PdfError) as error:
        Downloader(client, lambda _: ["8.8.8.8"]).fetch("https://example.org/x")
    assert error.value.code == "HTTP_ERROR" and error.value.details["http_status"] == 401


def test_ttl_uses_numeric_timestamps_and_preserves_23_hour_old_entry(tmp_path):
    store = Store(tmp_path)
    doc = store.save(b"content", {"format": "pdf"})
    with store.db() as db:
        db.execute("UPDATE documents SET accessed=?", (time.time() - 23 * 3600,))
    assert store.clear(True, 24)["cleared_documents"] == 0
    with store.db() as db:
        db.execute("UPDATE documents SET accessed=?", (time.time() - 25 * 3600,))
    assert store.clear(True, 24)["cleared_documents"] == 1
    assert not Path(doc["path"]).exists()


def test_snapshot_mutation_detected_without_mtime_change(tmp_path):
    store = Store(tmp_path)
    doc = store.save(b"FIRST", {"format": "pdf"})
    path = Path(doc["path"])
    stamp = path.stat().st_mtime
    path.write_bytes(b"OTHER")
    os.utime(path, (stamp, stamp))
    with pytest.raises(PdfError) as error:
        store.get(doc["document_id"])
    assert error.value.code == "CACHE_CHANGED"


def test_html_keeps_math_source_spans_and_cross_section_targets():
    data = b"""<article><section id="S1"><h2>Method</h2><p>See <a href="#F1">Figure 1</a> and <a href="#R1">[1]</a>. <math alttext="x^2"><msup><mi>x</mi><mn>2</mn></msup></math></p></section><section id="S2"><h2>Other</h2><figure id="F1"><img src="fig.png"/><figcaption>Caption</figcaption></figure><li class="ltx_bibitem" id="R1">A Reference</li></section></article>"""
    result = parse_structured(data, "html", "https://arxiv.org/html/paper/")
    assert "$x^2$" in result["blocks"][1]["text"]
    assert result["blocks"][1]["reference_targets"] == ["F1", "R1"]
    assert result["objects"][0]["assets"][0]["source"] == "https://arxiv.org/html/paper/fig.png"
    assert result["references"][0]["reference_key"] == "R1"


def test_jats_and_merged_cells_preserved():
    xml = b"""<?xml version="1.0"?><article><front><article-title>Title</article-title></front><body><sec id="s1"><title>Method</title><p>See <xref rid="t1">Table 1</xref>.</p></sec><sec id="s2"><title>Results</title><table-wrap id="t1"><caption>Results table</caption><table><tr><td rowspan="2">Merged</td><td>0.9</td></tr></table></table-wrap></sec></body><back><ref-list><ref id="r1">Citation</ref></ref-list></back></article>"""
    result = parse_structured(xml, "xml")
    assert result["objects"][0]["rows"][0][0]["rowspan"] == "2"
    assert result["blocks"][1]["reference_targets"] == ["t1"]
    assert result["metadata"]["title"] == "Title"


def test_xml_external_entities_rejected():
    with pytest.raises(PdfError):
        parse_structured(
            b'<!DOCTYPE x [<!ENTITY x SYSTEM "file:///etc/passwd">]><article><p>&x;</p></article>',
            "xml",
        )


def test_proxy_uses_original_hostname_and_still_blocks_private_literal():
    seen = []
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: seen.append(str(request.url)) or httpx.Response(200, content=b"body")
        )
    )
    downloader = Downloader(
        client,
        lambda _: pytest.fail("Proxy must resolve remote names"),
        proxy_url="http://127.0.0.1:7890",
    )
    assert (
        downloader.fetch("https://arxiv.org/html/2404.14219v1")[1]["network_mode"]
        == "explicit_trusted_proxy"
    )
    assert seen[0].startswith("https://arxiv.org/")
    with pytest.raises(PdfError):
        downloader.fetch("http://127.0.0.1/private")


def test_parser_signature_and_local_base_affect_snapshot_identity(tmp_path):
    store = Store(tmp_path)
    first = store.save(
        b"<article/>", {"format": "html", "origin": {"local_path": "/one/paper.html"}}
    )
    second = store.save(
        b"<article/>", {"format": "html", "origin": {"local_path": "/two/paper.html"}}
    )
    assert first["document_id"] != second["document_id"]
    store.signature = "changed parser"
    third = store.save(
        b"<article/>", {"format": "html", "origin": {"local_path": "/one/paper.html"}}
    )
    assert first["document_id"] != third["document_id"]
