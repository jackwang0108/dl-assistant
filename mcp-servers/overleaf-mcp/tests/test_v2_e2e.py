import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import anyio
import httpx
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from overleaf_mcp import server
from overleaf_mcp.config import Config
from overleaf_mcp.credentials import Credential
from overleaf_mcp.service import Service


async def call(client, tool_name, **arguments):
    result = await client.call_tool(tool_name, arguments)
    assert not result.is_error and "error" not in result.data, (tool_name, result.data)
    return result.data


def test_all_protocol_tools_annotations_and_full_workflow(service, cloud, monkeypatch, tmp_path):
    monkeypatch.setattr(server, "_service", service)

    async def scenario():
        async with Client(server.mcp) as client:
            tools = await client.list_tools()
            names = {t.name for t in tools}
            assert len(names) == 26 and "overleaf_compile" in names and "overleaf_read_log" in names
            export = next(t for t in tools if t.name == "overleaf_export_review_bundle")
            assert export.annotations.openWorldHint is False
            delete = next(t for t in tools if t.name == "overleaf_delete_project")
            assert (
                delete.annotations.destructiveHint is True
                and delete.annotations.readOnlyHint is False
            )
            assert (await call(client, "overleaf_capabilities"))["api_version"] == 2
            assert (await call(client, "overleaf_auth_status", verify=True))["valid"] is True
            assert (await call(client, "overleaf_projects"))["items"]
            assert (await call(client, "overleaf_import_auth", path=str(service.credentials.path)))[
                "validated"
            ]
            assert (await call(client, "overleaf_project_files", project_id="p1"))["items"]
            await call(client, "overleaf_workspaces")
            assert (await call(client, "overleaf_workspace", project_id="p1"))["items"][0][
                "binding"
            ] is None
            project = (
                await call(
                    client,
                    "overleaf_create_project",
                    name="Dedicated protocol test",
                    template="example",
                )
            )["project_id"]
            await call(client, "overleaf_project_settings", project_id=project, compiler="pdflatex")
            cloud.fail_next = True
            failed = await call(client, "overleaf_compile", project_id=project)
            assert failed["classification"] == "failed"
            succeeded = await call(client, "overleaf_compile", project_id=project)
            ident = succeeded["compile_id"]
            assert succeeded["classification"] == "clean"
            assert (await call(client, "overleaf_compile_status", project_id=project))[
                "compile_id"
            ] == ident
            assert (await call(client, "overleaf_compiles", project_id=project))["items"][0][
                "compile_id"
            ] == ident
            assert (
                await call(client, "overleaf_compile_report", project_id=project, compile_id=ident)
            )["items"]
            assert (await call(client, "overleaf_read_log", project_id=project, compile_id=ident))[
                "items"
            ]
            assert (
                await call(
                    client,
                    "overleaf_download_output",
                    project_id=project,
                    filename="output.pdf",
                    compile_id=ident,
                )
            )["format_valid"]
            rendered = await call(
                client, "overleaf_render", project_id=project, pages="1", compile_id=ident
            )
            assert Path(rendered["items"][0]["path"]).is_file()
            bundle = await call(
                client,
                "overleaf_export_review_bundle",
                project_id=project,
                compile_id=ident,
                pages="1",
            )
            assert Path(bundle["path"]).is_file() and bundle["screenshots_status"] == "included"
            assert (
                await call(
                    client,
                    "overleaf_compare_compiles",
                    project_id=project,
                    left_compile_id=failed["compile_id"],
                    right_compile_id=ident,
                )
            )["items"]
            await call(
                client, "overleaf_pin_compile", project_id=project, compile_id=failed["compile_id"]
            )
            await call(client, "overleaf_prune_compiles", project_id=project, keep=1)
            assert (await call(client, "overleaf_threads", project_id=project))["items"][0][
                "kind"
            ] == "feedback_context"
            assert (await call(client, "overleaf_history", project_id=project))["items"]
            assert (await call(client, "overleaf_labels", project_id=project))["items"]
            assert Path(
                (await call(client, "overleaf_version_snapshot", project_id=project, version=1))[
                    "path"
                ]
            ).is_file()
            await call(
                client,
                "overleaf_delete_project",
                project_id=project,
                expected_name="Dedicated protocol test",
            )

    anyio.run(scenario)


def test_real_stdio_subprocess_with_real_http_compile_and_download(tmp_path, cloud):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.handle_request()

        def do_POST(self):
            self.handle_request()

        def handle_request(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            request = httpx.Request(
                self.command,
                cloud.origin + self.path,
                headers=dict(self.headers.items()),
                content=body,
            )
            response = cloud.handler(request)
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response.content)

        def log_message(self, *args):
            pass

    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    cloud.origin = f"http://127.0.0.1:{http.server_port}"
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    config = Config(home=tmp_path, base_url=cloud.origin)
    config.credentials_path = tmp_path / "auth-v2.json"
    Service(config).credentials.save(
        Credential("overleaf_session2=test-session", "test-csrf", config.origin)
    )

    async def scenario():
        transport = StdioTransport(
            command=sys.executable,
            args=["-m", "overleaf_mcp"],
            env={
                "OVERLEAF_MCP_HOME": str(tmp_path),
                "OVERLEAF_BASE_URL": cloud.origin,
                "OVERLEAF_PROXY_URL": "",
                "OVERLEAF_CREDENTIALS_PATH": str(tmp_path / "auth-v2.json"),
            },
        )
        async with Client(transport) as client:
            compile_ = await call(client, "overleaf_compile", project_id="p1")
            assert compile_["classification"] == "clean"
            artifact = await call(
                client,
                "overleaf_download_output",
                project_id="p1",
                compile_id=compile_["compile_id"],
                filename="output.pdf",
            )
            assert artifact["format_valid"]
            rendered = await call(
                client,
                "overleaf_render",
                project_id="p1",
                compile_id=compile_["compile_id"],
                pages="1",
            )
            assert Path(rendered["items"][0]["path"]).exists()

    try:
        anyio.run(scenario)
    finally:
        http.shutdown()
        http.server_close()
        thread.join(timeout=5)


def test_protocol_validation_and_source_errors(service, monkeypatch):
    monkeypatch.setattr(server, "_service", service)

    async def scenario():
        async with Client(server.mcp) as client:
            result = await client.call_tool("overleaf_compile_report", {"project_id": "missing"})
            assert result.data["error"]["code"] == "COMPILE_NOT_FOUND"
            result = await client.call_tool(
                "overleaf_project_settings",
                {"project_id": "p1", "compiler": "invented"},
                raise_on_error=False,
            )
            assert result.is_error
            result = await client.call_tool(
                "overleaf_download_output", {"project_id": "p1", "filename": ".."}
            )
            assert result.data["error"]["code"] == "INVALID_FILENAME"

    anyio.run(scenario)
