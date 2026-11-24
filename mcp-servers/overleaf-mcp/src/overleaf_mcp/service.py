"""Project binding, compile evidence and bounded feedback/artifact operations."""

import hashlib
import io
import json
import time
import re
import shutil
import stat
import uuid
import zipfile
from pathlib import Path

from . import git, render
from .client import Client
from .config import Config
from .credentials import Credential, CredentialStore
from .diagnostics import classify
from .models import OverleafError, checksum, digest, filename, identifier
from .paging import page
from .store import Store

REVIEW_BUNDLE_MAX_BYTES = 100_000_000


def compile_outputs(value):
    if not isinstance(value, list):
        return [], [{"code": "OUTPUT_LIST_INVALID", "message": "Expected a list of build outputs"}]
    outputs, duplicates, seen, issues = [], set(), set(), []
    for index, output in enumerate(value):
        name = output.get("path") if isinstance(output, dict) else None
        if isinstance(name, str):
            try:
                filename(name)
            except OverleafError:
                name = None
        if isinstance(name, str) and name in seen:
            duplicates.add(name)
        if isinstance(name, str):
            seen.add(name)
        if (
            not isinstance(name, str)
            or not isinstance(output.get("url"), str)
            or not output["url"].strip()
        ):
            issues.append({"code": "OUTPUT_ENTRY_INVALID", "index": index})
            continue
        outputs.append(output)
    issues.extend(
        {"code": "OUTPUT_REFERENCE_AMBIGUOUS", "filename": name} for name in sorted(duplicates)
    )
    return [item for item in outputs if item["path"] not in duplicates], issues


