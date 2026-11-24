"""Thin MCP API; all state and behavior are testable through Service."""

import threading
from typing import Literal

from fastmcp import FastMCP

from . import assets
from .models import (
    Budget,
    CachePolicy,
    PaperFilters,
    PaperLookup,
    PaperQuery,
    PublicationYearRange,
    Source,
)
from .service import Service

mcp = FastMCP("paper-search")
_service: Service | None = None
_lock = threading.Lock()


def service():
    global _service
    with _lock:
        if _service is None:
            _service = Service()
        return _service


@mcp.tool()
def get_capabilities() -> dict:
    """Inspect enabled sources, supported operations/conditions and configuration gaps. No keys."""
    return service().get_capabilities()


@mcp.tool()
def resolve_papers(
    inputs: list[PaperLookup], sources: list[Source] | None = None, budget: Budget | None = None
) -> dict:
    """Resolve external identifiers or bibliographic hints. Title hits remain unconfirmed candidates."""
    return service().resolve_papers(inputs, sources, budget)


@mcp.tool()
def get_papers(
    paper_refs: list[str],
    fields: list[str] | None = None,
    view: Literal["normalized", "sources", "versions"] = "normalized",
    cache: CachePolicy = "prefer",
    budget: Budget | None = None,
) -> dict:
    """Fetch stable paper refs in batches, with field provenance, raw-source or observed-version views."""
    return service().get_papers(paper_refs, fields, view, cache, budget)


@mcp.tool()
def search_papers(
    queries: list[PaperQuery],
    filters: PaperFilters | None = None,
    sort: Literal["relevance", "date_desc", "date_asc", "citations_desc"] = "relevance",
    budget: Budget | None = None,
    cache: CachePolicy = "prefer",
) -> dict:
    """Search multiple explicit expressions. Returns a frozen query snapshot and per-source coverage."""
    return service().search_papers(queries, filters, sort, budget, cache)


@mcp.tool()
def get_paper_citations(
    paper_ref: str,
    sources: list[Source] | None = None,
    filters: PaperFilters | None = None,
    budget: Budget | None = None,
    cache: CachePolicy = "prefer",
    publication_year_range: PublicationYearRange | None = None,
) -> dict:
    """Find citing papers; optionally post-filter retrieved candidates by publication year."""
    return service().relation(
        paper_ref, "citations", sources, filters, budget, cache, publication_year_range
    )


@mcp.tool()
def get_paper_references(
    paper_ref: str,
    sources: list[Source] | None = None,
    budget: Budget | None = None,
    cache: CachePolicy = "prefer",
) -> dict:
    """Find cited works; missing indexing, failed retrieval and a verified empty list are distinct."""
    return service().relation(paper_ref, "references", sources, None, budget, cache)


@mcp.tool()
def find_related_papers(
    paper_refs: list[str],
    method: Literal["shared_references", "shared_citations", "provider_recommendations"],
    match: Literal["all", "any"] = "all",
    sources: list[Source] | None = None,
    budget: Budget | None = None,
) -> dict:
    """Find related works with explicit relation evidence and coverage limits, not novelty judgments."""
    return service().find_related_papers(paper_refs, method, match, sources, budget)


@mcp.tool()
def search_authors(
    name: str,
    affiliation: str | None = None,
    topic: str | None = None,
    sources: list[Source] | None = None,
    budget: Budget | None = None,
) -> dict:
    """Find author entities with stable IDs; affiliation/topic are hints, not guaranteed filters."""
    return service().search_entities(name, "author", sources, affiliation, topic, budget=budget)


@mcp.tool()
def search_institutions(
    name: str,
    country: str | None = None,
    sources: list[Source] | None = None,
    budget: Budget | None = None,
) -> dict:
    """Find institution candidates; never silently select the first similarly named organization."""
    return service().search_entities(name, "institution", sources, country=country, budget=budget)


@mcp.tool()
def get_entity_papers(
    entity_ref: str,
    filters: PaperFilters | None = None,
    sort: Literal["relevance", "date_desc", "date_asc", "citations_desc"] = "relevance",
    budget: Budget | None = None,
    cache: CachePolicy = "prefer",
) -> dict:
    """List papers for a confirmed author/institution entity ID; report actual indexing scope."""
    return service().get_entity_papers(entity_ref, filters, sort, budget, cache)


@mcp.tool()
def get_query_results(
    query_id: str | None = None,
    cursor: str | None = None,
    page_size: int = 20,
    fields: list[str] | None = None,
    snapshot_id: str | None = None,
) -> dict:
    """Read local pages. Supply a snapshot_id for an exact snapshot, or a query_id for a query."""
    return service().get_query_results(query_id, cursor, page_size, fields, snapshot_id)


@mcp.tool()
def extend_query(
    query_id: str,
    action: Literal["fetch_more", "retry_failed", "add_queries", "refresh"],
    queries: list[PaperQuery] | None = None,
    sources: list[Source] | None = None,
    budget: Budget | None = None,
) -> dict:
    """Fetch upstream pages, retry failures, add search expressions or refresh into a new snapshot."""
    return service().extend_query(query_id, action, queries, sources, budget)


@mcp.tool()
def list_paper_assets(
    paper_ref: str,
    version: str | None = None,
    cache: CachePolicy = "prefer",
    budget: Budget | None = None,
) -> dict:
    """Discover provider-linked landing/PDF/source resources and distinguish discovery from validation."""
    return assets.list_assets(service(), paper_ref, version, cache, budget)


@mcp.tool()
def download_paper_asset(
    paper_ref: str,
    asset_ref: str | None = None,
    asset_type: Literal["pdf", "source"] = "pdf",
    version: str | None = None,
    cache: CachePolicy = "prefer",
    budget: Budget | None = None,
) -> dict:
    """Download discovered assets with byte/time bounds, format validation, checksum and safe caching."""
    return assets.download(service(), paper_ref, asset_ref, asset_type, version, cache, budget)


@mcp.tool()
def export_records(
    query_id: str | None = None,
    paper_refs: list[str] | None = None,
    format: Literal["json", "bibtex", "markdown"] = "json",
    fields: list[str] | None = None,
    snapshot_id: str | None = None,
) -> dict:
    """Export records in an exact snapshot, a query's latest snapshot, or explicit paper refs."""
    return service().export_records(query_id, paper_refs, format, fields, snapshot_id)
