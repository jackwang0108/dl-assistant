import json
import os
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from overleaf_mcp.config import Config
from overleaf_mcp.credentials import Credential, CredentialStore
from overleaf_mcp.diagnostics import classify, parse_log
from overleaf_mcp.models import OverleafError, filename
from overleaf_mcp.paging import page
from overleaf_mcp.store import Store


@pytest.mark.parametrize(
    "name", ["..", ".", "../output.pdf", "folder/output.pdf", "/tmp/output.pdf", "", "bad\x00.pdf"]
)
def test_output_filename_rejects_escape(name):
    with pytest.raises(OverleafError):
        filename(name)


def test_failed_server_and_stats_never_become_success():
    assert (
        classify({"status": "failure", "outputFiles": []}, "No matching error regex")[0] == "failed"
    )
    assert (
        classify(
            {
                "status": "success",
                "stats": {"latexmk-errors": 2},
                "outputFiles": [{"path": "output.pdf"}],
            },
            "Looks clean",
        )[0]
        == "failed"
    )
    assert (
        classify({"status": "success", "outputFiles": [{"path": "output.pdf"}]}, None)[0]
        == "unknown"
    )
    assert (
        classify(
            {"status": "success", "outputFiles": [{"path": "output.pdf"}]},
            "Output written.",
            "Killed due to out of memory",
        )[0]
        == "failed"
    )


def test_diagnostic_locations_and_warnings_are_evidence_not_file_instructions():
    result = parse_log(
        "chapter.tex:27: LaTeX Error: Bad symbol\nLaTeX Warning: Citation undefined on input line 31.\nOverfull \\hbox at lines 10--12"
    )
    assert result[0]["source_file"] == "chapter.tex" and result[0]["source_line"] == 27
    assert result[1]["severity"] == "warning" and result[1]["source_line"] == 31
    assert result[2]["source_line"] == 10
    assert result[2]["source_end_line"] == 12


def test_classic_tex_trace_and_bibliography_errors():
    issues = parse_log(
        "! Undefined control sequence.\n<argument> \\missing\nl.12 \\bad\n! Fatal error"
    )
    assert issues[0]["log_line"] == 1 and issues[0]["log_end_line"] == 3
    assert "l.12" in issues[0]["excerpt"]
    assert issues[0]["source_line"] == 12 and issues[0]["source_file"] is None
    assert issues[0]["source_location_status"] == "reported_line_only"
    assert issues[1]["source_location_status"] == "unavailable"
    status, bibliography = classify(
        {"status": "success", "outputFiles": [{"path": "output.pdf"}]},
        log="Output written.",
        blg="2025/01/01 ERROR - Cannot find 'refs.bib'!",
    )
    assert status == "failed" and bibliography[0]["stream"] == "output.blg"


def test_paging_limits_entire_json_and_reassembles_huge_records(service):
    records = [{"text": '\\"中文\n' * 5000}, {"text": "last"}]
    result = page(service.store, ["x"], records, max_chars=2000)
    recovered = []
    parts = {}
    while True:
        assert len(json.dumps(result, ensure_ascii=False)) <= 2000
        for item in result["items"]:
            if item.get("kind") == "record_fragment":
                key = item["record_index"]
                parts.setdefault(key, []).append(item["text"])
                if item["final"]:
                    recovered.append(json.loads("".join(parts[key])))
            else:
                recovered.append(item)
        if not result["next_cursor"]:
            break
        result = page(service.store, ["x"], cursor=result["next_cursor"], max_chars=2000)
    assert recovered == records


def test_continuation_is_bound_to_request_and_does_not_refetch(service, cloud):
    cloud.projects.update({f"p{i}": "Long title " * 100 for i in range(2, 10)})
    first = service.projects(max_chars=2000)
    count = len(cloud.calls)
    assert first["next_cursor"]
    service.projects(first["next_cursor"], 2000)
    assert len(cloud.calls) == count
    with pytest.raises(OverleafError):
        page(service.store, ["wrong"], cursor=first["next_cursor"], max_chars=2000)


def test_credentials_are_private_origin_bound_and_nonprinting(tmp_path):
    store = CredentialStore(tmp_path / "credentials.json", "https://www.overleaf.com")
    credential = Credential("secret-cookie", "secret-csrf", "https://www.overleaf.com")
    store.save(credential)
    assert "secret" not in repr(store.read())
    if os.name == "posix":
        assert store.path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(OverleafError):
        CredentialStore(store.path, "https://other.example").read()
    store.path.write_text("[]")
    with pytest.raises(OverleafError):
        store.read()


def test_concurrent_credential_writes_are_complete(tmp_path):
    store = CredentialStore(tmp_path / "creds.json", "https://www.overleaf.com")

    def write(i):
        store.save(Credential(f"cookie-{i}", f"csrf-{i}", store.origin))

    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(write, range(20)))
    value = store.read()
    assert value.cookie.split("-")[-1] == value.csrf_token.split("-")[-1]


