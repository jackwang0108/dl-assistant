"""MCP protocol and real stdio process tests for all v2 tools."""

import sys
from pathlib import Path

import pymupdf
import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from tex_mcp import server
from tex_mcp.service import Service

pytestmark = pytest.mark.asyncio


@pytest.fixture
def source(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    (root / "main.tex").write_text(r"""\documentclass{article}\newcommand{\figref}[1]{Fig.~\ref{#1}}
\begin{document}\section{Intro}Start\section{Background}Background
\section{Method}\subsection{One}One\subsection{Two}Two
\subsection{Three}See \figref{fig:arch} and \cite{refkey}.
\section{Other}\input{figure}\bibliography{refs}\end{document}""")
    (root / "figure.tex").write_text(
        r"\begin{figure}\includegraphics{image.pdf}\caption{Architecture}\label{fig:arch}\end{figure}"
    )
    (root / "refs.bib").write_text(
        "@article{refkey,title={Reference Title},author={One Author},year={2020},doi={10.1234/ref}}"
    )
    pdf = pymupdf.open()
    pdf.new_page(width=100, height=100)
    pdf.save(root / "image.pdf")
    pdf.close()
    return root


@pytest.fixture
def mcp(source, tmp_path, monkeypatch):
    monkeypatch.setattr(server, "_service", Service(tmp_path / "cache", interval=0))
    return server.mcp


async def call(client, name, **kwargs):
    response = await client.call_tool(name, kwargs)
    assert not response.is_error
    assert "error" not in response.data, response.data
    return response.data


async def test_all_tools_and_cross_file_section_workflow(mcp, source, tmp_path):
    async with Client(mcp) as client:
        assert {t.name for t in await client.list_tools()} == {
            "tex_capabilities",
            "tex_open",
            "tex_outline",
            "tex_read",
            "tex_search",
            "tex_objects",
            "tex_get_object",
            "tex_references",
            "tex_reference_lookups",
            "tex_read_file",
            "tex_diagnostics",
            "tex_compare",
            "tex_attach_pdf",
            "tex_render_object",
        }
        assert (await call(client, "tex_capabilities"))["api_version"] == 2
        opened = await call(client, "tex_open", source=str(source))
        doc = opened["document_id"]
        outline = await call(client, "tex_outline", document_id=doc)
        assert any(s["id"] == "3.3" for s in outline["outline"])
        section = await call(client, "tex_read", document_id=doc, section="3.3")
        figure = next(i for i in section["items"] if i["kind"] == "object")
        assert figure["labels"] == ["fig:arch"] and figure["relationship"] == "directly_referenced"
        assert Path(figure["assets"][0]["image_path"]).exists()
        assert (await call(client, "tex_objects", document_id=doc))["items"]
        obj = await call(client, "tex_get_object", document_id=doc, object_ref="fig:arch")
        assert obj["items"][0]["caption"] == "Architecture"
        assert (await call(client, "tex_search", document_id=doc, query="See"))["matches"]
        refs = await call(client, "tex_references", document_id=doc, section="3.3")
        assert refs["items"][0]["key"] == "refkey"
        lookups = await call(client, "tex_reference_lookups", document_id=doc)
        assert lookups["items"][1]["paper_search_inputs"] == [{"identifier": "doi:10.1234/ref"}]
        original = await call(client, "tex_read_file", document_id=doc, path="figure.tex")
        assert "\\includegraphics" in original["items"][0]["text"]
        await call(client, "tex_diagnostics", document_id=doc)
        pdf = await call(client, "tex_attach_pdf", document_id=doc, path=str(source / "image.pdf"))
        render = await call(
            client,
            "tex_render_object",
            document_id=doc,
            object_ref="fig:arch",
            pdf_ref=pdf["pdf_ref"],
            page=1,
            bbox=[0, 0, 50, 50],
            dpi=72,
        )
        assert pymupdf.Pixmap(render["image_path"]).width == 50
        (source / "main.tex").write_text(
            (source / "main.tex").read_text().replace("Start", "Changed")
        )
        second = await call(client, "tex_open", source=str(source))
        diff = await call(
            client, "tex_compare", left_document_id=doc, right_document_id=second["document_id"]
        )
        assert diff["items"]


@pytest.mark.parametrize(
    "name,arguments",
    [
        ("tex_read", {"document_id": "missing", "view": "invented"}),
        ("tex_open", {"source": "bad", "limits": {"max_requests": 0}}),
        ("tex_get_object", {"document_id": "missing", "object_ref": "x", "asset_mode": "invented"}),
    ],
)
async def test_invalid_protocol_inputs(mcp, name, arguments):
    async with Client(mcp) as client:
        result = await client.call_tool(name, arguments, raise_on_error=False)
        assert result.is_error


async def test_errors_are_structured_not_silent_empty(mcp, source):
    async with Client(mcp) as client:
        result = await client.call_tool("tex_outline", {"document_id": "missing"})
        assert result.data["error"]["code"] == "DOCUMENT_NOT_FOUND"
        opened = await call(client, "tex_open", source=str(source))
        result = await client.call_tool(
            "tex_get_object", {"document_id": opened["document_id"], "object_ref": "nonexistent"}
        )
        assert result.data["error"]["code"] == "OBJECT_NOT_FOUND"


async def test_real_stdio_open_section_and_attached_image(source, tmp_path):
    transport = StdioTransport(
        command=sys.executable,
        args=["-m", "tex_mcp"],
        env={"TEX_MCP_CACHE_DIR": str(tmp_path / "stdio-cache")},
    )
    async with Client(transport) as client:
        assert len(await client.list_tools()) == 14
        doc = (await call(client, "tex_open", source=str(source)))["document_id"]
        section = await call(client, "tex_read", document_id=doc, section="3.3")
        figure = next(i for i in section["items"] if i["kind"] == "object")
        assert (
            figure["caption"] == "Architecture" and Path(figure["assets"][0]["image_path"]).exists()
        )


async def test_reference_handoff_through_paper_search_protocol(mcp, source, tmp_path, monkeypatch):
    import httpx

    other_source = Path(__file__).resolve().parents[3] / "mcp-servers/paper-search-mcp/src"
    if not other_source.is_dir():
        pytest.skip("Repository integration requires sibling paper-search source")
    monkeypatch.syspath_prepend(str(other_source))
    import paper_search_mcp.server as paper_server
    from paper_search_mcp.config import Config
    from paper_search_mcp.service import Service as SearchService
    from paper_search_mcp.transport import Transport

    def handler(request):
        return httpx.Response(
            200,
            json={
                "paperId": "source-reference",
                "externalIds": {"DOI": "10.1234/ref"},
                "title": "Reference Title",
                "year": 2020,
                "authors": [{"name": "One Author"}],
            },
        )

    intervals = dict.fromkeys(["arxiv", "semantic_scholar", "scholar", "openalex", "download"], 0.0)
    monkeypatch.setattr(
        paper_server,
        "_service",
        SearchService(
            Config(tmp_path / "paper-cache", {}),
            Transport(httpx.Client(transport=httpx.MockTransport(handler)), intervals),
        ),
    )
    async with Client(mcp) as tex_client, Client(paper_server.mcp) as search_client:
        doc = (await call(tex_client, "tex_open", source=str(source)))["document_id"]
        lookups = await call(tex_client, "tex_reference_lookups", document_id=doc)
        lookup = next(i for i in lookups["items"] if i["kind"] == "reference_lookup")
        resolved = await call(
            search_client,
            "resolve_papers",
            inputs=lookup["paper_search_inputs"],
            sources=["semantic_scholar"],
        )
        assert resolved["results"][0]["status"] == "confirmed"
        assert "doi:10.1234/ref" in resolved["results"][0]["paper"]["identifiers"]
        references = await call(tex_client, "tex_references", document_id=doc)
        assert references["items"][0]["external_identity"] == "unverified"
