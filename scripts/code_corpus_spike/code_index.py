"""A local full-text index over a source tree, for the code-search prototype.

One SQLite file with two FTS5 tables: `file` holds one row per source file, `method` one
row per method (and one per file for its fields and imports). Identifiers are split on
camelCase before indexing, so "villager trades" finds `VillagerTrades`. Ranking is SQLite's
BM25 with the class name weighted above the body.

The index holds the source text. Build it on the machine that uses it and never commit or
publish it.

    uv run python scripts/code_corpus_spike/code_index.py <src dir> <index.sqlite>
"""

import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+")
HUMP = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")
LITERAL = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
NAME_WEIGHT, BODY_WEIGHT = 8.0, 1.0


def _words(text: str) -> frozenset[str]:
    return frozenset(text.split())


NOISE = _words(
    "abstract boolean break byte case catch char class const continue default double else enum "
    "extends final finally float for goto implements import instanceof int interface long native "
    "new null package private protected public return short static super switch synchronized this "
    "throw throws transient true false try void volatile while var string object override list "
    "java util net minecraft com mojang get set "
    "the and that this with for are was not but you have has had from when what which will would "
    "can could should there their they them then than into out about after before also any all "
    "its does did doing being been were your our more most some such only very just over "
    "under again once here why how where who whom both each few other same too use used using "
    "see steps reproduce expected observed result results actual bug issue game"
)


def terms(text: str) -> list[str]:
    """Lower-case search terms: words and the humps of identifiers, lightly stemmed."""
    out = []
    for word in WORD.findall(text):
        for hump in HUMP.findall(word):
            term = hump.lower()
            if len(term) > 3 and term.endswith("s"):
                term = term[:-1]
            if len(term) >= 3 and term not in NOISE:
                out.append(term)
    return out


@dataclass(frozen=True, slots=True)
class Chunk:
    start: int  # 1-based, inclusive
    end: int
    text: str


def chunks(text: str) -> list[Chunk]:
    """One chunk per top-level method or nested type; the rest (imports, fields) as one more."""
    out: list[Chunk] = []
    rest: list[str] = []
    current: list[str] = []
    start = depth = 0
    for number, line in enumerate(text.splitlines(), 1):
        code = LITERAL.sub("", line)
        opened, closed = code.count("{"), code.count("}")
        if depth <= 1 and not current and (opened == 0 or depth == 0):
            rest.append(line)
        else:
            if not current:
                start = number
            current.append(line)
        depth += opened - closed
        if current and depth <= 1:
            out.append(Chunk(start, number, "\n".join(current)))
            current = []
    if current:
        out.append(Chunk(start, start + len(current) - 1, "\n".join(current)))
    if rest:
        out.append(Chunk(1, 1, "\n".join(rest)))
    return out


def build(src: Path, index: Path, suffix: str = ".java") -> tuple[int, int]:
    """Write a fresh index of every `suffix` file under `src`; returns (files, methods)."""
    index.unlink(missing_ok=True)
    db = sqlite3.connect(index)
    for table in ("file", "method"):
        db.execute(
            f"CREATE VIRTUAL TABLE {table} USING fts5("
            "name_terms, body_terms, path UNINDEXED, start UNINDEXED, end UNINDEXED, "
            "text UNINDEXED, tokenize = 'unicode61')"
        )
    files = methods = 0
    for path in sorted(src.rglob(f"*{suffix}")):
        rel = str(path.relative_to(src))
        text = path.read_text(errors="replace")
        name = " ".join(terms(path.stem))
        lines = text.count("\n") + 1
        db.execute(
            "INSERT INTO file VALUES (?, ?, ?, ?, ?, ?)",
            (name, " ".join(terms(text)), rel, 1, lines, text),
        )
        files += 1
        for chunk in chunks(text):
            db.execute(
                "INSERT INTO method VALUES (?, ?, ?, ?, ?, ?)",
                (name, " ".join(terms(chunk.text)), rel, chunk.start, chunk.end, chunk.text),
            )
            methods += 1
    db.commit()
    db.close()
    return files, methods


@dataclass(frozen=True, slots=True)
class Hit:
    path: str
    start: int
    end: int
    score: float  # higher is better
    text: str


def search(db: sqlite3.Connection, query: str, k: int, table: str = "method") -> list[Hit]:
    """The best-matching chunk of each of the top `k` files, best first."""
    wanted = list(dict.fromkeys(terms(query)))
    if not wanted or table not in ("file", "method"):
        return []
    match = " OR ".join(f'"{term}"' for term in wanted)
    rows = db.execute(
        f"SELECT path, start, end, -bm25({table}, ?, ?) AS score, text FROM {table} "
        f"WHERE {table} MATCH ? ORDER BY score DESC LIMIT ?",
        (NAME_WEIGHT, BODY_WEIGHT, match, k * 8),
    )
    hits: dict[str, Hit] = {}
    for path, start, end, score, text in rows:
        if path not in hits:
            hits[path] = Hit(path, start, end, score, text)
            if len(hits) == k:
                break
    return list(hits.values())


if __name__ == "__main__":
    counted = build(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"indexed {counted[0]} files, {counted[1]} chunks into {sys.argv[2]}")
