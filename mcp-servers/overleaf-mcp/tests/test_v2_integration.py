import subprocess
from pathlib import Path

import httpx
import pymupdf
import pytest

from overleaf_mcp.models import OverleafError
from overleaf_mcp.store import Store


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def make_repo(root, project="p1"):
    root.mkdir()
    git(root, "init", "-b", "working")
    git(root, "config", "user.name", "Test Author")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "remote", "add", "origin", "https://git.overleaf.com/" + project)
    (root / "main.tex").write_text("First source")
    git(root, "add", "main.tex")
    git(root, "commit", "-m", "Initial source")
    return root


def test_fail_fix_success_download_render_and_report(service, cloud, tmp_path):
    repo = make_repo(tmp_path / "repo")
    bound = service.bind("p1", str(repo))
    assert bound["dirty"] is False
    cloud.fail_next = True
    first = service.compile("p1", expected_commit=bound["head"])
    assert first["classification"] == "failed"
    assert service.report("p1", first["compile_id"])["items"]
    (repo / "main.tex").write_text("Fixed source")
    git(repo, "add", "main.tex")
    git(repo, "commit", "-m", "Fix source")
    head = git(repo, "rev-parse", "HEAD")
    second = service.compile("p1", expected_commit=head)
    assert (
        second["classification"] == "clean"
        and second["source_binding"] == "compiled_revision_not_certified"
    )
    pdf = service.download("p1", "output.pdf", second["compile_id"])
    assert pdf["format_valid"] and pdf["pages"] == 2
    small = service.render("p1", second["compile_id"], "1", 72)["items"][0]
    large = service.render("p1", second["compile_id"], "1", 144)["items"][0]
    assert (
        small["path"] != large["path"]
        and pymupdf.Pixmap(small["path"]).width == 300
        and large["width"] == 600
    )
    assert service.read_log("p1", second["compile_id"])["items"][0]["line"] == 1
    assert service.status("p1")["compile_id"] == second["compile_id"]


def test_old_download_never_rewinds_latest_and_restart_reads_same_records(service):
    first = service.compile("p1")
    second = service.compile("p1")
    service.download("p1", "output.pdf", first["compile_id"])
    assert service.status("p1")["compile_id"] == second["compile_id"]
    restarted = Store(service.config)
    assert restarted.get("p1")["compile_id"] == second["compile_id"]


def test_existing_invalid_pdf_not_trusted_and_tamper_is_reported(service):
    compiled = service.compile("p1")
    folder = service.store.directory("p1", compiled["compile_id"])
    (folder / "output.pdf").write_bytes(b"not PDF")
    item = service.download("p1", "output.pdf", compiled["compile_id"])
    assert item["format_valid"]
    (folder / "output.pdf").write_bytes(b"changed")
    with pytest.raises(OverleafError) as error:
        service.download("p1", "output.pdf", compiled["compile_id"])
    assert error.value.code == "ARTIFACT_CHANGED"


def test_invalid_remote_pdf_does_not_become_cached_artifact(service, cloud):
    compiled = service.compile("p1")
    cloud.builds["b1"]["output.pdf"] = b"<html>login</html>"
    with pytest.raises(OverleafError) as error:
        service.download("p1", "output.pdf", compiled["compile_id"])
    assert error.value.code == "INVALID_PDF"
    assert "output.pdf" not in service.store.get("p1", compiled["compile_id"])["outputs"]


def test_unknown_compile_is_journaled_not_blindly_retried(service, cloud):
    cloud.timeout_next = True
    first = service.compile("p1")
    assert first["state"] == "outcome_unknown"
    count = sum(r.url.path.endswith("/compile") for r in cloud.calls)
    with pytest.raises(OverleafError):
        service.compile("p1")
    assert sum(r.url.path.endswith("/compile") for r in cloud.calls) == count
    next_result = service.compile("p1", retry_unknown=True)
    assert next_result["state"] == "completed"
    assert (
        service.store.get("p1", next_result["compile_id"])["explicit_retry_of_unknown"]
        == first["compile_id"]
    )


def test_logs_download_errors_remain_visible_not_success(service, cloud):
    handler = cloud.handler

    def fail_log(request):
        if request.url.path.endswith("output.log"):
            return httpx.Response(503)
        return handler(request)

    service.client.http = httpx.Client(transport=httpx.MockTransport(fail_log))
    result = service.compile("p1")
    assert result["classification"] == "unknown"
    record = service.store.get("p1", result["compile_id"])
    assert record["artifact_issues"][0]["code"] == "ARTIFACT_UNAVAILABLE"


def test_expected_commit_rejects_dirty_worktree_without_sending_compile(service, cloud, tmp_path):
    repo = make_repo(tmp_path / "repo")
    binding = service.bind("p1", str(repo))
    (repo / "main.tex").write_text("Uncommitted changes")
    with pytest.raises(OverleafError) as error:
        service.compile("p1", expected_commit=binding["head"])
    assert error.value.code == "SOURCE_NOT_READY"
    assert not any(r.url.path.endswith("/compile") for r in cloud.calls)
    assert git(repo, "branch", "--show-current") == "working"


def test_binding_rejects_wrong_project_or_token_in_remote(service, tmp_path):
    repo = make_repo(tmp_path / "repo", project="wrong")
    with pytest.raises(OverleafError):
        service.bind("p1", str(repo))
    git(repo, "remote", "set-url", "origin", "https://git:secret-token@git.overleaf.com/p1")
    with pytest.raises(OverleafError) as error:
        service.bind("p1", str(repo))
    assert "secret-token" not in str(error.value)


