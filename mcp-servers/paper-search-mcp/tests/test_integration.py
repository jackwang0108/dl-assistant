"""Real orchestration, SQLite and HTTP adapters; upstream bytes are controlled."""

import json
from pathlib import Path

import httpx
import pymupdf
import pytest

from paper_search_mcp import assets
from paper_search_mcp.models import Budget, PaperLookup, PaperQuery
from paper_search_mcp.providers import arxiv_records, oa_record, scholar_record, ss_record
from paper_search_mcp.service import Service
from conftest import ATOM, OA_PAPER, SCHOLAR_PAPER, SS_PAPER


def query(source="semantic_scholar"):
    return [PaperQuery(text="attention", sources=[source])]


def test_source_merge_cache_and_restart(make_service):
    calls = []

    def handler(req):
        calls.append(req)
        if req.url.host == "export.arxiv.org":
            return httpx.Response(200, text=ATOM)
        return httpx.Response(200, json={"data": [SS_PAPER]})

    s = make_service(handler)
    result = s.search_papers([PaperQuery(text="attention", sources=["arxiv", "semantic_scholar"])])
    assert len(result["items"]) == 1 and len(result["items"][0]["authors"]) == 2 and len(calls) == 2
    again = s.search_papers([PaperQuery(text="attention", sources=["arxiv", "semantic_scholar"])])
    assert again["snapshot_id"] == result["snapshot_id"] and len(calls) == 2
    assert (
        Service(s.config, s.providers.http).get_query_results(result["snapshot_id"])["items"]
        == result["items"]
    )


def test_pages_continue_upstream_and_cursor_is_frozen(make_service):
    calls = []

    def handler(req):
        offset = int(req.url.params.get("offset", 0))
        calls.append(offset)
        records = [
            {
                **SS_PAPER,
                "paperId": f"s{offset + i}",
                "externalIds": {"DOI": f"10.1234/p{offset + i}"},
            }
            for i in range(2)
        ]
        return httpx.Response(
            200, json={"data": records, "next": offset + 2 if offset == 0 else None}
        )

    s = make_service(handler)
    first = s.search_papers(query(), budget=Budget(max_items=2))
    page = s.get_query_results(first["snapshot_id"], page_size=1)
    extended = s.extend_query(first["query_id"], "fetch_more", budget=Budget(max_items=2))
    assert calls == [0, 2] and len(extended["items"]) == 4
    old = s.get_query_results(first["query_id"], cursor=page["next_cursor"], page_size=1)
    assert old["snapshot_id"] == first["snapshot_id"]
    assert old["items"][0]["paper_ref"] == first["items"][1]["paper_ref"]
    assert (
        s.get_query_results(
            snapshot_id=first["snapshot_id"], cursor=page["next_cursor"], page_size=1
        )
        == old
    )
    assert len(s.get_query_results(first["snapshot_id"])["items"]) == 2
    original = s.get_query_results(snapshot_id=first["snapshot_id"])
    assert [r["offset_before"] for r in original["retrieval_history"][0]["attempts"]] == [None]
    history = extended["retrieval_history"][0]
    assert history["task_id"] == original["source_reports"][0]["task_id"]
    assert [r["offset_before"] for r in history["attempts"]] == [None, 2]
    with pytest.raises(ValueError, match="cursor"):
        s.get_query_results(snapshot_id=extended["snapshot_id"], cursor=page["next_cursor"])
    with pytest.raises(ValueError, match="Unknown"):
        s.get_query_results(snapshot_id=first["query_id"])
    assert calls == [0, 2]


