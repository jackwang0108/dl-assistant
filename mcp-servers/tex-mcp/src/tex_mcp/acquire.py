"""Bounded source acquisition. No archive links, no writes outside a staging directory."""

import gzip
import hashlib
import io
import re
import tarfile
import threading
import time
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

import httpx

from .models import Limits, TexError

_LOCK = threading.Lock()
_LAST = 0.0


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def contained(root, relative):
    root = Path(root).resolve()
    relative = Path(relative)
    if relative.is_absolute():
        raise TexError("UNSAFE_PATH", "Source references must be relative", path=str(relative))
    candidate = root / relative
    try:
        candidate.resolve().relative_to(root)
    except ValueError:
        raise TexError("UNSAFE_PATH", "Path escapes source snapshot", path=str(relative)) from None
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise TexError("UNSAFE_PATH", "Source symlinks are not accepted", path=str(relative))
    return candidate.resolve()


def arxiv_ref(source):
    value = source.strip()
    if value.startswith(("http://", "https://")):
        parsed = urlparse(value)
        if parsed.hostname not in ("arxiv.org", "www.arxiv.org", "export.arxiv.org"):
            raise TexError("INVALID_SOURCE", "Only arXiv URLs and local directories are supported")
        value = re.sub(r"^/(?:abs|pdf|e-print|src)/", "", parsed.path)
        value = re.sub(r"\.pdf$", "", value).rstrip("/")
    value = value.removeprefix("arxiv:")
    match = re.fullmatch(r"(\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(v[1-9]\d*)?", value)
    if not match:
        raise TexError("INVALID_SOURCE", "Invalid arXiv identifier")
    return match.group(1), match.group(2)


