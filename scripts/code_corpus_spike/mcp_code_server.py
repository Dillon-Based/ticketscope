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
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent))
import code_index
import log_evidence

K_MAX = 30
TEXT_MATCHES_MAX = 60
TEXT_MATCHES_PER_FILE = 3
WORKFLOW = """Work out where in the code this ticket lives, using the logs through the person.

1. search_code with the ticket's words, then get_code to read the likely files.
2. In those files, find what they log: logger names and message strings (find_text helps).
3. Write log queries from that evidence, not from guesses: the exact message text and the
   logger or class name, with the time window the ticket gives. You cannot run them. Ask the
   person which query language and field names their log viewer uses if you do not know, then
   give them the queries to run and ask them to paste the results back.
4. Pass what they paste to code_from_log. It returns the files and lines behind the stack
   frames, class names and messages in the paste.
5. Read those lines with get_code, then say which files most likely need to change and why,
   and what you could not confirm.

Ticket:
{ticket}
"""
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


class TextMatch(BaseModel):
    path: str
    line: int
    text: str


class TextSearchResponse(BaseModel):
    matches: list[TextMatch]
    files_matched: int
    case_sensitive: bool


class LogFrame(BaseModel):
    path: str
    line: int
    symbol: str
    count: int
    source: str


class LogClass(BaseModel):
    name: str
    path: str
    count: int


class LogMessage(BaseModel):
    path: str
    line: int
    literal: str
    count: int


class LogEvidenceResponse(BaseModel):
    frames: list[LogFrame]
    classes: list[LogClass]
    messages: list[LogMessage]
    unresolved: list[str]


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

    @server.tool(
        name="find_text",
        description=(
            "Find an exact piece of text in the code: an error message, a log message, a "
            "configuration key, a name. Use it to find the statement that wrote a log line, "
            "or the logger names and message strings of a file so a log query can quote them. "
            "Matches the text as written; it falls back to ignoring case when nothing matches."
        ),
    )
    def find_text(  # pyright: ignore[reportUnusedFunction]
        text: Annotated[str, Field(description="The exact text to find.", min_length=3)],
    ) -> TextSearchResponse:
        with connect() as db:
            rows = db.execute("SELECT path, text FROM file").fetchall()
        for fold in (False, True):
            needle = text.lower() if fold else text
            matches: list[TextMatch] = []
            files = 0
            for path, body in rows:
                if needle not in (body.lower() if fold else body):
                    continue
                files += 1
                found = 0
                for number, line in enumerate(body.splitlines(), 1):
                    if needle in (line.lower() if fold else line):
                        if len(matches) < TEXT_MATCHES_MAX and found < TEXT_MATCHES_PER_FILE:
                            matches.append(TextMatch(path=path, line=number, text=line.strip()))
                        found += 1
            if files:
                return TextSearchResponse(
                    matches=matches, files_matched=files, case_sensitive=not fold
                )
        return TextSearchResponse(matches=[], files_matched=0, case_sensitive=True)

    resolver: list[log_evidence.Resolver] = []

    @server.tool(
        name="code_from_log",
        description=(
            "Map log output to the code that produced it. Pass the text a person pasted from "
            "their log viewer: log lines, a stack trace, or exported JSON. Returns the files "
            "and lines behind its stack frames, the files of the classes it names (logger "
            "names, exception types), and the string in the code that produced each message. "
            "You cannot query the logs yourself: write a query, ask the person to run it and "
            "paste the result, then call this."
        ),
    )
    def code_from_log(  # pyright: ignore[reportUnusedFunction]
        log_text: Annotated[str, Field(description="The pasted log output, unedited.")],
    ) -> LogEvidenceResponse:
        if not resolver:
            resolver.append(
                log_evidence.Resolver(sqlite3.connect(f"file:{index}?mode=ro", uri=True))
            )
        return LogEvidenceResponse.model_validate(asdict(resolver[0].evidence(log_text)))

    @server.prompt(
        name="investigate_ticket",
        description="Find where a ticket lives in the code, using logs a person pastes in.",
    )
    def investigate_ticket(ticket: str) -> str:  # pyright: ignore[reportUnusedFunction]
        return WORKFLOW.format(ticket=ticket)

    return server


def main() -> None:
    index = os.environ.get("TICKETSCOPE_CODE_INDEX", "")
    if not index or not Path(index).is_file():
        sys.exit("TICKETSCOPE_CODE_INDEX must name an index file built by code_index.py")
    build_server(Path(index)).run("stdio")


if __name__ == "__main__":
    main()