def test_partial_failure_retries_only_failed_source(make_service):
    calls = {"ss": 0, "gs": 0}

    def handler(req):
        if req.url.host == "serpapi.com":
            calls["gs"] += 1
            if calls["gs"] == 1:
                return httpx.Response(403, json={"error": "denied"})
            return httpx.Response(200, json={"organic_results": [SCHOLAR_PAPER]})
        calls["ss"] += 1
        return httpx.Response(200, json={"data": [SS_PAPER]})

    s = make_service(handler)
    first = s.search_papers([PaperQuery(text="x", sources=["semantic_scholar", "scholar"])])
    assert [r["status"] for r in first["source_reports"]] == ["ok", "failed"]
    second = s.extend_query(first["query_id"], "retry_failed")
    assert calls == {"ss": 1, "gs": 2} and all(
        r["status"] == "ok" for r in second["source_reports"]
    )
    assert s.get_query_results(first["snapshot_id"])["source_reports"][1]["status"] == "failed"
    assert [r["status"] for r in second["retrieval_history"][1]["attempts"]] == ["failed", "ok"]
    assert len(second["retrieval_history"][0]["attempts"]) == 1


def test_add_queries_and_refresh_preserve_old_snapshot(make_service):
    def handler(req):
        term = req.url.params.get("query", "x")
        return httpx.Response(
            200,
            json={
                "data": [{**SS_PAPER, "paperId": term, "externalIds": {"DOI": "10.1234/" + term}}]
            },
        )

    s = make_service(handler)
    first = s.search_papers(query())
    added = s.extend_query(
        first["query_id"],
        "add_queries",
        queries=[PaperQuery(text="other", sources=["semantic_scholar"])],
    )
    assert len(added["items"]) == 2 and len(added["changes"]["newly_matched"]) == 1
    refreshed = s.extend_query(added["query_id"], "refresh")
    assert len(refreshed["items"]) == 2
    assert [h["task_id"] for h in refreshed["retrieval_history"]] == ["task-1", "task-2"]
    assert [len(h["attempts"]) for h in refreshed["retrieval_history"]] == [2, 2]
    assert s.get_query_results(first["snapshot_id"])["items"] == first["items"]


def test_refresh_cache_policy_keeps_existing_query_history(make_service):
    s = make_service(lambda req: httpx.Response(200, json={"data": [SS_PAPER]}))
    first = s.search_papers(query())
    refreshed = s.search_papers(query(), cache="refresh")
    assert refreshed["query_id"] == first["query_id"]
    assert refreshed["snapshot_id"] != first["snapshot_id"]
    assert [a["action"] for a in refreshed["retrieval_history"][0]["attempts"]] == [
        "initial",
        "refresh",
    ]


def test_title_candidate_not_bound_as_exact_identity(make_service):
    s = make_service(lambda req: httpx.Response(200, json={"data": [SS_PAPER]}))
    r = s.resolve_papers([PaperLookup(title="Unrelated Title")], sources=["semantic_scholar"])[
        "results"
    ][0]
    assert (
        r["status"] == "ambiguous"
        and not r["candidates"][0]["match_evidence"]["title_exact_normalized"]
    )
    assert s.store.paper("s2:unrelated") is None


def test_exact_resolution_rejects_wrong_provider_id(make_service):
    s = make_service(lambda req: httpx.Response(200, json=SS_PAPER))
    r = s.resolve_papers(
        [PaperLookup(identifier="doi:10.1234/wrong")], sources=["semantic_scholar"]
    )
    assert r["results"][0]["status"] == "not_found" and s.store.paper("doi:10.1234/wrong") is None


def test_citation_id_and_per_edge_source(make_service):
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(200, json={"organic_results": [SCHOLAR_PAPER]})

    s = make_service(handler)
    s.store.save_record(scholar_record(SCHOLAR_PAPER))
    r = s.relation("scholar:result1", "citations", sources=["scholar"])
    assert calls[0].url.params["cites"] == "12345"
    assert r["items"][0]["relation_evidence"][0]["source"] == "scholar"


def test_shared_references_recomputed_after_extension(make_service):
    def handler(req):
        seed = req.url.path.split("/")[-2]
        offset = int(req.url.params.get("offset", 0))
        name = "common" if seed == "one" or offset else "other"
        paper = {**SS_PAPER, "paperId": name, "externalIds": {"DOI": "10.1234/" + name}}
        return httpx.Response(
            200,
            json={"data": [{"citedPaper": paper}], "next": None if seed == "one" or offset else 1},
        )

    s = make_service(handler)
    first = s.find_related_papers(
        ["s2:one", "s2:two"],
        "shared_references",
        sources=["semantic_scholar"],
        budget=Budget(max_items=2),
    )
    assert first["items"] == []
    second = s.extend_query(first["query_id"], "fetch_more", budget=Budget(max_items=2))
    assert len(second["items"]) == 1
    assert {e["seed_ref"] for e in second["items"][0]["relation_evidence"]} == {"s2:one", "s2:two"}


