"""Shared fixtures for tex-mcp tests. Synthetic tex projects only — no network."""

import os
import tempfile
from pathlib import Path

# Redirect the server cache before tex_mcp.server is imported anywhere.
os.environ.setdefault("TEX_MCP_CACHE_DIR", tempfile.mkdtemp(prefix="tex-mcp-test-"))

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def single() -> str:
    return str(FIXTURES / "single")


@pytest.fixture
def multifile() -> str:
    return str(FIXTURES / "multifile")


@pytest.fixture
def bibref() -> str:
    return str(FIXTURES / "bibref")


@pytest.fixture
def multimain() -> str:
    return str(FIXTURES / "multimain")
