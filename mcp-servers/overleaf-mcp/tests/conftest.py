import io
import json
import zipfile

import httpx
import pymupdf
import pytest

from overleaf_mcp.config import Config
from overleaf_mcp.credentials import Credential
from overleaf_mcp.service import Service


def pdf_bytes(text="Research paper", pages=2):
    with pymupdf.open() as pdf:
        for number in range(pages):
            pdf.new_page(width=300, height=400).insert_text((30, 40), f"{text} page {number + 1}")
        return pdf.tobytes()


class Cloud:
    def __init__(self, origin="https://www.overleaf.com"):
        self.origin = origin
        self.projects = {"p1": "Test project"}
        self.builds = {}
        self.calls = []
        self.fail_next = False
        self.timeout_next = False
        self.next_history = None
        self.version = 1

    def handler(self, request):
        self.calls.append(request)
        path = request.url.path
        if "/build/" in path:
            build, name = path.split("/build/")[1].split("/", 1)
            return httpx.Response(200, content=self.builds[build][name])
        if request.headers.get("cookie") != "overleaf_session2=test-session":
            return httpx.Response(401)
        if request.method != "GET" and request.headers.get("x-csrf-token") != "test-csrf":
            return httpx.Response(403)
        if path == "/dev/csrf":
            return httpx.Response(200, text="test-csrf")
        if path == "/user/projects":
            return httpx.Response(
                200,
                json={
                    "projects": [
                        {"_id": key, "name": value} for key, value in self.projects.items()
                    ]
                },
            )
        if path == "/project/new":
            data = json.loads(request.content)
            key = "p" + str(len(self.projects) + 1)
            self.projects[key] = data["projectName"]
            return httpx.Response(200, json={"project_id": key})
        project = path.split("/")[2] if path.startswith("/project/") else None
        if path.endswith("/compile"):
            if self.timeout_next:
                self.timeout_next = False
                raise httpx.ReadTimeout("simulated; no credentials", request=request)
            build = "b" + str(len(self.builds) + 1)
            failed = self.fail_next
            self.fail_next = False
            self.builds[build] = {
                "output.log": b"! Undefined control sequence.\nl.12 \\bad"
                if failed
                else b"Output written on output.pdf (2 pages).",
                "output.stderr": b"",
            }
            if not failed:
                self.builds[build]["output.pdf"] = pdf_bytes("Changed " + build)
            return httpx.Response(
                200,
                json={
                    "status": "failure" if failed else "success",
                    "stats": {"latexmk-errors": int(failed)},
                    "outputFiles": [
                        {"path": name, "url": f"/build/{build}/{name}"}
                        for name in self.builds[build]
                    ],
                },
            )
        if path.endswith("/updates"):
            return httpx.Response(
                200,
                json=self.next_history
                or {
                    "updates": [{"toV": self.version, "end_ts": 1000}],
                    "nextBeforeTimestamp": None,
                },
            )
        if path.endswith("/entities"):
            return httpx.Response(
                200, json={"entities": [{"id": "doc1", "name": "main.tex", "type": "doc"}]}
            )
        if path.endswith("/threads"):
            return httpx.Response(
                200,
                json={
                    "thread1": {
                        "messages": [{"content": "Check the supported claim"}],
                        "resolved": False,
                        "ranges": [{"doc_id": "doc1", "start": 10, "end": 20}],
                    }
                },
            )
        if path.endswith("/labels"):
            return httpx.Response(200, json=[{"id": "label1", "version": 1, "comment": "Reviewed"}])
        if "/version/" in path:
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as archive:
                archive.writestr("main.tex", r"\documentclass{article}")
            return httpx.Response(200, content=buffer.getvalue())
        if request.method == "DELETE":
            self.projects.pop(project, None)
            return httpx.Response(204)
        if path.endswith("/settings"):
            return httpx.Response(204)
        return httpx.Response(404)


@pytest.fixture
def cloud():
    return Cloud()


@pytest.fixture
def service(tmp_path, cloud):
    config = Config(home=tmp_path, cdn_origins=["https://compiles.overleaf.com"])
    config.credentials_path = tmp_path / "auth-v2.json"
    result = Service(config, httpx.Client(transport=httpx.MockTransport(cloud.handler)))
    result.credentials.save(
        Credential("overleaf_session2=test-session", "test-csrf", config.origin)
    )
    return result