def test_cache_only_and_export_missing(make_service):
    def unexpected(req):
        raise AssertionError("No network allowed")

    s = make_service(unexpected)
    assert s.search_papers(query(), cache="only")["status"] == "cache_miss"
    assert s.get_papers(["s2:missing"], cache="only")["results"][0]["paper"] is None
    assert s.export_records(paper_refs=["s2:missing"])["missing"]


def test_budget_stops_other_sources(make_service):
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(200, json={"data": [SS_PAPER]})

    s = make_service(handler)
    r = s.search_papers(
        [
            PaperQuery(text="x", sources=["semantic_scholar"]),
            PaperQuery(text="y", sources=["semantic_scholar"]),
        ],
        budget=Budget(max_requests=1),
    )
    assert len(calls) == 1 and r["source_reports"][1]["error"]["kind"] == "budget"


def pdf_bytes():
    doc = pymupdf.open()
    doc.new_page()
    data = doc.tobytes()
    doc.close()
    return data


def test_download_html_fallback_and_corrupt_cache(make_service):
    pdf = pdf_bytes()
    calls = []

    def handler(req):
        calls.append(str(req.url))
        return httpx.Response(
            200, content=pdf if str(req.url).endswith("/good.pdf") else b"<html>blocked</html>"
        )

    s = make_service(handler)
    r = ss_record(SS_PAPER)
    r["assets"] = [
        {"url": "https://papers.test/" + n + ".pdf", "type": "pdf", "source": "semantic_scholar"}
        for n in ["bad", "good"]
    ]
    s.store.save_record(r)
    result = assets.download(s, "s2:s1")
    assert (
        result["status"] == "downloaded"
        and len(result["attempts"]) == 1
        and result["validation"]["pages"] == 1
    )
    assert (
        assets.download(s, "s2:s1", asset_ref=result["asset_ref"])["status"] == "cached"
        and len(calls) == 2
    )
    Path(result["path"]).write_text("corrupt")
    assert (
        assets.download(s, "s2:s1", asset_ref=result["asset_ref"])["status"] == "downloaded"
        and len(calls) == 3
    )


def test_download_byte_budget_no_partial_cache(make_service):
    s = make_service(lambda req: httpx.Response(200, content=b"X" * 500))
    s.store.save_record(ss_record(SS_PAPER))
    r = assets.download(s, "s2:s1", budget=Budget(max_download_bytes=100))
    assert r["status"] == "unavailable" and r["attempts"][0]["error"]["kind"] == "budget"
    assert list((s.store.directory / "assets").iterdir()) == []


def test_download_redirect_counted_and_unknown_asset(make_service):
    pdf = pdf_bytes()
    calls = []

    def handler(req):
        calls.append(req)
        if req.url.path == "/paper.pdf":
            return httpx.Response(302, headers={"location": "/final.pdf"})
        return httpx.Response(200, content=pdf)

    s = make_service(handler)
    s.store.save_record(ss_record(SS_PAPER))
    assert (
        assets.download(s, "s2:s1", asset_ref="invented")["status"] == "unavailable" and not calls
    )
    r = assets.download(s, "s2:s1")
    assert r["status"] == "downloaded" and r["usage"]["requests"] == 2


def test_old_version_never_returns_new_one(make_service):
    s = make_service(lambda req: httpx.Response(200, text=ATOM))
    s.store.save_record(arxiv_records(ATOM.replace("v1", "v2"))[0][0])
    assert (
        s.get_papers(["arxiv:1706.03762v1"], cache="refresh")["results"][0]["paper"]["version"]
        == "v1"
    )
    listed = assets.list_assets(s, "arxiv:1706.03762", version="v1", cache="only")
    assert listed["assets"] and all(a["version"] == "v1" for a in listed["assets"])


