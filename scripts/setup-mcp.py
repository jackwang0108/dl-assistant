#!/usr/bin/env python3
"""Install selected MCP servers and print their Codex TOML configuration."""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SERVERS = {
    "paper-search": ("paper-search-mcp", "paper_search_mcp"),
    "tex-mcp": ("tex-mcp", "tex_mcp"),
    "pdf-mcp": ("pdf-mcp", "pdf_mcp"),
    "overleaf": ("overleaf-mcp", "overleaf_mcp"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", choices=SERVERS, action="append",
                        help="Repeat to select servers. Default: all four.")
    parser.add_argument("--python", default="3.12", help="Python version or interpreter for uv.")
    parser.add_argument("--docling", action="store_true", help="Include the optional PDF parser.")
    parser.add_argument("--proxy", help="Proxy for MCP requests, e.g. http://127.0.0.1:7890.")
    parser.add_argument("--config-only", action="store_true", help="Use existing environments.")
    args = parser.parse_args()
    if args.proxy:
        proxy = urlsplit(args.proxy)
        if proxy.scheme not in {"http", "https"} or not proxy.hostname or proxy.username or proxy.password:
            parser.error("--proxy requires an HTTP(S) proxy URL without credentials")
    if not args.config_only and not shutil.which("uv"):
        parser.error("Install uv first")
    names = list(dict.fromkeys(args.server or SERVERS))
    if args.docling and "pdf-mcp" not in names:
        parser.error("--docling requires pdf-mcp")
    install_env = os.environ.copy()
    if args.proxy:
        install_env.update(HTTP_PROXY=args.proxy, HTTPS_PROXY=args.proxy)
    config = []
    for name in names:
        folder, module = SERVERS[name]
        project = ROOT / "mcp-servers" / folder
        if not args.config_only:
            command = ["uv", "sync", "--locked", "--no-dev", "--python", args.python]
            if name == "pdf-mcp" and args.docling:
                command.extend(("--extra", "structure"))
            result = subprocess.run(command, cwd=project, stdout=sys.stderr, env=install_env)
            if result.returncode:
                return result.returncode
        python = project / ".venv" / "bin" / "python"
        if not python.is_file():
            parser.error(f"Missing environment: {project / '.venv'}")
        section = f"mcp_servers.{name}"
        config.extend((f"[{section}]", f"command = {json.dumps(str(python), ensure_ascii=False)}",
                       f"args = {json.dumps(['-m', module])}"))
        if args.proxy:
            config.append(f"[{section}.env]")
            for key in ("HTTP_PROXY", "HTTPS_PROXY"):
                config.append(f"{key} = {json.dumps(args.proxy)}")
            proxy_keys = {"pdf-mcp": "PDF_MCP_PROXY_URL", "overleaf": "OVERLEAF_PROXY_URL"}
            if name in proxy_keys:
                config.append(f"{proxy_keys[name]} = {json.dumps(args.proxy)}")
        config.append("")
    print("\n".join(config))
    return 0


if __name__ == "__main__":
    sys.exit(main())
