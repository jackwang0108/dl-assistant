# /// script
# requires-python = ">=3.9"
# dependencies = ["arxiv>=2.1"]
# ///
"""Fetch arXiv papers matching keyword phrases within a submittedDate window.

Outputs clean JSON to stdout. Designed for the `direction-tracking` skill:
keyword-based incremental fetch (keywords + date window -> matching papers),
NOT category-based. Talks to the arXiv API directly.

Sibling of `arxiv-daily-paper/scripts/fetch_arxiv_daily.py` (category + date).
Same paper-dict shape and dedup; differs only in query construction
(`all:"phrase"` keywords vs `cat:` categories).

The caller (skill / agent) expands synonym groups from `config.yaml` into a
flat keyword list and passes them here -- this script is keyword-blind beyond
OR-joining the phrases.

Key properties:
  * A single OR-query across all keyword phrases
    (`all:"kw1" OR all:"kw2"`) so a paper matching several phrases comes back once.
  * Filters by arXiv *submittedDate* window [from, to] (UTC). For incremental
    tracking the caller uses the source-specific completed range plus overlap as --from.
  * Paginates by submittedDate until exhausted (or --max cap).
  * Carries author-provided comment / journal_ref metadata.

Run (zero setup, deps auto-installed by uv):
    uv run fetch_arxiv_keywords.py --keywords "referring expression segmentation" RES --from 2026-06-01 --to 2026-07-13
    uv run fetch_arxiv_keywords.py --keywords "open vocabulary detection" --from 2026-07-01

Date semantics: filters by arXiv *submittedDate* (UTC). arXiv indexing can lag,
so a paper submitted today may appear a day or two later -- callers may overlap the --from window to reduce omissions. This cannot
guarantee complete coverage; fetching and processing progress are separate.
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
    """Pull a page count out of an arXiv comment ('12 pages, 5 figures')."""
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
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", date_arg):
        raise ValueError("Expected YYYY-MM-DD")
    datetime.strptime(date_arg, "%Y-%m-%d")  # raises ValueError if malformed
    return date_arg


def build_query(keywords: list[str], date_from: str, date_to: str) -> str:
    """Build an arXiv query: (all:"kw1" OR all:"kw2") AND submittedDate:[from TO to]."""
    if date_from > date_to:
        raise ValueError("Start date must not be after end date.")
    # Keywords come from user-editable config.yaml -- strip embedded double
    # quotes so a stray `"` can't break out of the phrase and corrupt the query.
    cleaned = [k.replace('"', "").strip() for k in keywords]
    cleaned = [k for k in cleaned if k]
    if not cleaned:
        raise ValueError("No usable keyword after stripping quotes/whitespace.")
    kw = " OR ".join(f'all:"{k}"' for k in cleaned)
    start = date_from.replace("-", "")
    end = date_to.replace("-", "")
    date_range = f"submittedDate:[{start}0000 TO {end}2359]"
    if len(cleaned) > 1:
        return f"({kw}) AND {date_range}"
    return f"{kw} AND {date_range}"


def paper_to_dict(result: arxiv.Result) -> dict:
    """Normalise an arxiv.Result into a plain dict (same shape as fetch_arxiv_daily)."""
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


def fetch(keywords: list[str], date_from: str, date_to: str, max_results: int) -> list[dict]:
    """Query arXiv and return a de-duplicated list of paper dicts."""
    query = build_query(keywords, date_from, date_to)
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
        description="Fetch arXiv papers matching keywords within a date window as JSON."
    )
    parser.add_argument(
        "--keywords",
        required=True,
        nargs="+",
        help='Keyword phrases, e.g. "referring expression segmentation" RES',
    )
    parser.add_argument(
        "--from",
        required=True,
        dest="date_from",
        help="Start date YYYY-MM-DD, or 'today' / 'yesterday' (UTC).",
    )
    parser.add_argument(
        "--to",
        default="today",
        dest="date_to",
        help="End date YYYY-MM-DD, or 'today' / 'yesterday' (UTC). Default: today.",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=200,
        dest="max_results",
        help="Safety cap on total papers fetched (default 200).",
    )
    args = parser.parse_args()
    if args.max_results <= 0:
        parser.error("--max must be positive")

    try:
        date_from = resolve_date(args.date_from)
        date_to = resolve_date(args.date_to)
        if date_from > date_to:
            raise ValueError("Start date must not be after end date")
    except ValueError:
        print(
            json.dumps(
                {
                    "error": (
                        f"Invalid date. Use YYYY-MM-DD/today/yesterday. "
                        f"from={args.date_from} to={args.date_to}"
                    )
                }
            )
        )
        sys.exit(1)

    try:
        papers = fetch(args.keywords, date_from, date_to, args.max_results)
    except Exception as exc:  # network / API failure — report, don't crash silently
        print(json.dumps({"error": f"arXiv fetch failed: {type(exc).__name__}: {exc}"}))
        sys.exit(1)

    result = {
        "date_basis": "submittedDate",
        "timezone": "UTC",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "keywords": args.keywords,
        "date_from": date_from,
        "date_to": date_to,
        "total_count": len(papers),
        "truncated": len(papers) >= args.max_results,
        "papers": papers,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