def test_export_and_refresh_use_exact_arxiv_revision(make_service):
    def handler(req):
        assert req.url.params["id_list"] == "1706.03762v1"
        return httpx.Response(200, text=ATOM)

    s = make_service(handler)
    old, _ = arxiv_records(ATOM)
    old[0]["fetched_at"] = "2000-01-01T00:00:00+00:00"
    new, _ = arxiv_records(ATOM.replace("v1</id>", "v2</id>").replace("arXiv full abstract", "v2"))
    s.store.save_record(old[0])
    s.store.save_record(new[0])
    refs = ["https://arxiv.org/pdf/1706.03762v1.pdf", "arxiv:1706.03762v2", "arxiv:1706.03762v3"]
    data = json.loads(s.export_records(paper_refs=refs, fields=["abstract"])["content"])
    assert [(p["version"], p["abstract"]) for p in data["records"]] == [
        ("v1", "arXiv full abstract"),
        ("v2", "v2"),
    ]
    assert data["missing"] == [{"paper_ref": refs[2], "reason": "version_not_in_cache"}]
    refreshed = s.get_papers([refs[0]], view="versions")
    assert refreshed["usage"]["requests"] == 1
    assert refreshed["results"][0]["requested_ref"] == "arxiv:1706.03762v1"
    assert {v["version"] for v in refreshed["results"][0]["paper"]["versions"]} == {"v1"}
    assert s.get_papers([refs[0]])["usage"]["requests"] == 0


@pytest.mark.parametrize("page_size", [0, -1, 201])
def test_invalid_page_size_before_io(make_service, page_size):
    s = make_service(lambda req: httpx.Response(200, json={"data": []}))
    with pytest.raises(ValueError):
        s.get_query_results("anything", page_size=page_size)


def test_export_bibtex_and_source_provenance(make_service):
    s = make_service(lambda req: httpx.Response(200, json={}))
    s.store.save_record(ss_record(SS_PAPER))
    assert (
        "John Smith and Jane Smith"
        in s.export_records(paper_refs=["s2:s1"], format="bibtex")["content"]
    )
    raw = json.loads(s.export_records(paper_refs=["s2:s1"])["content"])
    assert raw["records"][0]["field_provenance"]["abstract"]["source"] == "semantic_scholar"


def test_url_resolves_via_provider_endpoint_not_title(make_service):
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(200, json=SS_PAPER)

    s = make_service(handler)
    url = "https://openreview.net/forum?id=abc"
    r = s.resolve_papers([PaperLookup(identifier=url)], sources=["semantic_scholar"])
    assert r["results"][0]["status"] == "confirmed"
    assert "/paper/URL:https://openreview.net/forum?id=abc" in calls[0].url.path
    assert s.store.paper("url:" + url)["title"] == SS_PAPER["title"]


def test_exact_revision_resolution_cannot_use_different_revision(make_service):
    s = make_service(lambda req: httpx.Response(200, text=ATOM.replace("v1", "v2")))
    r = s.resolve_papers([PaperLookup(identifier="arxiv:1706.03762v1")], sources=["arxiv"])
    assert r["results"][0]["status"] == "not_found"


def test_metadata_batch_isolates_invalid_ref_and_budget(make_service):
    s = make_service(lambda req: httpx.Response(200, json=SS_PAPER))
    r = s.get_papers(
        ["bad-id", "s2:s1", "doi:10.1234/other"],
        cache="refresh",
        budget=Budget(max_requests=1, max_items=1),
    )
    assert r["results"][0]["status"] == "invalid"
    assert r["results"][1]["status"] == "ok"
    assert r["usage"]["requests"] == 1 and r["usage"]["items"] == 1
    assert r["results"][2]["source_reports"][0]["error"]["kind"] == "budget"


def test_download_discovery_and_payload_share_request_budget(make_service):
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(200, json=SS_PAPER)

    s = make_service(handler)
    r = assets.download(s, "s2:s1", budget=Budget(max_requests=1))
    assert r["status"] == "unavailable" and r["usage"]["requests"] == 1 and len(calls) == 1
    assert r["attempts"][0]["error"]["kind"] == "budget"


