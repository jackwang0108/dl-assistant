"""Opt-in real APIs using isolated caches and small explicitly bounded requests."""

import os

import pytest

from paper_search_mcp.config import Config
from paper_search_mcp.models import Budget, PaperQuery
from paper_search_mcp.service import Service

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.getenv("RUN_LIVE_TESTS") != "1", reason="Set RUN_LIVE_TESTS=1"),
]


@pytest.fixture
def live(tmp_path):
    config = Config.from_env()
    config.cache_dir = tmp_path
    return Service(config)


@pytest.mark.parametrize("source", ["arxiv", "semantic_scholar", "scholar", "openalex"])
def test_real_search(live, source):
    if not live.providers.enabled(source):
        pytest.skip("Source not configured")
    r = live.search_papers(
        [PaperQuery(text='"Attention Is All You Need"', sources=[source])],
        budget=Budget(max_requests=2, max_items=2, max_seconds=35),
        cache="refresh",
    )
    assert r["source_reports"][0]["status"] == "ok", r["source_reports"]
    assert r["items"] and all(p["identifiers"] for p in r["items"])
    if source == "scholar":
        assert any(i.startswith("scholar_cites:") for p in r["items"] for i in p["identifiers"])
        assert r["items"][0].get("snippet") and not r["items"][0].get("abstract")