class Acquisition:
    def __init__(self, limits=None, client=None, interval=3.0):
        self.limits = limits or Limits()
        self.client = client or httpx.Client(follow_redirects=False)
        self.interval = interval
        self.started = time.monotonic()
        self.requests = self.download_bytes = self.source_bytes = self.file_count = 0

    def check(self):
        remaining = self.limits.max_seconds - (time.monotonic() - self.started)
        if remaining <= 0:
            raise TexError("BUDGET", "Operation time budget reached")
        return remaining

    def usage(self):
        return {
            "requests": self.requests,
            "download_bytes": self.download_bytes,
            "source_bytes": self.source_bytes,
            "files": self.file_count,
            "seconds": round(time.monotonic() - self.started, 3),
        }

    def get(self, url):
        global _LAST
        for attempt in range(3):
            self.check()
            if self.requests >= self.limits.max_requests:
                raise TexError("BUDGET", "Request budget reached")
            if not _LOCK.acquire(timeout=self.check()):
                raise TexError("BUDGET", "Request queue wait exceeded budget")
            try:
                delay = max(0.0, _LAST + self.interval - time.monotonic())
                if delay >= self.check():
                    raise TexError("BUDGET", "Rate-limit wait exceeded budget")
                time.sleep(delay)
                self.requests += 1
                with self.client.stream(
                    "GET",
                    url,
                    timeout=min(25.0, self.check()),
                    headers={"User-Agent": "tex-mcp/0.2"},
                    follow_redirects=False,
                ) as r:
                    if r.is_redirect:
                        from urllib.parse import urljoin

                        url = urljoin(url, r.headers.get("location", ""))
                        if not url.startswith("https://"):
                            raise TexError("FETCH_FAILED", "Unexpected redirect protocol")
                        continue
                    if (r.status_code == 429 or r.status_code >= 500) and attempt < 2:
                        continue
                    if r.status_code != 200:
                        raise TexError(
                            "FETCH_FAILED",
                            f"Upstream HTTP {r.status_code}",
                            status_code=r.status_code,
                        )
                    data = bytearray()
                    for chunk in r.iter_bytes():
                        self.check()
                        self.download_bytes += len(chunk)
                        if self.download_bytes > self.limits.max_download_bytes:
                            raise TexError("BUDGET", "Download byte budget reached")
                        data.extend(chunk)
                    return bytes(data)
            except httpx.HTTPError:
                if attempt == 2:
                    raise TexError("FETCH_FAILED", "Upstream connection failed") from None
            finally:
                _LAST = time.monotonic()
                _LOCK.release()
        raise TexError("FETCH_FAILED", "Download retries/redirects exhausted")

    def write(self, root, name, stream):
        path = contained(root, name)
        self.file_count += 1
        if self.file_count > self.limits.max_files:
            raise TexError("BUDGET", "Source file count exceeded")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as output:
            while True:
                self.check()
                chunk = stream.read(65536)
                if not chunk:
                    break
                self.source_bytes += len(chunk)
                if self.source_bytes > self.limits.max_source_bytes:
                    raise TexError("BUDGET", "Expanded source byte budget exceeded")
                output.write(chunk)

    def unpack(self, data, root):
        if data.lstrip().startswith(b"%PDF"):
            raise TexError("NO_SOURCE", "Submission contains PDF rather than TeX source")
        try:
            archive = tarfile.open(fileobj=io.BytesIO(data), mode="r:*")  # noqa: SIM115 - ownership passed to with archive below
        except tarfile.ReadError:
            archive = None
        if archive:
            with archive:
                for member in archive:
                    self.check()
                    if Path(member.name).is_absolute() or ".." in Path(member.name).parts:
                        raise TexError("UNSAFE_ARCHIVE", "Archive path traversal rejected")
                    contained(root, member.name)
                    if member.isdir():
                        continue
                    if not member.isfile() or member.issym() or member.islnk():
                        raise TexError(
                            "UNSAFE_ARCHIVE",
                            "Only ordinary source files are accepted",
                            name=member.name,
                        )
                    if member.size + self.source_bytes > self.limits.max_source_bytes:
                        raise TexError("BUDGET", "Archive declares excessive expanded size")
                    self.write(root, member.name, archive.extractfile(member))
        else:
            stream = (
                gzip.GzipFile(fileobj=io.BytesIO(data))
                if data[:2] == b"\x1f\x8b"
                else io.BytesIO(data)
            )
            self.write(root, "main.tex", stream)
            sample = (root / "main.tex").read_bytes()
            if b"\\documentclass" not in sample or b"<html" in sample[:500].lower():
                raise TexError("INVALID_CONTENT", "Response is not a recognized TeX submission")

    def acquire(self, source, root, metadata=None):
        local = Path(source).expanduser()
        if local.is_dir():
            source_root = local.resolve()
            for path in sorted(source_root.rglob("*")):
                relative = path.relative_to(source_root)
                if any(part.startswith(".") for part in relative.parts):
                    continue
                if path.is_symlink():
                    raise TexError(
                        "UNSAFE_PATH", "Local source contains a symlink", path=str(relative)
                    )
                if path.is_file():
                    with path.open("rb") as stream:
                        self.write(root, relative, stream)
            return {"kind": "local", "source": str(source_root), "actual_version": None}
        metadata = metadata or self.resolve_arxiv(source)
        ident, version = metadata["arxiv_id"], metadata["actual_version"]
        self.unpack(self.get(f"https://export.arxiv.org/e-print/{ident}{version}"), root)
        return metadata

    def resolve_arxiv(self, source):
        ident, requested = arxiv_ref(source)
        # Resolve latest to an explicit revision before obtaining bytes.
        atom = self.get(
            f"https://export.arxiv.org/api/query?id_list={ident + (requested or '')}&max_results=1"
        )
        try:
            tree = ET.fromstring(atom)
            actual = (
                tree.findtext("{http://www.w3.org/2005/Atom}entry/{http://www.w3.org/2005/Atom}id")
                or ""
            )
            resolved_id, version = arxiv_ref(actual)
        except (ET.ParseError, TexError):
            raise TexError("VERSION_UNRESOLVED", "Cannot establish actual arXiv revision") from None
        if resolved_id != ident or not version or requested and requested != version:
            raise TexError("VERSION_MISMATCH", "Resolved source does not match requested revision")
        return {
            "kind": "arxiv",
            "arxiv_id": ident,
            "requested_version": requested,
            "actual_version": version,
            "source": source,
        }
