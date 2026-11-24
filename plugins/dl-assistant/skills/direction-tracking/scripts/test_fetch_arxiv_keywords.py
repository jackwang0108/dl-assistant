# /// script
# requires-python = ">=3.9"
# dependencies = ["arxiv>=2.1", "pytest>=8.0"]
# ///
"""Offline regression checks. Run with uv run test_fetch_arxiv_keywords.py."""
import json
import sys
from datetime import datetime
from types import SimpleNamespace

import pytest
import fetch_arxiv_keywords as mod


@pytest.mark.parametrize("value", ["2026-7-01", "2026-02-30", "2026-07-01junk"])
def test_invalid_dates(value):
    with pytest.raises(ValueError):
        mod.resolve_date(value)


def test_query_or_and_inclusive_utc_dates():
    assert mod.build_query(['"object detection"', ' vision '], "2026-07-01", "2026-07-02") == (
        '(all:"object detection" OR all:"vision") AND submittedDate:[202607010000 TO 202607022359]'
    )


def test_reversed_query_dates():
    with pytest.raises(ValueError):
        mod.build_query(["vision"], "2026-07-02", "2026-07-01")


def test_empty_keywords():
    with pytest.raises(ValueError):
        mod.build_query(['"', ' '], "2026-07-01", "2026-07-01")


def run_main(monkeypatch, capsys, extra_args, papers, raw_count=None):
    monkeypatch.setattr(sys, "argv", ["fetch", "--keywords", "vision", "--from", "2026-07-01", "--to", "2026-07-02", *extra_args])
    calls = []

    def fake_fetch(*args):
        calls.append(args)
        return papers, len(papers) if raw_count is None else raw_count

    monkeypatch.setattr(mod, "fetch", fake_fetch)
    mod.main()
    return json.loads(capsys.readouterr().out), calls


def test_empty_response_keeps_dates_and_query_metadata(monkeypatch, capsys):
    result, calls = run_main(monkeypatch, capsys, [], [])
    assert calls == [(["vision"], "2026-07-01", "2026-07-02", 200)]
    assert result["date_from"] == "2026-07-01"
    assert result["date_to"] == "2026-07-02"
    assert result["date_basis"] == "submittedDate"
    assert result["timezone"] == "UTC"
    assert datetime.fromisoformat(result["fetched_at"]).tzinfo is not None
    assert result["total_count"] == 0
    assert result["truncated"] is False


def test_cap_reports_unconfirmed_completeness(monkeypatch, capsys):
    result, _ = run_main(monkeypatch, capsys, ["--max", "1"], [{"id": "2607.00001"}])
    assert result["truncated"] is True


def test_cap_uses_count_before_deduplication(monkeypatch, capsys):
    result, _ = run_main(monkeypatch, capsys, ["--max", "2"], [{"id": "2607.00001"}], raw_count=2)
    assert result["total_count"] == 1
    assert result["raw_count"] == result["max_results"] == 2
    assert result["truncated"] is True


@pytest.mark.parametrize("extra", [["--max", "0"], ["--max", "-1"], ["--to", "2026-06-30"]])
def test_bad_arguments_do_not_query(monkeypatch, capsys, extra):
    def forbidden_fetch(*args):
        pytest.fail("Invalid parameters must not trigger a query")

    monkeypatch.setattr(mod, "fetch", forbidden_fetch)
    monkeypatch.setattr(sys, "argv", ["fetch", "--keywords", "vision", "--from", "2026-07-01", "--to", "2026-07-02", *extra])
    with pytest.raises(SystemExit) as exc:
        mod.main()
    assert exc.value.code != 0


def test_fetch_keeps_latest_version_metadata_and_dedups(monkeypatch):
    paper = SimpleNamespace(
        entry_id="https://arxiv.org/abs/2607.00001v2", title="Example", authors=[],
        summary="Abstract", categories=["cs.CV"], primary_category="cs.CV",
        comment=None, journal_ref=None, pdf_url="https://arxiv.org/pdf/2607.00001v2",
        published=None, updated=None,
    )
    queries = []

    class Client:
        def __init__(self, **kwargs):
            pass

        def results(self, search):
            queries.append(search.query)
            return iter([paper, paper])

    monkeypatch.setattr(mod.arxiv, "Client", Client)
    result, raw_count = mod.fetch(["vision"], "2026-07-01", "2026-07-02", 200)
    assert len(queries) == 1
    assert raw_count == 2
    assert len(result) == 1
    assert result[0]["id"] == "2607.00001"
    assert result[0]["version_id"] == "2607.00001v2"


def test_dedup_preserves_legacy_archive_and_latest_numbered_version():
    def legacy(version):
        return mod.paper_to_dict(SimpleNamespace(
            entry_id=f"https://arxiv.org/abs/hep-th/9901001v{version}",
            title="Example", authors=[], summary="Abstract", categories=["hep-th"],
            primary_category="hep-th", comment=None, journal_ref=None,
            pdf_url=f"https://arxiv.org/pdf/hep-th/9901001v{version}", published=None, updated=None,
        ))

    result = mod.dedup([legacy(2), legacy(10), legacy(3)])
    assert len(result) == 1
    assert result[0]["id"] == "hep-th/9901001"
    assert result[0]["version_id"] == "hep-th/9901001v10"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q", "-p", "no:cacheprovider"]))
