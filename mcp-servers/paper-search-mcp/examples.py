"""Small opt-in example: reads capabilities by default; --search can use API quota."""

import argparse
import asyncio
import json

from fastmcp import Client

from paper_search_mcp.server import mcp


async def main(search):
    async with Client(mcp) as client:
        result = await client.call_tool("get_capabilities", {})
        print(json.dumps(result.data, ensure_ascii=False, indent=2))
        if search:
            result = await client.call_tool(
                "search_papers",
                {
                    "queries": [{"text": '"Attention Is All You Need"', "sources": ["arxiv"]}],
                    "budget": {"max_requests": 1, "max_items": 2, "max_seconds": 20},
                },
            )
            print(json.dumps(result.data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search", action="store_true")
    asyncio.run(main(parser.parse_args().search))
