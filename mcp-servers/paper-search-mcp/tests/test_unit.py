import threading
import time

import httpx
import pytest
from pydantic import ValidationError

from paper_search_mcp.identity import normalize_ref
from paper_search_mcp.models import Budget, DateRange, PaperFilters, PaperLookup, PaperQuery
from paper_search_mcp.providers import arxiv_records, oa_record, scholar_record, ss_record
from paper_search_mcp.store import Store
from paper_search_mcp.transport import Operation, SourceError, Transport
from conftest import ATOM, OA_PAPER, SCHOLAR_PAPER, SS_PAPER


@pytest.mark.parametrize(
    "value,expected",
    [
        ("https://doi.org/10.1234/ABC", "doi:10.1234/abc"),
        ("https://arxiv.org/pdf/1706.03762v2.pdf", "arxiv:1706.03762"),
        ("1706.03762v1", "arxiv:1706.03762"),
        ("https://arxiv.org/abs/hep-th/9701001", "arxiv:hep-th/9701001"),
        ("https://openalex.org/W123", "openalex:W123"),
        ("https://www.semanticscholar.org/paper/title/ABC", "s2:abc"),
    ],
)
def test_normalized_ref(value, expected):
    assert normalize_ref(value) == expected


@pytest.mark.parametrize("value", ["42", "doi:", "unknown:1"])
def test_invalid_refs(value):
    with pytest.raises(ValueError):
        normalize_ref(value)


@pytest.mark.parametrize(
    "construct",
    [
        lambda: Budget(max_requests=0),
        lambda: Budget(max_items=-1),
        lambda: Budget(max_seconds=0),
        lambda: DateRange(date_type="published"),
        lambda: DateRange(date_type="published", start="2025-01-01", end="2024-01-01"),
        lambda: PaperQuery(text="x", syntax="source_native"),
        lambda: PaperLookup(),
        lambda: PaperLookup(identifier="x", title="y"),
    ],
)
def test_input_validation(construct):
    with pytest.raises(ValidationError):
        construct()


def test_parsers_keep_snippet_separate_and_correct_scholar_id():
    r = scholar_record(SCHOLAR_PAPER)
    assert r["year"] == 2017
    assert r.get("abstract") is None and r["snippet"] == "Partial text"
    assert "scholar_cites:12345" in r["identifiers"]
    assert [a["url"] for a in r["assets"] if a["type"] == "pdf"] == [
        "https://papers.test/paper.pdf"
    ]
    assert oa_record(OA_PAPER)["abstract"] == "OpenAlex abstract"
    assert arxiv_records(ATOM)[0][0]["version"] == "v1"


def test_independent_observations_and_authors(tmp_path):
    store = Store(tmp_path)
    a = arxiv_records(ATOM)[0][0]
    b = ss_record(SS_PAPER)
    store.save_record(a)
    store.save_record(b)
    raw = store.paper("arxiv:1706.03762", "sources")["observations"]
    assert next(r for r in raw if r["source"] == "arxiv")["abstract"] == "arXiv full abstract"
    result = store.paper("doi:10.1234/attention")
    assert len(result["authors"]) == 2
    assert len(result["conflicts"]["abstract"]) == 2
    assert result["citation_counts"] == [
        {"source": "semantic_scholar", "value": 100, "fetched_at": b["fetched_at"]}
    ]


def test_same_title_distinct_ids_and_version_history(tmp_path):
    store = Store(tmp_path)
    one = ss_record(SS_PAPER)
    two = ss_record({**SS_PAPER, "paperId": "different", "externalIds": {"DOI": "10.1234/other"}})
    store.save_record(one)
    store.save_record(two)
    assert "doi:10.1234/other" not in store.paper("s2:s1")["identifiers"]
    store.save_record(arxiv_records(ATOM)[0][0])
    store.save_record(arxiv_records(ATOM.replace("v1", "v2"))[0][0])
    assert {
        v["version"]
        for v in store.paper("arxiv:1706.03762", "versions")["versions"]
        if v["source"] == "arxiv"
    } == {"v1", "v2"}
    assert store.paper("arxiv:1706.03762", version="v1")["version"] == "v1"


def test_bridge_aliases_unifies_without_title_matching(tmp_path):
    store = Store(tmp_path)
    store.save_record(ss_record(SS_PAPER))
    store.save_record(oa_record({**OA_PAPER, "doi": None}))
    store.save_record(oa_record(OA_PAPER))
    assert "s2:s1" in store.paper("openalex:W1")["identifiers"]


def test_date_filters_are_sent_and_no_silent_fallback(make_service):
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(200, json={"data": [], "total": 0})

    service = make_service(handler)
    filters = PaperFilters(
        date_range=DateRange(date_type="published", start="2025-01-01", end="2025-12-31")
    )
    service.search_papers([PaperQuery(text="x", sources=["semantic_scholar"])], filters=filters)
    assert calls[0].url.params["publicationDateOrYear"] == "2025-01-01:2025-12-31"
    calls.clear()
    r = service.search_papers([PaperQuery(text="x", sources=["arxiv"])], filters=filters)
    assert not calls and r["source_reports"][0]["status"] == "unsupported"