def test_cursor_rejects_other_query_and_bad_snapshot_type(make_service):
    import base64

    s = make_service(lambda req: httpx.Response(200, json={"data": [SS_PAPER]}))
    a = s.search_papers([PaperQuery(text="a", sources=["semantic_scholar"])])
    b = s.search_papers([PaperQuery(text="b", sources=["semantic_scholar"])])
    for value in [[b["snapshot_id"], 0], [[], 0]]:
        cursor = base64.urlsafe_b64encode(json.dumps(value).encode()).decode()
        with pytest.raises(ValueError):
            s.get_query_results(a["query_id"], cursor=cursor)


def test_not_indexed_and_unknown_citation_endpoints_are_distinct(make_service):
    s = make_service(lambda req: httpx.Response(404))
    assert (
        s.resolve_papers([PaperLookup(identifier="s2:absent")], sources=["semantic_scholar"])[
            "results"
        ][0]["status"]
        == "not_found"
    )
    other = make_service(lambda req: httpx.Response(200, json={"data": [{"citedPaper": None}]}))
    result = other.relation("s2:s1", "references", sources=["semantic_scholar"])
    assert result["source_reports"][0]["status"] == "partial"
    assert "unavailable" in result["source_reports"][0]["limitations"][0]


@pytest.mark.parametrize(
    ("response", "status", "resolution"),
    [
        (404, "not_found", "not_indexed"),
        (403, "failed", "failed"),
        (200, "failed", "failed"),  # returned a different DOI
    ],
)
def test_openalex_doi_lookup_failure_never_fetches_relationship(
    make_service, response, status, resolution
):
    def handler(req):
        assert req.url.path.startswith("/works/https://doi.org/")
        return httpx.Response(response, json=OA_PAPER)

    s = make_service(handler)
    result = s.relation("doi:10.1234/other", "citations", sources=["openalex"])
    report = result["source_reports"][0]
    assert (report["status"], report["identifier_resolution"]["status"]) == (status, resolution)
    assert result["usage"]["requests"] == 1 and not result["items"]
    unsupported = s.relation("arxiv:1706.03762", "citations", sources=["openalex"])
    assert (
        unsupported["source_reports"][0]["identifier_resolution"]["status"] == "missing_identifier"
    )
    assert unsupported["usage"]["requests"] == 0


def test_openalex_doi_lookup_shares_budget_and_reuses_verified_id(make_service):
    def handler(req):
        if req.url.path == "/works":
            assert req.url.params["filter"] == "cited_by:W1"
            return httpx.Response(200, json={"results": []})
        assert req.url.path == "/works/https://doi.org/10.1234/attention"
        return httpx.Response(200, json=OA_PAPER)

    s = make_service(handler)
    first = s.relation(
        "doi:10.1234/attention", "references", sources=["openalex"], budget=Budget(max_requests=1)
    )
    report = first["source_reports"][0]
    assert report["error"]["kind"] == "budget"
    assert report["identifier_resolution"] == {
        "status": "resolved",
        "lookup_ref": "doi:10.1234/attention",
        "identifier": "openalex:W1",
    }
    resumed = s.extend_query(first["query_id"], "retry_failed", budget=Budget(max_requests=1))
    assert resumed["source_reports"][0]["status"] == "ok"
    assert [r["requests"] for r in resumed["retrieval_history"][0]["attempts"]] == [1, 1]
    assert resumed["coverage"]["upstream_has_more"] is False
    cached = s.relation("doi:10.1234/attention", "references", sources=["openalex"], cache="only")
    assert cached["snapshot_id"] == resumed["snapshot_id"]


