#!/usr/bin/env python3
"""Start one dl-assistant MCP using the shared local configuration."""

import argparse
import json
import os
import re
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVERS = {
    "paper-search": ("paper-search-mcp", "paper_search_mcp"),
    "tex-mcp": ("tex-mcp", "tex_mcp"),
    "pdf-mcp": ("pdf-mcp", "pdf_mcp"),
    "overleaf": ("overleaf-mcp", "overleaf_mcp"),
}


def read_environment(config, server):
    if not config.exists():
        return {}
    if not stat.S_ISREG(config.stat().st_mode) or config.stat().st_mode & 0o077:
        raise ValueError("MCP configuration must be a private regular file (chmod 600)")
    try:
        data = json.loads(config.read_text())
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError("MCP configuration is not valid JSON") from None
    if not isinstance(data, dict) or set(data) - {"shared", *SERVERS}:
        raise ValueError("Unknown MCP configuration section")
    for section in data.values():
        if not isinstance(section, dict) or any(
            not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key)
            or not isinstance(value, str) or "\0" in value
            for key, value in section.items()
        ):
            raise ValueError("Each MCP section must map environment names to strings")
    return data.get("shared", {}) | data.get(server, {})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("server", choices=SERVERS)
    parser.add_argument("--config", type=Path, default=Path.home() / ".config/dl-assistant/mcp.json")
    args = parser.parse_args()
    try:
        env = os.environ | read_environment(args.config.expanduser(), args.server)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    folder, module = SERVERS[args.server]
    python = ROOT / "mcp-servers" / folder / ".venv/bin/python"
    if not python.is_file():
        parser.exit(1, f"Missing environment for {args.server}. Run scripts/setup-mcp.py.\n")
    os.execve(python, [str(python), "-m", module], env)


if __name__ == "__main__":
    main()
