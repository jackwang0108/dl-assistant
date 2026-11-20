"""Protocol E2E: all public tools, validated inputs and multi-call workflows."""

import httpx
import pymupdf
import pytest
from fastmcp import Client

import paper_search_mcp.server as server
from conftest import ATOM, OA_PAPER, SCHOLAR_PAPER, SS_PAPER

pytestmark = pytest.mark.asyncio


@pytest.fixture
def e2e(make_service, monkeypatch):
    doc = pymupdf.open()
    doc.new_page()
    pdf = doc.tobytes()
    doc.close()

    def handler(req):
        host, path = req.url.host, req.url.path
        if host == "papers.test":
            return httpx.Response(200, content=pdf)
        if host == "export.arxiv.org":
            return httpx.Response(200, text=ATOM)
        if host == "serpapi.com":
            return httpx.Response(200, json={"organic_results": [SCHOLAR_PAPER]})
        if host == "api.openalex.org":
            if path == "/institutions":
                return httpx.Response(
                    200,
                    json={
                        "results": [
                            {
                                "id": "https://openalex.org/I1",
                                "display_name": "Example University",
                                "country_code": "US",
                            }
                        ],
                        "meta": {},
                    },
                )
            if path == "/authors":
                return httpx.Response(
                    200,
                    json={
                        "results": [
                            {"id": "https://openalex.org/A1", "display_name": "John Smith"}
                        ],
                        "meta": {},
                    },
                )
            if path == "/works":
                return httpx.Response(200, json={"results": [OA_PAPER], "meta": {}})
            return httpx.Response(200, json=OA_PAPER)
        if "/recommendations/" in path:
            return httpx.Response(200, json={"recommendedPapers": [SS_PAPER]})
        if path.endswith("/author/search"):
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "authorId": "a1",
                            "name": "John Smith",
                            "affiliations": ["Example University"],
                        }
                    ]
                },
            )
        if path.endswith("/author/a1/papers"):
            return httpx.Response(200, json={"data": [SS_PAPER]})
        if path.endswith("/citations"):
            return httpx.Response(200, json={"data": [{"citingPaper": SS_PAPER}]})
        if path.endswith("/references"):
            return httpx.Response(200, json={"data": [{"citedPaper": SS_PAPER}]})
        if path.endswith("/paper/search"):
            return httpx.Response(200, json={"data": [SS_PAPER]})
        return httpx.Response(200, json=SS_PAPER)

    service = make_service(handler)
    monkeypatch.setattr(server, "_service", service)
    return server.mcp


async def call(client, tool_name, **args):
    result = await client.call_tool(tool_name, args)
    assert not result.is_error
    return result.data


async def test_exact_tool_catalog(e2e):
    expected = {
        "get_capabilities",
        "resolve_papers",
        "get_papers",
        "search_papers",
        "get_paper_citations",
        "get_paper_references",
        "find_related_papers",
        "search_authors",
        "search_institutions",
        "get_entity_papers",
        "get_query_results",
        "extend_query",
        "list_paper_assets",
        "download_paper_asset",
        "export_records",
    }
    async with Client(e2e) as client:
        tools = await client.list_tools()
        assert {t.name for t in tools} == expected
        schema = next(t for t in tools if t.name == "search_papers").inputSchema
        assert schema["properties"]["queries"]["items"]["properties"]["syntax"]["enum"] == [
            "text",
            "source_native",
        ]


