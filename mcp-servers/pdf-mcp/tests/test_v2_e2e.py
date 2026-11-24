import sys
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from pdf_mcp import server
from pdf_mcp.service import Service

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mcp(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "_service", Service(tmp_path / "cache"))
    return server.mcp


async def call(client, name, **arguments):
    result = await client.call_tool(name, arguments)
    assert not result.is_error and "error" not in result.data, result.data
    return result.data


async def test_protocol_tools_and_full_workflow(mcp, text_pdf, table_pdf):
    async with Client(mcp) as client:
        assert {t.name for t in await client.list_tools()} == {
            "pdf_capabilities",
            "pdf_open",
            "pdf_info",
            "pdf_page_info",
            "pdf_outline",
            "pdf_read",
            "pdf_search",
            "pdf_objects",
            "pdf_get_object",
            "pdf_render",
            "pdf_parse",
            "pdf_diagnostics",
            "pdf_references",
            "pdf_links",
            "pdf_source_candidates",
            "pdf_cache_stats",
            "pdf_cache_clear",
        }
        assert (await call(client, "pdf_capabilities"))["api_version"] == 2
        doc = (await call(client, "pdf_open", source=text_pdf))["document_id"]
        assert (await call(client, "pdf_info", document_id=doc))["items"][0]["page_count"] == 3
        assert (await call(client, "pdf_page_info", document_id=doc, pages="1"))["items"][0][
            "chars"
        ] > 0
        assert (await call(client, "pdf_outline", document_id=doc))["items"]
        assert (await call(client, "pdf_read", document_id=doc, section="Experiments"))["items"]
        matches = await call(client, "pdf_search", document_id=doc, query="experiments")
        match = next(i for i in matches["items"] if i["kind"] == "match")
        local = await call(client, "pdf_read", document_id=doc, match_ref=match["match_ref"])
        assert local["items"][0]["scope"] == "match"
        assert any(i["kind"] == "original_page_crop" for i in local["items"])
        assert matches["items"][0]["pages_with_matches"] == [2]
        rendered = await call(
            client, "pdf_render", document_id=doc, pages="2", bbox=[0, 0, 200, 200]
        )
        assert Path(rendered["items"][0]["image_path"]).is_file()
        await call(client, "pdf_links", document_id=doc)
        await call(client, "pdf_diagnostics", document_id=doc)
        await call(client, "pdf_references", document_id=doc)
        await call(client, "pdf_source_candidates", document_id=doc, arxiv_id="2404.14219v1")
        table_doc = (await call(client, "pdf_open", source=table_pdf))["document_id"]
        objects = await call(client, "pdf_objects", document_id=table_doc, kind="table")
        obj = next(i for i in objects["items"] if i.get("kind") == "table")
        assert (
            await call(
                client,
                "pdf_get_object",
                document_id=table_doc,
                object_id=obj["object_id"],
                view="image",
            )
        )["items"][0]["image"]["image_path"]
        assert (await call(client, "pdf_cache_stats"))["documents"] == 2
        assert (await call(client, "pdf_cache_clear", expired_only=False))["cleared_documents"] == 2


async def test_real_stdio_process(text_pdf, tmp_path):
    transport = StdioTransport(
        command=sys.executable,
        args=["-m", "pdf_mcp"],
        env={"PDF_MCP_CACHE_DIR": str(tmp_path / "stdio-cache")},
    )
    async with Client(transport) as client:
        doc = (await call(client, "pdf_open", source=text_pdf))["document_id"]
        read = await call(client, "pdf_read", document_id=doc, pages="1")
        assert any("introduce" in i.get("text", "") for i in read["items"])
        assert Path(
            (await call(client, "pdf_render", document_id=doc, pages="1"))["items"][0]["image_path"]
        ).exists()


async def test_schema_and_structured_errors(mcp, text_pdf):
    async with Client(mcp) as client:
        result = await client.call_tool("pdf_info", {"document_id": "missing"})
        assert result.data["error"]["code"] == "DOCUMENT_NOT_FOUND"
        result = await client.call_tool(
            "pdf_open", {"source": text_pdf, "source_format": "invented"}, raise_on_error=False
        )
        assert result.is_error
        doc = (await call(client, "pdf_open", source=text_pdf))["document_id"]
        result = await client.call_tool("pdf_read", {"document_id": doc, "pages": "1-2wrong"})
        assert result.data["error"]["code"] == "INVALID_PAGES"
        result = await client.call_tool(
            "pdf_source_candidates", {"document_id": doc, "arxiv_id": "1706.03762"}
        )
        assert result.data["error"]["code"] == "VERSION_REQUIRED"


async def test_parse_protocol_uses_selected_pages_and_saved_parse_id(
    mcp, text_pdf, tmp_path, monkeypatch
):
    executable = tmp_path / "parser-python"
    executable.write_text(
        "#!"
        + sys.executable
        + '\nimport json,sys\nfrom pathlib import Path\nif sys.argv[1]=="-c":\n print("test-engine");sys.exit()\nr=json.loads(Path(sys.argv[2]).read_text())\nassert r["allow_model_download"] is False\nb={"block_id":"b1","kind":"text","page":r["pages"][0],"bbox":[20,20,100,40],"text":"Parsed evidence","provenance":"test_worker","section_ids":[],"reference_targets":[]}\nPath(sys.argv[3]).write_text(json.dumps({"blocks":[b],"objects":[],"sections":[],"references":[],"diagnostics":[],"pages_processed":r["pages"],"coverage":"inferred","engine_version":"test-engine"}))\n'
    )
    executable.chmod(0o700)
    monkeypatch.setenv("PDF_MCP_STRUCTURE_PYTHON", str(executable))
    async with Client(mcp) as client:
        doc = (await call(client, "pdf_open", source=text_pdf))["document_id"]
        parsed = await call(client, "pdf_parse", document_id=doc, pages="2")
        assert parsed["pages_processed"] == [2]
        read = await call(client, "pdf_read", document_id=doc, parse_id=parsed["parse_id"])
        assert read["items"][1]["text"] == "Parsed evidence"
        assert (await call(client, "pdf_parse", document_id=doc, pages="2"))["cache_state"] == "hit"
        result = await client.call_tool(
            "pdf_read", {"document_id": doc, "parse_id": parsed["parse_id"], "pages": "1"}
        )
        assert result.data["error"]["code"] == "PARSE_SCOPE_MISMATCH"
