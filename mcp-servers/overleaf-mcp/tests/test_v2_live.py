"""Explicit live tests; mutate only a uniquely named dedicated test project."""

import hashlib
import json
import os
import uuid
import zipfile
from pathlib import Path

import pytest

from overleaf_mcp.config import Config
from overleaf_mcp.service import Service

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.getenv("OVERLEAF_RUN_LIVE") != "1",
        reason="Set OVERLEAF_RUN_LIVE=1 with a private configured session",
    ),
]


def test_dedicated_project_compile_artifacts_feedback_and_cleanup(tmp_path):
    real = Config()
    config = Config(
        home=tmp_path,
        base_url=real.base_url,
        proxy=os.getenv("OVERLEAF_PROXY_URL", "http://127.0.0.1:7890"),
    )
    config.credentials_path = real.credentials_path
    service = Service(config)
    assert service.auth_status(verify=True)["valid"] is True
    name = "overleaf-mcp-v2-test-" + uuid.uuid4().hex[:12]
    project = None
    result = {"dedicated_project_name": name, "deleted": False}
    try:
        project = service.create_project(name, "example")["project_id"]
        result["project_id"] = project
        failed = service.compile(project, root_resource_path="mcp-missing-document.tex")
        result["missing_root_classification"] = failed["classification"]
        assert failed["classification"] == "failed"
        failed_bundle = service.export_review_bundle(project, failed["compile_id"], pages="1")
        assert failed_bundle["screenshots_status"] == "verified_pdf_required"
        with zipfile.ZipFile(failed_bundle["path"]) as archive:
            failed_report = json.loads(archive.read("review.json"))
            assert failed_report["summary"]["classification"] == "failed"
            assert archive.namelist() == ["review.json"]
        clean = service.compile(project)
        assert clean["state"] == "completed" and clean["classification"] in ("clean", "warnings")
        pdf = service.download(project, "output.pdf", clean["compile_id"])
        assert pdf["format_valid"] and pdf["pages"] > 0
        image = service.render(project, clean["compile_id"], "1", dpi=72)["items"][0]
        assert Path(image["path"]).is_file()
        newer = service.compile(project)
        service.download(project, "output.pdf", clean["compile_id"])
        assert service.status(project)["compile_id"] == newer["compile_id"]
        bundle = service.export_review_bundle(project, clean["compile_id"], pages="1", dpi=72)
        assert bundle["screenshots_status"] == "included"
        assert hashlib.sha256(Path(bundle["path"]).read_bytes()).hexdigest() == bundle["sha256"]
        with zipfile.ZipFile(bundle["path"]) as archive:
            report = json.loads(archive.read("review.json"))
            assert report["summary"]["compile_id"] == clean["compile_id"]
            assert report["summary"]["source_binding"] == clean["source_binding"]
            assert (
                report["pdf"]["sha256"] == pdf["sha256"] and report["pdf"]["status"] == "verified"
            )
            screenshot = report["screenshots"]["items"][0]
            assert screenshot["sha256"] == image["sha256"]
            assert hashlib.sha256(archive.read(screenshot["path"])).hexdigest() == image["sha256"]
        assert service.status(project)["compile_id"] == newer["compile_id"]
        assert service.read_log(project, clean["compile_id"])["items"]
        assert service.files(project)["items"]
        assert service.threads(project)["items"][0]["kind"] == "feedback_context"
        history = service.history(project)["items"]
        assert history[0]["kind"] == "coverage"
        service.labels(project)
        versions = [
            item["data"].get("toV") for item in history[1:] if isinstance(item.get("data"), dict)
        ]
        version = next((v for v in versions if isinstance(v, int) and v >= 0), None)
        if version is not None:
            snapshot = service.snapshot(project, version)
            assert Path(snapshot["path"]).is_file()
            result["version_snapshot_verified"] = True
        result.update(
            compile_classification=clean["classification"],
            pdf_pages=pdf["pages"],
            render_verified=True,
            review_bundle_verified=True,
            failed_review_bundle_without_screenshot=True,
            old_download_preserves_latest=True,
            source_binding=clean["source_binding"],
        )
    finally:
        if project:
            assert name.startswith("overleaf-mcp-v2-test-")
            service.delete_project(project, name)
            result["deleted"] = True
            listed = service.client.projects()
            assert all(p["id"] != project for p in listed)
            result["absent_from_projects_after_cleanup"] = True
        path = os.getenv("OVERLEAF_LIVE_REPORT")
        if path:
            Path(path).write_text(json.dumps(result, indent=2))