async def test_search_resolve_export_download_workflow(e2e):
    async with Client(e2e) as client:
        capabilities = await call(client, "get_capabilities")
        assert capabilities["api_version"] == 2
        resolved = await call(
            client, "resolve_papers", inputs=[{"identifier": "arxiv:1706.03762"}], sources=["arxiv"]
        )
        assert resolved["results"][0]["status"] == "confirmed"
        papers = await call(
            client, "get_papers", paper_refs=["arxiv:1706.03762"], view="sources", cache="only"
        )
        assert papers["results"][0]["paper"]["observations"]
        searched = await call(
            client,
            "search_papers",
            queries=[{"text": "attention", "sources": ["semantic_scholar"]}],
        )
        page = await call(client, "get_query_results", query_id=searched["snapshot_id"])
        assert len(page["items"]) == 1
        added = await call(
            client,
            "extend_query",
            query_id=searched["query_id"],
            action="add_queries",
            queries=[{"text": "other", "sources": ["openalex"]}],
        )
        assert added["snapshot_id"] != searched["snapshot_id"]
        exported = await call(
            client, "export_records", query_id=added["snapshot_id"], format="bibtex"
        )
        assert "@misc{" in exported["content"]
        listed = await call(client, "list_paper_assets", paper_ref="arxiv:1706.03762", cache="only")
        assert any(a["type"] == "pdf" for a in listed["assets"])
        downloaded = await call(client, "download_paper_asset", paper_ref="arxiv:1706.03762")
        assert downloaded["status"] == "downloaded" and downloaded["validation"]["pages"] == 1


@pytest.mark.parametrize("tool", ["get_paper_citations", "get_paper_references"])
async def test_relationship_tools(e2e, tool):
    async with Client(e2e) as client:
        result = await call(client, tool, paper_ref="s2:s1", sources=["semantic_scholar"])
        assert result["items"][0]["relation_evidence"][0]["source"] == "semantic_scholar"


@pytest.mark.parametrize(
    "method", ["shared_references", "shared_citations", "provider_recommendations"]
)
async def test_related_tools(e2e, method):
    async with Client(e2e) as client:
        result = await call(
            client,
            "find_related_papers",
            paper_refs=["s2:s1"],
            method=method,
            sources=["semantic_scholar"],
        )
        assert result["items"]


async def test_entities_then_papers(e2e):
    async with Client(e2e) as client:
        authors = await call(
            client, "search_authors", name="John Smith", sources=["semantic_scholar"]
        )
        assert authors["items"][0]["entity_ref"] == "s2:author:a1"
        result = await call(
            client, "get_entity_papers", entity_ref=authors["items"][0]["entity_ref"]
        )
        assert result["items"]
        institutions = await call(client, "search_institutions", name="Example", country="US")
        result = await call(
            client, "get_entity_papers", entity_ref=institutions["items"][0]["entity_ref"]
        )
        assert result["items"]


@pytest.mark.parametrize(
    "name,args",
    [
        ("search_papers", {"queries": [{"text": "x", "sources": ["not-a-source"]}]}),
        ("search_papers", {"queries": [{"text": "x"}], "budget": {"max_requests": 0}}),
        ("get_papers", {"paper_refs": ["s2:s1"], "cache": "invented"}),
        (
            "search_papers",
            {
                "queries": [{"text": "x"}],
                "filters": {
                    "date_range": {
                        "date_type": "published",
                        "start": "2025-12-31",
                        "end": "2025-01-01",
                    }
                },
            },
        ),
        ("download_paper_asset", {"paper_ref": "s2:s1", "asset_type": "executable"}),
    ],
)
async def test_protocol_rejects_invalid_inputs(e2e, name, args):
    async with Client(e2e) as client:
        result = await client.call_tool(name, args, raise_on_error=False)
        assert result.is_error


async def test_real_stdio_server_process(tmp_path):
    import sys
    from fastmcp.client.transports import StdioTransport

    transport = StdioTransport(
        command=sys.executable,
        args=["-m", "paper_search_mcp"],
        env={
            "PAPER_SEARCH_CACHE_DIR": str(tmp_path),
            "SERPAPI_KEY": "",
            "SEMANTIC_SCHOLAR_API_KEY": "",
            "OPENALEX_API_KEY": "",
            "FASTMCP_SHOW_SERVER_BANNER": "false",
        },
    )
    async with Client(transport) as client:
        tools = await client.list_tools()
        assert len(tools) == 15
        result = await call(client, "get_capabilities")
        assert result["sources"]["scholar"]["enabled"] is False
        result = await call(client, "get_papers", paper_refs=["arxiv:1706.03762"], cache="only")
        assert result["results"][0]["paper"] is None
        exported = await call(client, "export_records", paper_refs=["arxiv:1706.03762"])
        assert exported["missing"]