def test_retry_budget_and_no_secret_in_errors():
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(429, headers={"Retry-After": "0"})

    transport = Transport(httpx.Client(transport=httpx.MockTransport(handler)), {"scholar": 0})
    op = Operation(Budget(max_requests=1))
    with pytest.raises(SourceError) as exc:
        transport.json("scholar", "https://serpapi.com/search", op, params={"api_key": "SECRET"})
    assert len(calls) == 1 and "SECRET" not in str(exc.value)
    assert exc.value.kind == "rate_limit"


def test_business_error_not_empty_success():
    transport = Transport(
        httpx.Client(
            transport=httpx.MockTransport(
                lambda req: httpx.Response(200, json={"error": "secret details"})
            )
        ),
        {"scholar": 0},
    )
    with pytest.raises(SourceError) as exc:
        transport.json("scholar", "https://serpapi.com/search", Operation())
    assert "secret details" not in str(exc.value)


def test_rate_limiter_serializes_actual_requests():
    starts = []

    def handler(req):
        starts.append(time.monotonic())
        time.sleep(0.04)
        return httpx.Response(200, json={})

    t = Transport(httpx.Client(transport=httpx.MockTransport(handler)), {"scholar": 0.02})
    threads = [
        threading.Thread(target=t.json, args=("scholar", "https://example.org", Operation()))
        for _ in range(2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert starts[1] - starts[0] >= 0.055


def test_http_date_retry_after():
    assert Transport.retry_delay("Thu, 01 Jan 1970 00:00:00 GMT", 2) == 0
    assert Transport.retry_delay("invalid", 2) == 2


def test_invalid_atom_rejected():
    with pytest.raises(SourceError):
        arxiv_records("<html>blocked</html>")


def test_generic_paper_url_and_version_discrimination():
    from paper_search_mcp.identity import version_from_ref

    assert (
        normalize_ref("https://openreview.net/forum?id=abc#details")
        == "url:https://openreview.net/forum?id=abc"
    )
    assert version_from_ref("doi:10.1234/methodv1") is None
    assert version_from_ref("https://arxiv.org/pdf/1706.03762v2.pdf?download=1") == "v2"
    assert version_from_ref(" https://arxiv.org/pdf/1706.03762%76%32.pdf ") == "v2"
    with pytest.raises(ValueError, match="revision"):
        normalize_ref("arxiv:1706.03762v0")


@pytest.mark.parametrize("bounds", [{}, {"start": 2025, "end": 2024}, {"start": "2024"}])
def test_publication_year_range_checks(bounds):
    from paper_search_mcp.models import PublicationYearRange

    with pytest.raises(ValueError):
        PublicationYearRange.model_validate(bounds)
    assert PublicationYearRange(start=2025).end is None


def test_recommendations_request_uses_verified_endpoint(make_service):
    calls = []

    def handler(req):
        calls.append(req)
        if req.url.path != "/recommendations/v1/papers/forpaper/ARXIV:1706.03762":
            return httpx.Response(404)
        return httpx.Response(200, json={"recommendedPapers": [SS_PAPER]})

    s = make_service(handler)
    r = s.find_related_papers(
        ["arxiv:1706.03762"], "provider_recommendations", budget=Budget(max_items=2)
    )
    assert r["items"] and calls[0].url.params["from"] == "all-cs"


def test_queued_request_respects_deadline():
    t = Transport(intervals={"scholar": 0.0})
    t.locks["scholar"].acquire()
    try:
        with pytest.raises(SourceError) as exc:
            t.json("scholar", "https://example.org", Operation(Budget(max_seconds=0.01)))
        assert exc.value.kind == "budget"
    finally:
        t.locks["scholar"].release()


def test_unsupported_sort_report_is_explicit(make_service):
    s = make_service(lambda req: httpx.Response(200, json={"data": []}))
    filters = PaperFilters(unsupported="report")
    r = s.search_papers(
        [PaperQuery(text="x", sources=["semantic_scholar"])], filters=filters, sort="date_desc"
    )
    assert r["source_reports"][0]["status"] == "partial"
    assert "Not enforced: sort:date_desc" in r["source_reports"][0]["limitations"]


def test_http_info_logs_redact_api_keys(caplog):
    import logging

    transport = Transport(
        httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={}))),
        {"scholar": 0.0},
    )
    with caplog.at_level(logging.INFO, logger="httpx"):
        transport.json(
            "scholar",
            "https://serpapi.com/search",
            Operation(),
            params={"api_key": "secret-value", "q": "test"},
        )
    assert "secret-value" not in caplog.text
    assert "[REDACTED]" in caplog.text


@pytest.mark.parametrize("value", ["arxiv:garbage", "doi:broken", "openalex:A123"])
def test_malformed_external_ids_rejected(value):
    with pytest.raises(ValueError):
        normalize_ref(value)


def test_generic_url_preserves_encoded_query_delimiters():
    url = "https://example.org/paper?title=a%26b"
    assert normalize_ref(url) == "url:" + url
