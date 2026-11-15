"""Prototype MCP server: search a local code index and read from it.

Not product code and not deployed: it runs on the machine that holds the index, over stdio,
beside the ticketscope MCP server. An agent asks `search_similar_issues` what happened to
tickets like this one, and `search_code` where in the code the ticket probably lives.

    TICKETSCOPE_CODE_INDEX=/path/to/index.sqlite \
        uv run python scripts/code_corpus_spike/mcp_code_server.py

The index comes from `code_index.py`. Tool output contains source text from the index, so
connect this server only to a client that may see that code.
"""

import os
import sqlite3
import sys
from pathlib import Path
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent))
import code_index

K_MAX = 30
SNIPPET_LINES = 60
READ_LINES_MAX = 400


class CodeResult(BaseModel):
    rank: int
    path: str
    score: float
    start_line: int
    end_line: int
    snippet: str


class CodeSearchResponse(BaseModel):
    index: str
    results: list[CodeResult]


class CodeFile(BaseModel):
    path: str
    start_line: int
    end_line: int
    total_lines: int
    text: str


def _best_chunk(db: sqlite3.Connection, query: str, path: str) -> tuple[int, int, str] | None:
    """The method in `path` that covers the most distinct query terms; BM25 breaks ties."""
    wanted = set(code_index.terms(query))
    if not wanted:
        return None
    match = " OR ".join(f'"{term}"' for term in wanted)
    rows = db.execute(
        "SELECT start, end, text, body_terms FROM method WHERE method MATCH ? AND path = ? "
        "ORDER BY bm25(method, ?, ?)",
        (match, path, 0.0, 1.0),
    ).fetchall()
    if not rows:
        return None
    best = max(rows, key=lambda row: len(wanted & set(row[3].split())))  # max keeps the first tie
    return best[0], best[1], best[2]


def build_server(index: Path) -> MCPServer:
    server = MCPServer("ticketscope-code")

    def connect() -> sqlite3.Connection:
        return sqlite3.connect(f"file:{index}?mode=ro", uri=True)

    @server.tool(
        name="search_code",
        description=(
            "Find the source files most likely to be involved in a bug or behaviour, given a "
            "description in plain words (a ticket's title and text work well). Ranked by "
            "keyword match on code identifiers and text; the right file is often in the top "
            "10 but not always first, so read several results and search again with other "
            "words if none fits. Each result carries the best-matching method as a snippet; "
            "use get_code to read more of a file."
        ),
    )
    def search_code(  # pyright: ignore[reportUnusedFunction]
        query: Annotated[str, Field(description="What to look for, in plain words.")],
        k: Annotated[int, Field(description="How many files to return.", ge=1, le=K_MAX)] = 10,
    ) -> CodeSearchResponse:
        with connect() as db:
            results = []
            for rank, hit in enumerate(code_index.search(db, query, k, "file"), 1):
                start, end, text = _best_chunk(db, query, hit.path) or (1, 1, "")
                lines = text.splitlines()
                snippet = "\n".join(lines[:SNIPPET_LINES])
                if len(lines) > SNIPPET_LINES:
                    snippet += f"\n... ({len(lines) - SNIPPET_LINES} more lines)"
                results.append(
                    CodeResult(
                        rank=rank,
                        path=hit.path,
                        score=round(hit.score, 2),
                        start_line=start,
                        end_line=end,
                        snippet=snippet,
                    )
                )
        return CodeSearchResponse(index=index.name, results=results)

    @server.tool(
        name="get_code",
        description=(
            "Read part of a source file by the path search_code returned. Returns at most "
            f"{READ_LINES_MAX} lines from start_line."
        ),
    )
    def get_code(  # pyright: ignore[reportUnusedFunction]
        path: Annotated[str, Field(description="A path exactly as search_code returned it.")],
        start_line: Annotated[int, Field(description="First line to read.", ge=1)] = 1,
        end_line: Annotated[
            int | None, Field(description="Last line to read; omit for the next lines.", ge=1)
        ] = None,
    ) -> CodeFile:
        with connect() as db:
            row = db.execute("SELECT text FROM file WHERE path = ?", (path,)).fetchone()
        if row is None:
            raise ToolError(f"no such file in the index: {path}")
        lines = row[0].splitlines()
        last = min(end_line or len(lines), start_line + READ_LINES_MAX - 1, len(lines))
        return CodeFile(
            path=path,
            start_line=start_line,
            end_line=last,
            total_lines=len(lines),
            text="\n".join(lines[start_line - 1 : last]),
        )

    return server


def main() -> None:
    index = os.environ.get("TICKETSCOPE_CODE_INDEX", "")
    if not index or not Path(index).is_file():
        sys.exit("TICKETSCOPE_CODE_INDEX must name an index file built by code_index.py")
    build_server(Path(index)).run("stdio")


if __name__ == "__main__":
    main()
