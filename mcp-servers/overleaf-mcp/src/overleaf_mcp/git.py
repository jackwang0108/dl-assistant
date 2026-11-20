"""Read-only inspection of a user-chosen Git worktree. No clone, fetch, merge or push."""

import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from .models import OverleafError, checksum, digest, identifier


def git(repo, *args):
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, timeout=15, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        raise OverleafError("GIT_UNAVAILABLE", "Git inspection failed or timed out") from None
    if result.returncode:
        raise OverleafError(
            "GIT_QUERY_FAILED", "Git inspection failed; repository content was not changed"
        )
    text = result.stdout.decode("utf-8", errors="replace")
    return text if "-z" in args else text.strip()


def inspect(repo, project_id, base_url, remote="origin", branch="main"):
    identifier(project_id)
    identifier(remote)
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_./-]{0,150}", branch) or ".." in branch:
        raise OverleafError("INVALID_BRANCH", "Use an explicit ordinary remote branch name")
    path = Path(repo).expanduser().resolve()
    root = Path(git(path, "rev-parse", "--show-toplevel")).resolve()
    if root != path:
        raise OverleafError("GIT_ROOT_REQUIRED", "Bind the repository root, not a subdirectory")
    url = git(path, "remote", "get-url", remote)
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.password
        or parsed.username not in (None, "git")
    ):
        raise OverleafError(
            "GIT_REMOTE_INVALID",
            "Use an Overleaf HTTPS remote without a password/token embedded in its URL",
        )
    expected_hosts = (
        {"git.overleaf.com"}
        if urlsplit(base_url).hostname in ("www.overleaf.com", "overleaf.com")
        else {urlsplit(base_url).hostname}
    )
    if (
        parsed.hostname not in expected_hosts
        or parsed.path.rstrip("/").split("/")[-1] != project_id
    ):
        raise OverleafError(
            "GIT_PROJECT_MISMATCH", "Git remote does not identify this Overleaf project/instance"
        )
    head = git(path, "rev-parse", "HEAD")
    status = git(path, "status", "--porcelain=v1", "-z")
    refs = git(path, "for-each-ref", "--format=%(objectname)", f"refs/remotes/{remote}/{branch}")
    tracked = git(path, "ls-files", "-z").split("\x00")
    manifest = []
    total = 0
    partial = False
    symlinks = []
    for name in tracked:
        if not name:
            continue
        file = path / name
        if file.is_symlink():
            symlinks.append(name)
            continue
        if not file.is_file():
            continue
        size = file.stat().st_size
        if total + size > 250_000_000 or len(manifest) >= 5000:
            partial = True
            break
        if not file.resolve().is_relative_to(path):
            raise OverleafError("UNSAFE_PATH", "Tracked file escapes bound worktree")
        total += size
        manifest.append({"path": name, "sha256": checksum(file), "bytes": size})
    return {
        "project_id": project_id,
        "repo_dir": str(path),
        "remote": remote,
        "remote_branch": branch,
        "git_url": url,
        "head": head,
        "dirty": bool(status),
        "local_status": status[:12000],
        "tracking_head": refs or None,
        "tracking_head_freshness": "local_observation_not_live_remote_verification",
        "source_manifest": manifest,
        "manifest_sha256": digest(manifest),
        "manifest_partial": partial,
        "symlinks": symlinks,
    }


def changed_files(binding, left, right):
    if not binding or not all(re.fullmatch(r"[a-f0-9]{40,64}", s or "") for s in (left, right)):
        return {"status": "unavailable", "reason": "Both bound commits are required"}
    try:
        text = git(
            binding["repo_dir"],
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            "--name-status",
            left,
            right,
            "--",
        )
        return {"status": "available", "name_status": text}
    except OverleafError:
        return {
            "status": "unavailable",
            "reason": "Commits are not available in the current bound repository",
        }
