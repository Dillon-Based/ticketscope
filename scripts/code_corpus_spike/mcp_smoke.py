"""Start the prototype MCP server over stdio and call both tools like a client would.

usage: mcp_smoke.py <server.py> <index.sqlite> <query>
"""

import asyncio
import json
import os
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters, stdio_client


def body(result: Any) -> Any:
    return result.structured_content or json.loads(result.content[0].text)


async def main() -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=[sys.argv[1]],
        env={**os.environ, "TICKETSCOPE_CODE_INDEX": sys.argv[2]},
    )
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        print("tools:", [t.name for t in tools.tools])
        res = await session.call_tool("search_code", {"query": sys.argv[3], "k": 5})
        found = body(res)
        print("is_error:", res.is_error, "index:", found["index"])
        for r in found["results"]:
            print(
                f"  {r['rank']}. {r['path']}:{r['start_line']}-{r['end_line']} score={r['score']}"
            )
            print("      " + r["snippet"].strip().splitlines()[0][:90])
        top = found["results"][0]
        got = await session.call_tool(
            "get_code",
            {
                "path": top["path"],
                "start_line": top["start_line"],
                "end_line": top["start_line"] + 5,
            },
        )
        g = body(got)
        print(
            "get_code:", g["path"], g["start_line"], g["end_line"], "of", g["total_lines"], "lines"
        )
        bad = await session.call_tool("get_code", {"path": "nope/Missing.java"})
        print("missing file -> is_error:", bad.is_error)


asyncio.run(main())