def test_origin_rejected_before_cookie_sent(service):
    seen = []
    service.client.http = httpx.Client(
        transport=httpx.MockTransport(lambda r: seen.append(r) or httpx.Response(200, content=b"x"))
    )
    with pytest.raises(OverleafError):
        service.client.outputs(
            {"outputFiles": [{"path": "output.pdf", "url": "https://evil.example/stolen"}]},
            "output.pdf",
        )
    assert not seen


def test_cdn_and_redirect_do_not_receive_cookie_even_with_client_cookie_jar(service):
    seen = []

    def handler(request):
        seen.append(request)
        return (
            httpx.Response(302, headers={"location": "https://compiles.overleaf.com/file"})
            if request.url.path == "/start"
            else httpx.Response(200, content=b"output")
        )

    service.client.http = httpx.Client(
        transport=httpx.MockTransport(handler), cookies={"leak": "must-not-send"}
    )
    assert service.client.request("GET", "/start", output=True) == b"output"
    assert seen[0].headers.get("cookie") == "overleaf_session2=test-session"
    assert "cookie" not in seen[1].headers and "x-csrf-token" not in seen[1].headers


@pytest.mark.parametrize(
    "status,expected", [(401, "AUTH_EXPIRED"), (403, "FORBIDDEN"), (429, "RATE_LIMITED")]
)
def test_auth_permission_and_rate_limit_are_distinct(service, status, expected):
    calls = []
    service.client.http = httpx.Client(
        transport=httpx.MockTransport(lambda r: calls.append(r) or httpx.Response(status))
    )
    with pytest.raises(OverleafError) as error:
        service.client.projects()
    assert error.value.code == expected and len(calls) == 1


def test_redirect_to_login_and_cdn_denial_are_not_conflated(service):
    service.client.http = httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(302, headers={"location": "/login?"})
        )
    )
    with pytest.raises(OverleafError) as error:
        service.client.projects()
    assert error.value.code == "AUTH_EXPIRED"
    service.client.http = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(403)))
    with pytest.raises(OverleafError) as error:
        service.client.request("GET", "https://compiles.overleaf.com/file", output=True)
    assert error.value.code == "OUTPUT_ACCESS_FAILED"


def test_schema_change_is_not_an_empty_project_list(service):
    service.client.http = httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"new_field": []}))
    )
    with pytest.raises(OverleafError) as error:
        service.client.projects()
    assert error.value.code == "API_SCHEMA"


def test_symlink_rejected_before_any_external_directory_creation(service, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    artifacts = service.store.root / "artifacts"
    artifacts.mkdir()
    (artifacts / "p1").symlink_to(outside, target_is_directory=True)
    with pytest.raises(OverleafError):
        service.store.directory("p1", "compile1")
    assert not list(outside.iterdir())


def test_instance_namespaces_and_single_active_compile(tmp_path):
    a = Store(Config(home=tmp_path, base_url="https://www.overleaf.com"))
    b = Store(Config(home=tmp_path, base_url="https://selfhost.example"))
    assert a.root != b.root
    first = a.reserve("p1", {})
    with pytest.raises(OverleafError):
        a.reserve("p1", {})
    a.patch("p1", first["compile_id"], {"state": "outcome_unknown"})
    with pytest.raises(OverleafError):
        a.reserve("p1", {})
    second = a.reserve("p1", {}, retry_unknown=True)
    assert second["explicit_retry_of_unknown"] == first["compile_id"]


def test_download_byte_budget_and_mutation_500_unknown(service):
    service.client.http = httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, content=b"x" * 1024))
    )
    with pytest.raises(OverleafError) as error:
        service.client.request("GET", "/large", max_bytes=100)
    assert error.value.code == "DOWNLOAD_LIMIT"
    service.client.http = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    with pytest.raises(OverleafError) as error:
        service.client.request("POST", "/project/p1/compile", {})
    assert error.value.code == "REQUEST_OUTCOME_UNKNOWN"


@pytest.mark.parametrize("spec", ["0", "3", "1-999999", "bad", "2-1"])
def test_render_page_ranges_do_not_silently_shrink(spec):
    from overleaf_mcp.render import pages

    with pytest.raises(OverleafError):
        pages(spec, 2)


def test_invalid_credential_import_preserves_previous_session(service, tmp_path):
    candidate = tmp_path / "candidate.json"
    candidate.write_text(
        json.dumps(
            {"origin": service.config.origin, "cookie": "bad-cookie", "csrf_token": "candidate"}
        )
    )
    candidate.chmod(0o600)
    with pytest.raises(OverleafError):
        service.import_auth(str(candidate))
    assert service.credentials.read().cookie == "overleaf_session2=test-session"


def test_empty_proxy_environment_is_accepted(tmp_path, monkeypatch):
    monkeypatch.setenv("OVERLEAF_PROXY_URL", "")
    assert Config(home=tmp_path).proxy is None
