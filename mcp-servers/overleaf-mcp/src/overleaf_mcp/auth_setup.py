"""Interactive local setup: secrets are never command arguments or MCP tool inputs."""

import argparse
import getpass
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url", default=os.getenv("OVERLEAF_BASE_URL", "https://www.overleaf.com")
    )
    parser.add_argument("--proxy", default=os.getenv("OVERLEAF_PROXY_URL"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    parsed = urlsplit(base)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        parser.error("Use an HTTPS Overleaf instance URL without embedded credentials")
    target = (
        args.output
        or Path(os.getenv("OVERLEAF_MCP_HOME", str(Path.home() / ".local/share/overleaf-mcp")))
        / "auth-v2.json"
    )
    cookie = getpass.getpass("Overleaf 完整 Cookie header（输入不回显，不粘贴到聊天）: ").strip()
    if not cookie or "\n" in cookie or "\r" in cookie:
        parser.error("Cookie header must be a nonempty single line")
    try:
        with httpx.Client(
            base_url=base + "/",
            proxy=args.proxy,
            follow_redirects=False,
            trust_env=False,
            timeout=30,
        ) as client:
            csrf_response = client.get("dev/csrf", headers={"Cookie": cookie})
            csrf = csrf_response.text.strip()
            if csrf_response.status_code != 200 or not csrf or "<" in csrf or len(csrf) > 8192:
                raise ValueError(
                    "Session could not be validated; log in again and copy a current request Cookie header"
                )
            response = client.get("user/projects", headers={"Cookie": cookie})
            if response.status_code != 200:
                raise ValueError(
                    "Session was rejected or redirected; no existing credentials changed"
                )
            projects = response.json().get("projects")
            if not isinstance(projects, list):
                raise ValueError("Unexpected Overleaf response; no existing credentials changed")
        target = target.expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            os.chmod(temporary, 0o600)
            json.dump({"origin": base, "cookie": cookie, "csrf_token": csrf}, stream)
        os.replace(temporary, target)
        os.chmod(target, 0o600)
        print(
            json.dumps(
                {"status": "validated", "path": str(target), "projects_visible": len(projects)},
                ensure_ascii=False,
            )
        )
    except httpx.HTTPError:
        print(
            "Network request failed; check the proxy and retry. Existing credentials were not changed."
        )
        raise SystemExit(1) from None
    except (ValueError, OSError):
        print(
            "Validation or local save failed. Check the current login and proxy; no secret values are printed."
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
