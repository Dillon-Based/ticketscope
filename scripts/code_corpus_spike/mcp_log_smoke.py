"""Call find_text, code_from_log and the prompt over MCP with a made-up paste.

usage: mcp_log_smoke.py <server.py> <index.sqlite>
"""

import asyncio
import json
import os
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters, stdio_client

# What a person might paste: two exported JSON hits (escaped newlines) and one plain line.
PASTE = (
    json.dumps(
        {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "@timestamp": "2026-11-14T09:12:01Z",
                            "level": "ERROR",
                            "logger_name": "net.minecraft.server.level.ChunkMap",
                            "message": "Failed to save chunk 12,-7",
                            "stack_trace": (
                                "java.util.ConcurrentModificationException: null\n"
                                "\tat java.base/java.util.HashMap$HashIterator.nextNode"
                                "(HashMap.java:1597)\n"
                                "\tat net.minecraft.world.level.chunk.storage.ChunkSerializer.write"
                                "(ChunkSerializer.java:300)\n"
                                "\tat net.minecraft.server.level.ChunkMap.save(ChunkMap.java:720)\n"
                                "\tat net.minecraft.server.level.ChunkMap$1.run"
                                "(ChunkMap.java:101)\n"
                            ),
                        }
                    },
                    {
                        "_source": {
                            "@timestamp": "2026-11-14T09:12:03Z",
                            "level": "ERROR",
                            "logger_name": "net.minecraft.server.level.ChunkMap",
                            "message": "Couldn't load chunk [3, 4]",
                        }
                    },
                ]
            }
        }
    )
    + "\n2026-11-14 09:12:05 ERROR [Server thread] ChunkMap - Chunk file at [8, 2] is missing"
    " level data, skipping\n"
)


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
        print("tools:", [t.name for t in (await session.list_tools()).tools])
        print("prompts:", [p.name for p in (await session.list_prompts()).prompts])
        found = body(await session.call_tool("find_text", {"text": "Failed to save chunk"}))
        where = [(m["path"].rsplit("/", 1)[-1], m["line"]) for m in found["matches"]]
        print("find_text:", found["files_matched"], "files;", where)
        ev = body(await session.call_tool("code_from_log", {"log_text": PASTE}))
        print("frames:")
        for f in ev["frames"]:
            name = f["path"].rsplit("/", 1)[-1]
            print(f"  {name}:{f['line']} {f['symbol']} x{f['count']} | {f['source'][:70]}")
        print("classes:", [(c["name"].rsplit(".", 1)[-1], c["count"]) for c in ev["classes"]])
        print("messages:")
        for m in ev["messages"]:
            print(f"  {m['path'].rsplit('/', 1)[-1]}:{m['line']} x{m['count']} | {m['literal']}")
        print("unresolved:", ev["unresolved"])
        prompt = await session.get_prompt("investigate_ticket", {"ticket": "Chunks fail to save"})
        print("prompt chars:", len(prompt.messages[0].content.text))


asyncio.run(main())
