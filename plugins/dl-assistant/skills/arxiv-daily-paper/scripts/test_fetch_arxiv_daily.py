# /// script
# requires-python = ">=3.9"
# dependencies = ["arxiv>=2.1", "pytest>=8.0"]
# ///
"""Tests for fetch_arxiv_daily.py — pure logic, no network.

Run:  uv run test_fetch_arxiv_daily.py        (delegates to pytest)
  or: uv run pytest test_fetch_arxiv_daily.py
"""

from __future__ import annotations

import sys
import types
import json
from datetime import datetime, timezone

import pytest

import fetch_arxiv_daily as mod


# ── extract_pages ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "comment,expected",
    [
        ("12 pages, 5 figures", 12),
        ("Accepted to CVPR 2026. 8 pages", 8),
        ("Project page: https://x.io", None),  # no page count
        (None, None),
        ("", None),
        ("1 page extended abstract", 1),
    ],
)
def test_extract_pages(comment, expected):
    assert mod.extract_pages(comment) == expected


# ── build_query ──────────────────────────────────────────────────────────


def test_build_query_single_category():
    q = mod.build_query(["cs.CV"], "2026-06-29")
    assert "cat:cs.CV" in q
    assert "submittedDate:[202606290000 TO 202606292359]" in q
    # single category: no OR-parenthesis wrapping needed
    assert " OR " not in q


def test_build_query_multi_category_uses_or_and_parens():
    q = mod.build_query(["cs.CV", "cs.LG", "cs.RO"], "2026-06-29")
    # OR across categories so a cross-listed paper returns once
    assert "cat:cs.CV OR cat:cs.LG OR cat:cs.RO" in q
    assert q.startswith("(")
    assert "submittedDate:" in q


# ── dedup (cross-listed papers come back once) ───────────────────────────


def test_dedup_keeps_first_occurrence_by_base_id():
    papers = [
        {"id": "2606.001", "title": "A"},
        {"id": "2606.002", "title": "B"},
        {"id": "2606.001", "title": "A-dup"},  # cross-listed duplicate
    ]
    out = mod.dedup(papers)
    assert [p["id"] for p in out] == ["2606.001", "2606.002"]
    assert out[0]["title"] == "A"  # first occurrence wins


# ── resolve_date ─────────────────────────────────────────────────────────


def test_resolve_date_explicit_passthrough():
    assert mod.resolve_date("2026-06-29") == "2026-06-29"


def test_resolve_date_today_is_iso():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert mod.resolve_date("today") == today


def test_resolve_date_invalid_raises():
    with pytest.raises(ValueError):
        mod.resolve_date("June 29")


# ── paper_to_dict (mock arxiv.Result, strips version, keeps signals) ─────


def _fake_result(**kw):
    """Build a stand-in for arxiv.Result with the attributes we read."""
    author = types.SimpleNamespace(name="Jane Doe")
    defaults = dict(
        entry_id="http://arxiv.org/abs/2606.28322v2",
        title="A Great\nPaper",
        authors=[author],
        summary="We propose\na method.",
        categories=["cs.CV", "cs.LG"],
        primary_category="cs.CV",
        comment="Accepted to ECCV 2026. 14 pages",
        journal_ref=None,
        pdf_url="http://arxiv.org/pdf/2606.28322v2",
        published=datetime(2026, 6, 29, tzinfo=timezone.utc),
        updated=datetime(2026, 6, 30, tzinfo=timezone.utc),
    )
    defaults.update(kw)
    return types.SimpleNamespace(**defaults)


def test_paper_to_dict_strips_version_and_extracts_signals():
    d = mod.paper_to_dict(_fake_result())
    assert d["id"] == "2606.28322"  # version stripped
    assert d["version_id"] == "2606.28322v2"
    assert d["title"] == "A Great Paper"  # newline collapsed
    assert d["comment"] == "Accepted to ECCV 2026. 14 pages"
    assert d["pages"] == 14  # extracted from comment
    assert d["categories"] == ["cs.CV", "cs.LG"]
    assert d["abs_url"] == "https://arxiv.org/abs/2606.28322"


def test_paper_to_dict_handles_missing_comment():
    d = mod.paper_to_dict(_fake_result(comment=None))
    assert d["comment"] is None
    assert d["pages"] is None


def test_paper_to_dict_preserves_legacy_archive_in_versioned_id():
    paper = mod.paper_to_dict(_fake_result(entry_id="http://arxiv.org/abs/hep-th/9901001v2"))
    assert paper["id"] == "hep-th/9901001"
    assert paper["version_id"] == "hep-th/9901001v2"


@pytest.mark.parametrize("value", ["2026-6-29", "2026-02-30", "2026-06-29-extra"])
def test_resolve_date_rejects_invalid_iso_dates(value):
    with pytest.raises(ValueError):
        mod.resolve_date(value)


def test_empty_result_keeps_requested_date_and_records_query_basis(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["fetch", "--date", "2026-06-29", "--categories", "cs.CV"])
    calls = []

    def fake_fetch(categories, date, max_results):
        calls.append((categories, date, max_results))
        return [], 0

    monkeypatch.setattr(mod, "fetch", fake_fetch)
    mod.main()
    result = json.loads(capsys.readouterr().out)
    assert calls == [(["cs.CV"], "2026-06-29", 500)]
    assert result["date"] == "2026-06-29"
    assert result["date_basis"] == "submittedDate"
    assert result["timezone"] == "UTC"
    assert datetime.fromisoformat(result["fetched_at"]).tzinfo is not None
    assert result["total_count"] == 0
    assert result["truncated"] is False


def test_cap_is_checked_before_deduplication(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [
        "fetch", "--date", "2026-06-29", "--categories", "cs.LG", "cs.CV", "cs.CV", "--max", "2",
    ])
    monkeypatch.setattr(mod.arxiv.Client, "results", lambda self, search: iter([_fake_result(), _fake_result()]))
    mod.main()
    result = json.loads(capsys.readouterr().out)
    assert result["categories"] == ["cs.CV", "cs.LG"]
    assert result["total_count"] == 1
    assert result["raw_count"] == result["max_results"] == 2
    assert result["truncated"] is True


def test_nonpositive_cap_is_rejected_before_fetch(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["fetch", "--date", "2026-06-29", "--categories", "cs.CV", "--max", "0"])
    with pytest.raises(SystemExit) as exc:
        mod.main()
    assert exc.value.code == 2


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