def test_source_and_diagnostic_comparison_and_pdf_visual_changes(service, tmp_path):
    repo = make_repo(tmp_path / "repo")
    service.bind("p1", str(repo))
    first = service.compile("p1")
    service.download("p1", "output.pdf", first["compile_id"])
    (repo / "main.tex").write_text("Next source")
    git(repo, "add", "main.tex")
    git(repo, "commit", "-m", "Next source")
    second = service.compile("p1")
    service.download("p1", "output.pdf", second["compile_id"])
    result = service.compare("p1", first["compile_id"], second["compile_id"], "1")["items"]
    assert result[0]["status"] == "available" and "main.tex" in result[0]["name_status"]
    assert next(i for i in result if i.get("page") == 1)["status"] == "visual_change"


def test_pin_dry_run_and_explicit_cleanup(service, tmp_path):
    first = service.compile("p1")
    second = service.compile("p1")
    third = service.compile("p1")
    service.store.pin("p1", first["compile_id"])
    dry = service.prune("p1", keep=1)
    assert dry["selected_compile_ids"] == [second["compile_id"]]
    assert len(service.store.compiles("p1")) == 3
    service.prune("p1", keep=1, dry_run=False)
    assert [r["compile_id"] for r in service.store.compiles("p1")] == [
        third["compile_id"],
        first["compile_id"],
    ]


def test_history_repeated_cursor_is_detected_and_schema_not_empty(service, cloud):
    cloud.next_history = {"updates": [{"toV": 1}], "nextBeforeTimestamp": 123}
    with pytest.raises(OverleafError) as error:
        service.history("p1", max_pages=3)
    assert error.value.code == "HISTORY_CURSOR_STALLED"


def test_comments_keep_anchor_and_history_context(service):
    result = service.threads("p1")["items"]
    assert result[0]["kind"] == "feedback_context"
    assert result[1]["ranges"][0]["doc_id"] == "doc1"
    assert result[1]["messages"][0]["content"] == "Check the supported claim"


def test_snapshot_validation_and_bare_filename_guard(service):
    result = service.snapshot("p1", 1)
    assert Path(result["path"]).is_file() and result["extracted"] is False
    compiled = service.compile("p1")
    with pytest.raises(OverleafError):
        service.download("p1", "..", compiled["compile_id"])


def test_projects_and_mutations_use_only_requested_target(service, cloud):
    project = service.create_project("Dedicated test", "example")
    with pytest.raises(OverleafError):
        service.delete_project(project["project_id"], "Wrong name")
    assert project["project_id"] in cloud.projects
    assert service.settings(project["project_id"], compiler="xelatex")["applied"] == {
        "compiler": "xelatex"
    }
    service.delete_project(project["project_id"], "Dedicated test")
    assert project["project_id"] not in cloud.projects and "p1" in cloud.projects


def test_expired_local_request_is_unknown_and_can_be_explicitly_retried(service):
    record = service.store.reserve("p1", {})
    service.store.patch("p1", record["compile_id"], {"request_deadline_ns": 1})
    status = service.status("p1", record["compile_id"])
    assert status["state"] == "outcome_unknown" and status["error"]["code"] == "REQUEST_INTERRUPTED"
    result = service.compile("p1", retry_unknown=True)
    assert result["state"] == "completed"


def test_concurrent_artifact_metadata_updates_do_not_lose_downloads(service):
    from concurrent.futures import ThreadPoolExecutor

    record = service.store.reserve("p1", {})

    def save(i):
        service.store.output("p1", record["compile_id"], f"output-{i}.log", {"sha256": str(i)})

    with ThreadPoolExecutor(max_workers=5) as executor:
        list(executor.map(save, range(20)))
    assert len(service.store.get("p1", record["compile_id"])["outputs"]) == 20


def test_zip_wrong_format_and_traversal_are_not_accepted(service):
    import io
    import zipfile

    service.client.http = httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, content=b"not zip"))
    )
    with pytest.raises(OverleafError) as error:
        service.snapshot("p1", 1)
    assert error.value.code == "INVALID_ARCHIVE"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("../escape.tex", "text")
    service.client.http = httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, content=buffer.getvalue()))
    )
    with pytest.raises(OverleafError) as error:
        service.snapshot("p1", 1)
    assert error.value.code == "INVALID_ARCHIVE"


def test_invalid_render_inputs_do_not_create_misleading_artifacts(service):
    record = service.compile("p1")
    service.download("p1", "output.pdf", record["compile_id"])
    with pytest.raises(OverleafError):
        service.render("p1", record["compile_id"], "1", dpi=0)
    with pytest.raises(OverleafError):
        service.render("p1", record["compile_id"], "1", bbox=[0, 0, float("nan"), 20])


def test_pin_after_cleanup_selection_still_protects_record(service, monkeypatch):
    first = service.compile("p1")
    service.compile("p1")
    original = service.store.compiles

    def raced_selection(project):
        records = original(project)
        service.store.pin(project, first["compile_id"])
        return records

    monkeypatch.setattr(service.store, "compiles", raced_selection)
    result = service.prune("p1", keep=1, dry_run=False)
    assert first["compile_id"] not in result["selected_compile_ids"]
    assert service.store.get("p1", first["compile_id"])["pinned"]


def test_token_as_git_username_is_not_returned_in_workspace(service, tmp_path):
    repo = make_repo(tmp_path / "repo")
    git(repo, "remote", "set-url", "origin", "https://secret-as-username@git.overleaf.com/p1")
    with pytest.raises(OverleafError) as error:
        service.bind("p1", str(repo))
    assert "secret-as-username" not in str(error.value)