def test_citation_year_postfilter_freezes_evidence_and_upstream_coverage(make_service):
    def citing(n, year):
        return {
            "citingPaper": {
                "paperId": f"c{n}",
                "externalIds": {"DOI": f"10.1234/c{n}"},
                "year": year,
            }
        }

    def handler(req):
        assert "year" not in req.url.params
        assert req.url.path.endswith("/citations")
        if req.url.params["offset"] == "0":
            return httpx.Response(
                200,
                json={
                    "data": [citing(1, 2025), citing(2, 2023), citing(3, None), citing(4, 2025)],
                    "next": 4,
                },
            )
        return httpx.Response(200, json={"data": [citing(5, 2026)]})

    s = make_service(handler)
    s.store.save_record(
        oa_record({**OA_PAPER, "doi": "https://doi.org/10.1234/c4", "publication_year": 2024})
    )
    first = s.relation(
        "s2:seed",
        "citations",
        sources=["semantic_scholar"],
        publication_year_range={"start": 2025, "end": 2026},
    )
    counts = first["year_filter"]
    assert (counts["retrieved_count"], counts["matched_count"], counts["outside_count"]) == (
        4,
        1,
        1,
    )
    assert [(u["paper_ref"], u["reason"]) for u in counts["unknown_items"]] == [
        ("doi:10.1234/c3", "missing_publication_year"),
        ("doi:10.1234/c4", "conflicting_publication_years"),
    ]
    assert first["items"][0]["publication_year_evidence"]["year"] == 2025
    assert first["coverage"]["upstream_has_more"] is True
    more = s.extend_query(first["query_id"], "fetch_more")
    assert more["year_filter"]["matched_count"] == 2
    assert more["coverage"]["upstream_has_more"] is False
    exported = json.loads(s.export_records(snapshot_id=first["snapshot_id"])["content"])
    assert exported["year_filter"] == counts
    assert exported["coverage"]["upstream_has_more"] is True


def test_snapshot_export_includes_all_local_pages(make_service):
    def handler(req):
        start = int(req.url.params.get("offset", 0))
        return httpx.Response(
            200,
            json={
                "data": [{"paperId": f"record-{i}"} for i in range(start, start + 20)],
                "next": start + 20,
            },
        )

    s = make_service(handler)
    first = s.search_papers(query())
    second = s.extend_query(first["query_id"], "fetch_more")
    assert len(second["items"]) == 20 and second["next_cursor"]
    current = s.export_records(query_id=first["query_id"])
    assert current["count"] == 40 and current["snapshot_id"] == second["snapshot_id"]
    assert current["coverage"]["export_scope"] == "all_local_matching_records"
    assert not current["coverage"]["local_has_more"] and current["coverage"]["upstream_has_more"]
    frozen = s.export_records(snapshot_id=first["snapshot_id"])
    assert frozen["count"] == 20


def test_source_archive_validated_without_extraction(make_service):
    import io
    import tarfile

    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        content = b"\\documentclass{article}"
        member = tarfile.TarInfo("paper.tex")
        member.size = len(content)
        archive.addfile(member, io.BytesIO(content))
    s = make_service(lambda req: httpx.Response(200, content=buffer.getvalue()))
    s.store.save_record(arxiv_records(ATOM)[0][0])
    result = assets.download(s, "arxiv:1706.03762", asset_type="source", version="v1")
    assert result["status"] == "downloaded"
    assert result["validation"] == {"archive": "tar", "extracted": False}
    assert not (s.store.directory / "paper.tex").exists()


def test_empty_success_unavailable_and_disabled_are_distinct(make_service):
    s = make_service(lambda req: httpx.Response(200, json={"data": []}))
    s.config.keys["scholar"] = ""
    s.providers.keys["scholar"] = ""
    result = s.search_papers([PaperQuery(text="x", sources=["semantic_scholar", "scholar"])])
    assert result["items"] == []
    assert [r["status"] for r in result["source_reports"]] == ["ok", "disabled"]
    assert result["coverage"]["upstream_has_more"] is None


def test_entity_fields_selection_keeps_stable_identity(make_service):
    s = make_service(
        lambda req: httpx.Response(200, json={"data": [{"authorId": "a1", "name": "John Smith"}]})
    )
    first = s.search_entities("John Smith", "author", sources=["semantic_scholar"])
    selected = s.get_query_results(first["snapshot_id"], fields=["name"])
    assert selected["items"][0]["entity_ref"] == "s2:author:a1"
