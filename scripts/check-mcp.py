#!/usr/bin/env python3
"""Check installed MCP servers over stdio without touching external services."""

import argparse
import asyncio
import json
import sys
import tempfile
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

ROOT = Path(__file__).resolve().parents[1]
SERVERS = (
    ("paper-search-mcp", "paper-search", "get_capabilities", "PAPER_SEARCH_CACHE_DIR", 15),
    ("tex-mcp", "tex-mcp", "tex_capabilities", "TEX_MCP_CACHE_DIR", 14),
    ("pdf-mcp", "pdf-mcp", "pdf_capabilities", "PDF_MCP_CACHE_DIR", 17),
    ("overleaf-mcp", "overleaf", "overleaf_capabilities", "OVERLEAF_MCP_HOME", 26),
)


async def check(folder, name, capability, cache_key, expected):
    python = ROOT / "mcp-servers" / folder / ".venv" / "bin" / "python"
    if not python.is_file():
        raise FileNotFoundError(f"Run scripts/setup-mcp.py first for {folder}")
    with tempfile.TemporaryDirectory(prefix="dl-assistant-mcp-") as cache:
        env = {
            cache_key: cache,
            "FASTMCP_SHOW_SERVER_BANNER": "false",
            "FASTMCP_CHECK_FOR_UPDATES": "off",
        }
        if name == "overleaf":
            env["OVERLEAF_CREDENTIALS_PATH"] = str(Path(cache) / "unused-auth.json")
        config = Path(cache) / "config.json"
        config.write_text(json.dumps({name: env}))
        config.chmod(0o600)
        args = [str(ROOT / "scripts/run-mcp.py"), name, "--config", str(config)]
        transport = StdioTransport(command=str(python), args=args, cwd=cache)
        async with Client(transport, timeout=20) as client:
            tools = await client.list_tools()
            result = await client.call_tool(capability, {})
            data = result.structured_content or result.data
            if result.is_error or data.get("api_version") != 2 or len(tools) != expected:
                raise RuntimeError(f"{folder}: unexpected API version or tool count")
    print(f"{folder}: API v2, {len(tools)} tools")


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", choices=[s[0] for s in SERVERS])
    args = parser.parse_args()
    for server in SERVERS:
        if args.server is None or server[0] == args.server:
            await check(*server)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (OSError, RuntimeError) as error:
        sys.exit(str(error))