class Service:
    def __init__(self, config=None, http=None):
        self.config = config or Config()
        self.credentials = CredentialStore(self.config.credentials_path, self.config.origin)
        self.client = Client(self.config, self.credentials, http)
        self.store = Store(self.config)

    def capabilities(self):
        return {
            "api_version": 2,
            "instance": self.config.base_url,
            "credentials_configured": self.config.credentials_path.is_file(),
            "credential_input": "private local file; secrets are not MCP arguments",
            "git_operations": "read-only worktree inspection; editing/clone/fetch/push stay with caller CLI",
            "git_access": "not established by web session",
            "remote_compile_running_status": "not certified by this web adapter; unknown requests are never silently retried",
            "cdn_origins": sorted(self.config.cdn_origins),
            "coordinate_system": "top_left_pdf_points_xyxy",
            "pages": "1-based",
            "proxy_configured": bool(self.config.proxy),
            "retention": "explicit dry-run/prune; pinned and active requests protected",
        }

    def auth_status(self, verify=False):
        try:
            self.credentials.read()
            if not verify:
                return {"configured": True, "valid": None, "verification": "not_requested"}
            self.client.projects()
            return {"configured": True, "valid": True}
        except OverleafError as error:
            return {
                "configured": error.code != "AUTH_MISSING",
                "valid": False
                if error.code
                in ("AUTH_MISSING", "AUTH_EXPIRED", "AUTH_FILE_INVALID", "AUTH_INSTANCE_MISMATCH")
                else None,
                "error": error.result()["error"],
            }

    def import_auth(self, path):
        candidate = self.credentials.read(Path(path).expanduser())
        csrf = self.client.csrf(candidate)
        candidate = Credential(candidate.cookie, csrf, candidate.origin)
        projects = self.client.projects(candidate)
        self.credentials.save(candidate)
        return {
            "validated": True,
            "projects_visible": len(projects),
            "credential_path": str(self.credentials.path),
            "secret_values_returned": False,
        }

    def projects(self, cursor=None, max_chars=24000):
        records = (
            None
            if cursor
            else [
                {k: p.get(k) for k in ("id", "name", "lastUpdated", "archived", "trashed")}
                for p in self.client.projects()
            ]
        )
        return page(self.store, ["projects"], records, cursor, max_chars)

    def create_project(self, name, template="none"):
        if not name.strip() or len(name) > 200 or template not in ("none", "example"):
            raise OverleafError("INVALID_INPUT", "Use a project name and template none/example")
        response = self.client.json(
            "POST", "project/new", {"projectName": name, "template": template}
        )
        ident = response.get("project_id")
        if not isinstance(ident, str):
            raise OverleafError(
                "REQUEST_OUTCOME_UNKNOWN",
                "Creation response lacks project_id; check the project list before retrying",
            )
        identifier(ident)
        return {"project_id": ident, "name": name, "template": template}

    def delete_project(self, project_id, expected_name):
        identifier(project_id)
        project = next((p for p in self.client.projects() if p["id"] == project_id), None)
        if not project or project["name"] != expected_name:
            raise OverleafError(
                "PROJECT_CONFIRMATION_MISMATCH",
                "Current project ID/name does not match the explicitly selected deletion target",
            )
        self.client.request("DELETE", f"project/{project_id}")
        return {
            "project_id": project_id,
            "remote_delete_requested": True,
            "local_evidence_preserved": True,
        }

    def files(self, project_id, cursor=None, max_chars=24000):
        identifier(project_id)
        records = None
        if not cursor:
            response = self.client.json("GET", f"project/{project_id}/entities")
            records = response.get("entities")
            if not isinstance(records, list):
                raise OverleafError(
                    "API_SCHEMA", "File-tree response changed; empty content was not assumed"
                )
        return page(self.store, ["files", project_id], records, cursor, max_chars)

    def settings(self, project_id, compiler=None, root_doc_id=None, spell_check_language=None):
        identifier(project_id)
        changes = {}
        if compiler:
            if compiler not in ("latex", "pdflatex", "xelatex", "lualatex"):
                raise OverleafError("INVALID_COMPILER", "Unsupported compiler choice")
            changes["compiler"] = compiler
        if root_doc_id:
            changes["rootDocId"] = identifier(root_doc_id)
        if spell_check_language:
            if len(spell_check_language) > 50:
                raise OverleafError("INVALID_INPUT", "Language code is too long")
            changes["spellCheckLanguage"] = spell_check_language
        if changes:
            self.client.request("POST", f"project/{project_id}/settings", changes)
        return {"project_id": project_id, "applied": changes}

    def bind(self, project_id, repo_dir, remote="origin", remote_branch="main"):
        value = git.inspect(repo_dir, project_id, self.config.base_url, remote, remote_branch)
        binding = {
            k: value[k] for k in ("project_id", "repo_dir", "remote", "remote_branch", "git_url")
        }
        self.store.binding(project_id, binding)
        return {
            **binding,
            "head": value["head"],
            "dirty": value["dirty"],
            "tracking_head": value["tracking_head"],
            "remote_verification": "local_tracking_ref_only",
        }

    def workspace(self, project_id):
        value = self.store.binding(project_id)
        if not value:
            return {
                "project_id": identifier(project_id),
                "binding": None,
                "instruction": "Bind the existing user-visible Git repository; no hidden clone was created",
            }
        return git.inspect(
            value["repo_dir"],
            project_id,
            self.config.base_url,
            value["remote"],
            value["remote_branch"],
        )

    def source(self, project_id, expected_commit=None):
        value = self.workspace(project_id)
        if expected_commit:
            if not re.fullmatch(r"[a-f0-9]{40,64}", expected_commit):
                raise OverleafError("INVALID_COMMIT", "Supply the full expected commit hash")
            if (
                value.get("head") != expected_commit
                or value.get("dirty")
                or value.get("manifest_partial")
                or value.get("symlinks")
            ):
                raise OverleafError(
                    "SOURCE_NOT_READY",
                    "Bound worktree does not exactly match the clean expected local commit",
                )
        return {
            **value,
            "expected_commit": expected_commit,
            "binding_status": "unverified_compiled_revision",
            "note": "Local Git and history observations do not establish atomic compilation of that commit",
        }

    def observe_history(self, project_id):
        try:
            response = self.client.json("GET", f"project/{project_id}/updates?min_count=1")
            updates = response.get("updates") if isinstance(response, dict) else None
            if not isinstance(updates, list):
                raise OverleafError("API_SCHEMA", "History response lacks updates")
            first = updates[0] if updates else None
            return {
                "status": "observed",
                "latest_update_sha256": digest(first),
                "reported_version": first.get("toV", first.get("version"))
                if isinstance(first, dict)
                else None,
            }
        except OverleafError as error:
            return {"status": "unavailable", "error": error.result()["error"]}

    def summary(self, record, *, verify_pdf=True):
        item = record.get("outputs", {}).get("output.pdf")
        if verify_pdf or not item:
            artifact = self.store.artifact_status(record, "output.pdf")
        else:
            artifact = {
                "status": "not_checked",
                "recorded_validation": item.get("validation"),
                "sha256": item["sha256"],
            }
        result = {
            k: record.get(k)
            for k in (
                "compile_id",
                "project_id",
                "created_ns",
                "state",
                "classification",
                "raw_status",
                "error",
                "pinned",
                "source_binding",
                "remote_build_ids",
                "output_list_status",
            )
        } | {
            "pdf_status": artifact.get("recorded_validation")
            if artifact["status"] == "verified"
            else artifact["status"],
            "pdf_artifact": artifact,
            "diagnostics_count": len(record.get("diagnostics", [])),
        }
        if result["error"] is None:
            result.pop("error")
        result["pinned"] = bool(result["pinned"])
        return result

    def compile(
        self,
        project_id,
        root_resource_path=None,
        draft=False,
        stop_on_first_error=False,
        expected_commit=None,
        retry_unknown=False,
    ):
        identifier(project_id)
        if root_resource_path and (
            len(root_resource_path) > 1024
            or Path(root_resource_path).is_absolute()
            or ".." in Path(root_resource_path).parts
        ):
            raise OverleafError("INVALID_INPUT", "Root resource must be a project-relative path")
        self.credentials.read()
        source = self.source(project_id, expected_commit)
        source["remote_before"] = self.observe_history(project_id)
        record = self.store.reserve(project_id, source, retry_unknown, self.config.compile_timeout)
        ident = record["compile_id"]
        self.store.directory(project_id, ident)
        options = {
            "draft": draft,
            "stopOnFirstError": stop_on_first_error,
            "check": "silent",
            "incrementalCompilesEnabled": True,
        }
        if root_resource_path is not None:
            options["rootResourcePath"] = root_resource_path
        self.store.patch(
            project_id,
            ident,
            {
                "options": options,
                "request_deadline_ns": time.time_ns()
                + int(self.config.compile_timeout * 1_000_000_000),
            },
        )
        try:
            response = self.client.json(
                "POST",
                f"project/{project_id}/compile?auto_compile=true",
                options,
                timeout=self.config.compile_timeout,
            )
            if (
                not isinstance(response, dict)
                or not isinstance(response.get("status"), str)
                or not response["status"].strip()
            ):
                raise OverleafError(
                    "REQUEST_OUTCOME_UNKNOWN",
                    "Compile response schema changed; do not blindly trigger another compile",
                )
        except OverleafError as error:
            unknown = error.code in ("REQUEST_OUTCOME_UNKNOWN", "API_SCHEMA", "DOWNLOAD_LIMIT")
            record = self.store.patch(
                project_id,
                ident,
                {
                    "state": "outcome_unknown" if unknown else "failed",
                    "error": error.result()["error"],
                    "classification": "unknown" if unknown else "failed",
                },
                release=not unknown,
            )
            return self.summary(record)
        outputs, issues = compile_outputs(response.get("outputFiles"))
        response = {**response, "outputFiles": outputs}
        manifest_status = "partial" if issues else "reported"
        build_ids = sorted(
            {
                match[1]
                for output in response["outputFiles"]
                if isinstance(output, dict)
                and isinstance(output.get("url"), str)
                and (match := re.search(r"/build/([^/]+)/", output["url"]))
            }
        )
        self.store.patch(
            project_id,
            ident,
            {
                "response": response,
                "raw_status": response["status"],
                "remote_build_ids": build_ids,
                "output_list_status": manifest_status,
                "artifact_issues": issues,
            },
        )
        for name in ("output.log", "output.stderr", "output.blg"):
            if not any(f.get("path") == name for f in response["outputFiles"]):
                if name == "output.log":
                    issues.append(
                        {
                            "code": "LOG_UNAVAILABLE",
                            "message": "Build response did not include output.log",
                        }
                    )
                continue
            try:
                self.download(project_id, name, ident)
            except OverleafError as error:
                issues.append(
                    {
                        "code": "ARTIFACT_UNAVAILABLE",
                        "filename": name,
                        "error": error.result()["error"],
                    }
                )
            except (OSError, ValueError, TypeError) as error:
                issues.append(
                    {
                        "code": "ARTIFACT_UNAVAILABLE",
                        "filename": name,
                        "error": {
                            "code": "LOCAL_OR_INVALID_OUTPUT",
                            "reason": type(error).__name__,
                        },
                    }
                )
        after = self.observe_history(project_id)
        binding = (
            "concurrent_remote_change_observed"
            if source["remote_before"].get("status") == "observed"
            and after.get("status") == "observed"
            and source["remote_before"]["latest_update_sha256"] != after["latest_update_sha256"]
            else "compiled_revision_not_certified"
        )
        self.store.patch(
            project_id,
            ident,
            {
                "artifact_issues": issues,
                "remote_after": after,
                "source_binding": binding,
                "state": "completed",
            },
            release=True,
        )
        record = self.reclassify(project_id, ident)
        return self.summary(record)

    def reclassify(self, project_id, ident):
        record = self.store.get(project_id, ident)
        texts = {}
        for name in ("output.log", "output.stderr", "output.blg"):
            item = self.store.verify_output(record, name)
            texts[name] = (
                Path(item["path"]).read_text(encoding="utf-8", errors="replace") if item else None
            )
        classification, diagnostics = classify(
            record.get("response") or {},
            texts["output.log"],
            texts["output.stderr"],
            texts["output.blg"],
        )
        if classification == "clean" and (
            record.get("output_list_status") == "partial" or record.get("artifact_issues")
        ):
            classification = "unknown"
        return self.store.patch(
            project_id, ident, {"classification": classification, "diagnostics": diagnostics}
        )

    def download(self, project_id, name, compile_id=None):
        filename(name)
        record = self.store.get(project_id, compile_id)
        cached = self.store.verify_output(record, name)
        if cached:
            return {
                "compile_id": record["compile_id"],
                "filename": name,
                **cached,
                "cache_state": "hit",
            }
        if name in record.get("outputs", {}):
            raise OverleafError(
                "ARTIFACT_CHANGED",
                "Saved artifact is missing or modified; its original evidence was not silently replaced",
            )
        if not record.get("response"):
            raise OverleafError(
                "OUTPUT_NOT_AVAILABLE",
                "This request has no confirmed output references; its remote outcome may be unknown",
            )
        data = self.client.outputs(record["response"], name, project_id=project_id)
        details = (
            render.validate_pdf(data) if name.lower().endswith(".pdf") else {"format_valid": None}
        )
        target = self.store.directory(project_id, record["compile_id"]) / name
        self.store.write(target, data)
        item = {
            "sha256": checksum(target),
            "bytes": len(data),
            "validation": "pdf_readable"
            if name.lower().endswith(".pdf")
            else "downloaded_bytes_uninterpreted",
            **details,
        }
        self.store.output(project_id, record["compile_id"], name, item)
        return {
            "compile_id": record["compile_id"],
            "filename": name,
            "path": str(target),
            **item,
            "cache_state": "miss",
        }

    def report(self, project_id, compile_id=None, cursor=None, max_chars=24000):
        record = self.store.get(project_id, compile_id)
        records = None
        if not cursor:
            records = (
                [
                    {"kind": "summary", **self.summary(record)},
                    {
                        "kind": "source_evidence",
                        "source": record.get("source"),
                        "remote_after": record.get("remote_after"),
                        "options": record.get("options"),
                    },
                    {"kind": "artifact_issues", "items": record.get("artifact_issues", [])},
                ]
                + [{"kind": "diagnostic", **d} for d in record.get("diagnostics", [])]
                + [
                    {
                        "kind": "output",
                        "filename": name,
                        **value,
                        **self.store.artifact_status(record, name),
                    }
                    for name, value in record.get("outputs", {}).items()
                ]
            )
        return page(
            self.store, ["report", project_id, record["compile_id"]], records, cursor, max_chars
        )

    def export_review_bundle(self, project_id, compile_id, pages=None, dpi=150):
        identifier(compile_id)
        if not 36 <= dpi <= 400:
            raise OverleafError("INVALID_DPI", "DPI must be 36–400")
        record = self.store.get(project_id, compile_id)
        summary = self.summary(record)
        artifact = summary.pop("pdf_artifact")
        artifact_path = artifact.pop("path", None)
        source = record.get("source", {})
        report = {
            "schema_version": 1,
            "summary": summary,
            "source_evidence": {
                k: source[k]
                for k in (
                    "binding",
                    "head",
                    "expected_commit",
                    "dirty",
                    "tracking_head",
                    "tracking_head_freshness",
                    "source_manifest",
                    "manifest_sha256",
                    "manifest_partial",
                    "symlinks",
                    "remote_before",
                    "binding_status",
                    "note",
                )
                if k in source
            },
            "remote_after": record.get("remote_after"),
            "compile_options": record.get("options"),
            "artifact_issues": record.get("artifact_issues", []),
            "diagnostics": record.get("diagnostics", []),
            "logged_artifacts": {
                name: {
                    k: v for k, v in self.store.artifact_status(record, name).items() if k != "path"
                }
                for name in record.get("outputs", {})
                if name != "output.pdf"
            },
            "pdf": artifact,
            "screenshots": {"requested_pages": pages, "status": "not_requested", "items": []},
        }
        images = []
        if pages is not None:
            if artifact_path is None:
                report["screenshots"]["status"] = "verified_pdf_required"
            else:
                images = render.render(self.store, record, artifact_path, pages, dpi=dpi)
                if not self.store.verify_output(record, "output.pdf"):
                    raise OverleafError(
                        "ARTIFACT_CHANGED", "PDF changed while generating screenshots"
                    )
                report["screenshots"]["status"] = "included"
                report["screenshots"]["items"] = [
                    {**image, "path": f"pages/page-{image['page']}.png"} for image in images
                ]

        encoded = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True).encode()
        size = len(encoded)
        if size > REVIEW_BUNDLE_MAX_BYTES:
            raise OverleafError(
                "REVIEW_BUNDLE_LIMIT", "Compile evidence exceeds the bundle size limit"
            )
        bundle = io.BytesIO()
        with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                zipfile.ZipInfo("review.json"), encoded, compress_type=zipfile.ZIP_DEFLATED
            )
            for image, entry in zip(images, report["screenshots"]["items"], strict=True):
                with Path(image["path"]).open("rb") as stream:
                    contents = stream.read(REVIEW_BUNDLE_MAX_BYTES - size + 1)
                size += len(contents)
                if size > REVIEW_BUNDLE_MAX_BYTES:
                    raise OverleafError("REVIEW_BUNDLE_LIMIT", "Select fewer pages or lower DPI")
                if hashlib.sha256(contents).hexdigest() != image["sha256"]:
                    raise OverleafError(
                        "ARTIFACT_CHANGED", "Screenshot changed while saving the bundle"
                    )
                archive.writestr(zipfile.ZipInfo(entry["path"]), contents)
        data = bundle.getvalue()
        sha256 = hashlib.sha256(data).hexdigest()
        path = self.store.directory(project_id, compile_id) / f"review-{sha256}.zip"
        self.store.write(path, data)
        return {
            "compile_id": compile_id,
            "path": str(path),
            "sha256": sha256,
            "bytes": len(data),
            "pdf_status": artifact["status"],
            "screenshots_status": report["screenshots"]["status"],
            "pages": [image["page"] for image in images],
        }

    def status(self, project_id, compile_id=None):
        record = self.store.get(project_id, compile_id)
        if record["state"] == "requested" and time.time_ns() > record.get(
            "request_deadline_ns", 2**63 - 1
        ):
            if record.get("response"):
                issues = record.get("artifact_issues", []) + [
                    {
                        "code": "FINALIZATION_INTERRUPTED",
                        "message": "Recorded server result; local evidence collection was interrupted",
                    }
                ]
                self.store.patch(
                    project_id,
                    record["compile_id"],
                    {
                        "state": "completed",
                        "artifact_issues": issues,
                        "source_binding": record.get("source_binding")
                        or "compiled_revision_not_certified",
                    },
                    release=True,
                )
                record = self.reclassify(project_id, record["compile_id"])
            else:
                record = self.store.patch(
                    project_id,
                    record["compile_id"],
                    {
                        "state": "outcome_unknown",
                        "error": {
                            "code": "REQUEST_INTERRUPTED",
                            "message": "The local request deadline passed without a recorded server response",
                        },
                    },
                )
        return {
            **self.summary(record),
            "remote_running_state": "not_certified",
            "retry_policy": "Unknown requests are not automatically retried; retry_unknown is an explicit caller decision after checking Overleaf",
        }

    def read_log(
        self,
        project_id,
        compile_id=None,
        stream="output.log",
        start_line=1,
        end_line=None,
        cursor=None,
        max_chars=24000,
    ):
        if stream not in ("output.log", "output.stderr", "output.blg", "output.stdout"):
            raise OverleafError("INVALID_STREAM", "Select a supported compile log stream")
        record = self.store.get(project_id, compile_id)
        records = None
        if not cursor:
            item = self.store.verify_output(record, stream)
            if not item:
                raise OverleafError("LOG_UNAVAILABLE", "Download and verify this log first")
            lines = Path(item["path"]).read_text(encoding="utf-8", errors="replace").splitlines()
            if not lines:
                if start_line != 1 or end_line not in (None, 0):
                    raise OverleafError("INVALID_LINES", "Empty stream has no requested line range")
                return page(
                    self.store,
                    ["log", project_id, record["compile_id"], stream, start_line, end_line],
                    [{"kind": "log_status", "stream": stream, "lines": 0}],
                    None,
                    max_chars,
                )
            last = end_line if end_line is not None else len(lines)
            if not 1 <= start_line <= max(len(lines), 1) or last < start_line or last > len(lines):
                raise OverleafError("INVALID_LINES", "Log line range is outside the saved stream")
            records = [
                {"stream": stream, "line": i + 1, "text": lines[i]}
                for i in range(start_line - 1, last)
            ]
        return page(
            self.store,
            ["log", project_id, record["compile_id"], stream, start_line, end_line],
            records,
            cursor,
            max_chars,
        )

    def render(
        self, project_id, compile_id, pages, dpi=150, bbox=None, cursor=None, max_chars=24000
    ):
        record = self.store.get(project_id, compile_id)
        records = None
        if not cursor:
            pdf = self.store.verify_output(record, "output.pdf")
            if not pdf:
                raise OverleafError(
                    "PDF_NOT_READY", "Download and verify this build PDF before rendering"
                )
            records = render.render(self.store, record, pdf["path"], pages, dpi, bbox)
        return page(
            self.store,
            ["render", project_id, record["compile_id"], pages, dpi, bbox],
            records,
            cursor,
            max_chars,
        )

    def compare(self, project_id, left_id, right_id, pages="1", cursor=None, max_chars=24000):
        left = self.store.get(project_id, left_id)
        right = self.store.get(project_id, right_id)
        records = None
        if not cursor:
            binding = self.store.binding(project_id)
            records = [
                {
                    "kind": "source_diff",
                    **git.changed_files(
                        binding,
                        left.get("source", {}).get("head"),
                        right.get("source", {}).get("head"),
                    ),
                },
                {
                    "kind": "diagnostic_change",
                    "left": left.get("diagnostics", []),
                    "right": right.get("diagnostics", []),
                },
            ]
            a = self.store.verify_output(left, "output.pdf")
            b = self.store.verify_output(right, "output.pdf")
            if a and b:
                records.extend(render.compare(self.store, left, right, a["path"], b["path"], pages))
            else:
                records.append(
                    {"kind": "visual_comparison", "status": "both_verified_pdfs_required"}
                )
        return page(
            self.store,
            ["compare", project_id, left_id, right_id, pages],
            records,
            cursor,
            max_chars,
        )

    def prune(self, project_id, keep=10, dry_run=True):
        if not 1 <= keep <= 1000:
            raise OverleafError("INVALID_RETENTION", "keep must be 1–1000")
        all_records = self.store.compiles(project_id)
        candidates = [
            r
            for r in all_records[keep:]
            if not r["pinned"] and r["state"] in ("completed", "failed")
        ]
        if len(candidates) > 1000:
            raise OverleafError(
                "RETENTION_LIMIT", "Prune at most 1000 records per explicit operation"
            )
        if not dry_run:
            removed = []
            for record in candidates:
                with self.store.db() as db:
                    db.execute("BEGIN IMMEDIATE")
                    current = db.execute(
                        "SELECT payload,pinned FROM compiles WHERE id=? AND project=?",
                        (record["compile_id"], project_id),
                    ).fetchone()
                    if (
                        not current
                        or current[1]
                        or json.loads(current[0])["state"] not in ("completed", "failed")
                    ):
                        continue
                    directory = self.store.directory(project_id, record["compile_id"], create=False)
                    if directory.exists():
                        shutil.rmtree(directory)
                    db.execute(
                        "DELETE FROM compiles WHERE id=? AND project=?",
                        (record["compile_id"], project_id),
                    )
                    removed.append(record)
            candidates = removed
        return {
            "dry_run": dry_run,
            "selected_compile_ids": [r["compile_id"] for r in candidates],
            "kept_pinned_and_active": True,
        }

    def threads(self, project_id, cursor=None, max_chars=24000):
        identifier(project_id)
        records = None
        if not cursor:
            before = self.observe_history(project_id)
            value = self.client.json("GET", f"project/{project_id}/threads")
            if not isinstance(value, dict) or any(not isinstance(v, dict) for v in value.values()):
                raise OverleafError("API_SCHEMA", "Comment thread response changed")
            after = self.observe_history(project_id)
            records = [
                {
                    "kind": "feedback_context",
                    "before": before,
                    "after": after,
                    "binding": "reported_anchors_not_certified_current_local_positions",
                }
            ] + [{"kind": "thread", "thread_id": k, **v} for k, v in value.items()]
        return page(self.store, ["threads", project_id], records, cursor, max_chars)

    def history(self, project_id, before_timestamp=None, max_pages=1, cursor=None, max_chars=24000):
        identifier(project_id)
        if not 1 <= max_pages <= 5:
            raise OverleafError("INVALID_BUDGET", "History max_pages must be 1–5")
        records = None
        if not cursor:
            updates = []
            next_before = before_timestamp
            seen_cursors = {before_timestamp} if before_timestamp is not None else set()
            seen_updates = set()
            known_more = None
            for _ in range(max_pages):
                params = {"min_count": 50}
                if next_before is not None:
                    params["beforeTimestamp"] = next_before
                query = "&".join(f"{k}={int(v)}" for k, v in params.items())
                data = self.client.json("GET", f"project/{project_id}/updates?" + query)
                if not isinstance(data.get("updates"), list):
                    raise OverleafError("API_SCHEMA", "History response lacks updates")
                for update in data["updates"]:
                    key = digest(update)
                    if key not in seen_updates:
                        updates.append(update)
                        seen_updates.add(key)
                known_more = (
                    bool(data.get("nextBeforeTimestamp")) if "nextBeforeTimestamp" in data else None
                )
                next_before = data.get("nextBeforeTimestamp")
                if not next_before:
                    break
                if next_before in seen_cursors:
                    raise OverleafError(
                        "HISTORY_CURSOR_STALLED", "History cursor repeated; fetching stopped"
                    )
                seen_cursors.add(next_before)
            records = [
                {
                    "kind": "coverage",
                    "upstream_has_more": known_more,
                    "next_before_timestamp": next_before,
                }
            ] + [{"kind": "update", "data": u} for u in updates]
        return page(
            self.store,
            ["history", project_id, before_timestamp, max_pages],
            records,
            cursor,
            max_chars,
        )

    def labels(self, project_id, cursor=None, max_chars=24000):
        identifier(project_id)
        records = None
        if not cursor:
            records = self.client.json("GET", f"project/{project_id}/labels")
            if not isinstance(records, list):
                raise OverleafError("API_SCHEMA", "Version label response is not a list")
        return page(self.store, ["labels", project_id], records, cursor, max_chars)

    def snapshot(self, project_id, version):
        identifier(project_id)
        if not 0 <= version <= 1_000_000_000:
            raise OverleafError("INVALID_VERSION", "Use a nonnegative history version")
        data = self.client.request(
            "GET", f"project/{project_id}/version/{version}/zip", output=True
        )
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                entries = archive.infolist()
                if len(entries) > 10000 or sum(e.file_size for e in entries) > 500_000_000:
                    raise OverleafError(
                        "ARCHIVE_LIMIT", "Snapshot archive exceeds file/expanded-size limits"
                    )
                for e in entries:
                    if (
                        Path(e.filename).is_absolute()
                        or ".." in Path(e.filename).parts
                        or stat.S_ISLNK(e.external_attr >> 16)
                        or e.flag_bits & 1
                    ):
                        raise OverleafError(
                            "INVALID_ARCHIVE", "Snapshot contains unsafe or encrypted entries"
                        )
                if archive.testzip():
                    raise OverleafError(
                        "INVALID_ARCHIVE", "Snapshot archive failed integrity checks"
                    )
        except zipfile.BadZipFile:
            raise OverleafError(
                "INVALID_ARCHIVE", "Remote response is not a valid ZIP snapshot"
            ) from None
        folder = self.store.directory(project_id, "snapshot-" + uuid.uuid4().hex)
        target = folder / f"version-{version}.zip"
        self.store.write(target, data)
        return {
            "project_id": project_id,
            "version": version,
            "path": str(target),
            "sha256": checksum(target),
            "bytes": len(data),
            "entries": len(entries),
            "extracted": False,
        }
