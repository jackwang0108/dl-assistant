# /// script
# requires-python = ">=3.9"
# dependencies = ["arxiv>=2.1"]
# ///
"""Fetch all arXiv papers submitted on a given date for given categories.

Outputs clean JSON to stdout. Designed for the `arxiv-daily-paper` skill:
deterministic batch fetch (date + categories -> full list), NOT semantic
search, so it talks to the arXiv API directly instead of going through
paper-search.

Key properties:
  * A single OR-query across all requested categories
    (`cat:cs.CV OR cat:cs.LG`) so a paper cross-listed in several
    categories comes back once, not once per category.
  * Paginates by submittedDate until the day is exhausted (or --max cap),
    instead of silently truncating at a fixed page size.
  * Carries the `comment` and `journal_ref` fields — arXiv's objective
    quality signals ("Accepted to CVPR 2026", "Code: github.com/...") that
    paper-search drops.

Run (zero setup, deps auto-installed by uv):
    uv run fetch_arxiv_daily.py --date today --categories cs.CV cs.LG
    uv run fetch_arxiv_daily.py --date 2026-06-29 --categories cs.CV --max 400

Date semantics: filters by arXiv *submittedDate* (UTC), which is the
submission timestamp, not the public announcement day. arXiv announces on
weekday schedules, so a date with no results usually means "not announced
yet / weekend / holiday", not an error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone

import arxiv


_PAGES_RE = re.compile(r"(\d+)\s*pages?\b", re.IGNORECASE)


def extract_pages(comment: str | None) -> int | None:
    """Pull a page count out of an arXiv comment (e.g. '12 pages, 5 figures').

    arXiv has no dedicated page field; authors conventionally put it in the
    comment, but not always — returns None when absent.
    """
    if not comment:
        return None
    m = _PAGES_RE.search(comment)
    return int(m.group(1)) if m else None


def resolve_date(date_arg: str) -> str:
    """Resolve 'today'/'yesterday'/YYYY-MM-DD to a YYYY-MM-DD string (UTC)."""
    if date_arg == "today":
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if date_arg == "yesterday":
        return (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    # Validate explicit date
    datetime.strptime(date_arg, "%Y-%m-%d")  # raises ValueError if malformed
    return date_arg


def build_query(categories: list[str], date: str) -> str:
    """Build an arXiv query: (cat:A OR cat:B) AND submittedDate:[day]."""
    cats = " OR ".join(f"cat:{c}" for c in categories)
    stamp = date.replace("-", "")
    date_range = f"submittedDate:[{stamp}0000 TO {stamp}2359]"
    if len(categories) > 1:
        return f"({cats}) AND {date_range}"
    return f"{cats} AND {date_range}"


def paper_to_dict(result: arxiv.Result) -> dict:
    """Normalise an arxiv.Result into a plain dict, keeping quality signals."""
    arxiv_id = result.entry_id.split("/")[-1]  # e.g. 2606.28322v1
    base_id = arxiv_id.split("v")[0]  # strip version for stable key
    comment = (result.comment or "").strip().replace("\n", " ") or None
    return {
        "id": base_id,
        "version_id": arxiv_id,
        "title": result.title.strip().replace("\n", " "),
        "authors": [a.name for a in result.authors],
        "abstract": (result.summary or "").strip().replace("\n", " "),
        "categories": result.categories,
        "primary_category": result.primary_category,
        "comment": comment,
        "pages": extract_pages(comment),
        "journal_ref": (result.journal_ref or "").strip() or None,
        "pdf_url": result.pdf_url,
        "abs_url": f"https://arxiv.org/abs/{base_id}",
        "published": result.published.isoformat() if result.published else None,
        "updated": result.updated.isoformat() if result.updated else None,
    }


def dedup(papers: list[dict]) -> list[dict]:
    """Drop duplicate papers by stable base id, preserving first occurrence."""
    seen: set[str] = set()
    out: list[dict] = []
    for p in papers:
        if p["id"] in seen:
            continue
        seen.add(p["id"])
        out.append(p)
    return out


def fetch(categories: list[str], date: str, max_results: int) -> list[dict]:
    """Query arXiv and return a de-duplicated list of paper dicts."""
    query = build_query(categories, date)
    client = arxiv.Client(page_size=100, delay_seconds=3.0, num_retries=3)
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    papers = [paper_to_dict(r) for r in client.results(search)]
    return dedup(papers)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch arXiv papers for a date + categories as JSON."
    )
    parser.add_argument(
        "--date", required=True, help="YYYY-MM-DD, or 'today' / 'yesterday' (UTC)."
    )
    parser.add_argument(
        "--categories",
        required=True,
        nargs="+",
        help="arXiv category codes, e.g. cs.CV cs.LG",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=500,
        dest="max_results",
        help="Safety cap on total papers fetched (default 500).",
    )
    args = parser.parse_args()

    try:
        date = resolve_date(args.date)
    except ValueError:
        print(
            json.dumps(
                {"error": f"Invalid --date '{args.date}'. Use YYYY-MM-DD/today/yesterday."}
            )
        )
        sys.exit(1)

    try:
        papers = fetch(args.categories, date, args.max_results)
    except Exception as exc:  # network / API failure — report, don't crash silently
        print(json.dumps({"error": f"arXiv fetch failed: {type(exc).__name__}: {exc}"}))
        sys.exit(1)

    result = {
        "date": date,
        "categories": args.categories,
        "total_count": len(papers),
        "truncated": len(papers) >= args.max_results,
        "papers": papers,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
