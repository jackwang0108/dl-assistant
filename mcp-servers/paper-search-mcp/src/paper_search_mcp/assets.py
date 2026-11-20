"""Validated, bounded downloads. Only URLs discovered for the selected paper are accepted."""

import hashlib
import json
import os
import tarfile
import tempfile
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
import pymupdf

from .identity import normalize_ref, version_from_ref
from .store import digest, now
from .transport import Operation, SourceError


def validate_file(path, kind):
    if kind == "pdf":
        try:
            with pymupdf.open(path) as pdf:
                if not pdf.is_pdf or pdf.page_count < 1 or pdf.needs_pass:
                    raise ValueError("Not a readable PDF")
                return {"pages": pdf.page_count}
        except Exception:
            raise SourceError("invalid_file", "Downloaded file is not a readable PDF") from None
    if kind == "source":
        try:
            with tarfile.open(path, "r:*") as archive:
                for index, _ in enumerate(archive):
                    if index > 10000:
                        raise ValueError("Too many archive entries")
                return {"archive": "tar", "extracted": False}
        except (tarfile.TarError, ValueError):
            raise SourceError(
                "invalid_file", "Source resource is not a validated tar archive"
            ) from None
    raise ValueError("Only pdf/source downloads are supported")


def list_assets(service, paper_ref, version=None, cache="prefer", budget=None):
    ref = normalize_ref(paper_ref)
    version = version or version_from_ref(paper_ref)
    if version and not re.fullmatch(r"v[1-9]\d*", version):
        raise ValueError("version must be an arXiv revision such as v2")
    if version and not ref.startswith("arxiv:"):
        raise ValueError("Explicit revision selection requires an arxiv: paper reference")
    target = ref + version if version else paper_ref
    result = service.get_papers([target], cache=cache, budget=budget)
    paper = result["results"][0]["paper"]
    assets, seen = [], set()
    if paper:
        for value in paper.get("assets", []):
            if version and value.get("version") != version:
                continue
            if value["url"] in seen:
                continue
            seen.add(value["url"])
            item = {
                **value,
                "asset_ref": digest([ref, value["url"], value["type"]]),
                "identity_status": "provider_link_not_content_verified",
            }
            assets.append(item)
    return {
        "paper_ref": ref,
        "requested_version": version,
        "assets": assets,
        "source_reports": result["results"][0]["source_reports"],
        "usage": result["usage"],
        "limitations": [
            "A provider-linked URL does not independently prove the PDF identity or exact version."
        ],
    }


def download(
    service, paper_ref, asset_ref=None, asset_type="pdf", version=None, cache="prefer", budget=None
):
    op = Operation(budget)
    # Asset discovery shares the same operation budget, rather than resetting the counter.
    result = list_assets(service, paper_ref, version, cache="only")
    if not result["assets"] and cache != "only":
        target = normalize_ref(paper_ref) + (version or version_from_ref(paper_ref) or "")
        service.get_papers([target], cache="refresh", _op=op)
        result = list_assets(service, paper_ref, version, cache="only")
    candidates = [
        a
        for a in result["assets"]
        if a["type"] == asset_type and (not asset_ref or a["asset_ref"] == asset_ref)
    ]
    if not candidates:
        return {
            "status": "unavailable",
            "paper_ref": normalize_ref(paper_ref),
            "attempts": [],
            "usage": op.usage(),
            "reason": "No matching discovered asset/version",
        }
    directory = service.store.directory / "assets"
    directory.mkdir(exist_ok=True)
    attempts = []
    for candidate in candidates:
        key = candidate["asset_ref"]
        suffix = ".pdf" if asset_type == "pdf" else ".tar"
        target, meta = directory / (key + suffix), directory / (key + ".json")
        if cache != "refresh" and target.exists() and meta.exists():
            try:
                metadata = json.loads(meta.read_text())
                actual = hashlib.sha256(target.read_bytes()).hexdigest()
                if actual != metadata["sha256"]:
                    raise ValueError("Cache checksum mismatch")
                validation = validate_file(target, asset_type)
                return {
                    **metadata,
                    "status": "cached",
                    "validation": validation,
                    "usage": op.usage(),
                }
            except (ValueError, KeyError, SourceError, OSError):
                attempts.append({"asset_ref": key, "status": "invalid_cache"})
        if cache == "only":
            continue
        temp = None
        try:
            url = candidate["url"]
            with tempfile.NamedTemporaryFile(dir=directory, delete=False) as handle:
                temp = Path(handle.name)
                for redirect in range(6):
                    parsed = urlparse(url)
                    if (
                        parsed.scheme not in ("http", "https")
                        or not parsed.hostname
                        or parsed.username
                    ):
                        raise SourceError("invalid_url", "Unsupported asset URL")
                    op.check()
                    op.requests += 1
                    try:
                        with service.providers.http.client.stream(
                            "GET", url, follow_redirects=False, timeout=min(20.0, op.remaining())
                        ) as response:
                            if response.is_redirect:
                                location = response.headers.get("location")
                                if not location:
                                    raise SourceError("redirect", "Missing redirect location")
                                url = urljoin(url, location)
                                continue
                            if response.status_code >= 400:
                                raise SourceError(
                                    "download_http", f"Download HTTP {response.status_code}"
                                )
                            length = response.headers.get("content-length")
                            if (
                                length
                                and int(length) > op.budget.max_download_bytes - op.download_bytes
                            ):
                                raise SourceError("budget", "Download exceeds byte budget")
                            for chunk in response.iter_bytes():
                                if (
                                    len(chunk) + op.download_bytes > op.budget.max_download_bytes
                                    or not op.remaining()
                                ):
                                    raise SourceError("budget", "Download byte/time budget reached")
                                op.download_bytes += len(chunk)
                                handle.write(chunk)
                            break
                    except httpx.HTTPError:
                        raise SourceError("network", "Download connection failed", True) from None
                else:
                    raise SourceError("redirect", "Too many redirects")
            validation = validate_file(temp, asset_type)
            sha = hashlib.sha256(temp.read_bytes()).hexdigest()
            os.replace(temp, target)
            temp = None
            metadata = {
                "paper_ref": normalize_ref(paper_ref),
                "asset_ref": key,
                "path": str(target),
                "sha256": sha,
                "type": asset_type,
                "source": candidate["source"],
                "source_url": candidate["url"],
                "final_url": url,
                "version": candidate.get("version"),
                "identity_status": "provider_link_not_content_verified",
                "downloaded_at": now(),
                "validation": validation,
            }
            # A metadata-less file is never treated as a complete cached download.
            meta.write_text(json.dumps(metadata, ensure_ascii=False))
            return {**metadata, "status": "downloaded", "attempts": attempts, "usage": op.usage()}
        except (SourceError, ValueError) as exc:
            error = (
                exc.public()
                if isinstance(exc, SourceError)
                else {"kind": "parse", "message": "Invalid download header"}
            )
            attempts.append({"asset_ref": key, "status": "failed", "error": error})
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
    return {"status": "unavailable", "attempts": attempts, "usage": op.usage()}
