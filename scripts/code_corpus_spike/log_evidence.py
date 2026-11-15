"""Map pasted log output to the code that produced it.

For a setup where the model cannot query the log store: it writes a query, a person runs it
and pastes the result back. The paste can be plain log lines, a stack trace, or JSON copied
from a log viewer (escaped newlines are handled). Three kinds of evidence are pulled out and
resolved against a `code_index.py` index:

- stack frames (`at pkg.Class.method(File.java:12)`, `File "x.py", line 12`, `path/x.go:12`),
  to a file and line;
- dotted class names, such as logger names and exception types, to a file;
- message text, to the string literal in the code that produced it, placeholders allowed
  (`"Failed to store chunk {}"` matches `Failed to store chunk [3, 4]`).

Nothing here knows a log schema: it reads text.
"""

import re
import sqlite3
from collections import Counter
from dataclasses import dataclass, field

SOURCE_EXT = r"(?:java|kt|scala|groovy|py|js|jsx|ts|tsx|go|rb|cs|php)"
JAVA_FRAME = re.compile(r"\bat\s+(?:[\w.@]+/)?([\w$.]+)\.([\w$<>]+)\(([\w$-]+\.\w+):(\d+)\)")
PY_FRAME = re.compile(r'File "([^"]+\.py)", line (\d+)(?:, in (\S+))?')
PATH_FRAME = re.compile(rf"(?<![\w/.$-])((?:[\w.@-]+/)*[\w.@-]+\.{SOURCE_EXT}):(\d+)")
DOTTED_CLASS = re.compile(r"\b((?:[a-z_]\w*\.){2,}[A-Z]\w*)")
LITERAL = re.compile(r'"((?:\\.|[^"\\])*)"')
PLACEHOLDER = re.compile(r"\{[^{}]*\}|%[-\d.]*[a-zA-Z]|\$\{[^{}]*\}|\\[nt]")
MIN_LITERAL, MIN_FRAGMENT = 15, 10


@dataclass(frozen=True, slots=True)
class Frame:
    path: str
    line: int
    symbol: str  # the method or function, when the log names it
    count: int
    source: str  # the line of code at that position


@dataclass(frozen=True, slots=True)
class ClassMention:
    name: str
    path: str
    count: int


@dataclass(frozen=True, slots=True)
class MessageSource:
    path: str
    line: int
    literal: str  # the string in the code
    count: int  # log lines it matches


@dataclass(slots=True)
class Evidence:
    frames: list[Frame] = field(default_factory=list)
    classes: list[ClassMention] = field(default_factory=list)
    messages: list[MessageSource] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)  # frames in code the index lacks


def normalise(text: str) -> str:
    """Undo the escaping a JSON export puts on multi-line fields."""
    return (
        text.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
    )


class Resolver:
    """Looks names from a log up in one index. Holds the file list; reads text on demand."""

    def __init__(self, db: sqlite3.Connection) -> None:
        self.db = db
        self.paths = [row[0] for row in db.execute("SELECT path FROM file")]
        self.by_class: dict[str, str] = {}
        self.by_name: dict[str, list[str]] = {}
        for path in self.paths:
            self.by_class[path.rsplit(".", 1)[0].replace("/", ".")] = path
            self.by_name.setdefault(path.rsplit("/", 1)[-1], []).append(path)
        self._literals: list[tuple[list[str], str, int, str]] | None = None

    def _line(self, path: str, line: int) -> str:
        row = self.db.execute("SELECT text FROM file WHERE path = ?", (path,)).fetchone()
        lines = row[0].splitlines() if row else []
        return lines[line - 1].strip() if 0 < line <= len(lines) else ""

    def class_path(self, dotted: str) -> str | None:
        """The file of a dotted class name; inner classes resolve to their outer file."""
        name = dotted.split("$", 1)[0]
        while name:
            if name in self.by_class:
                return self.by_class[name]
            name = name.rpartition(".")[0] if "." in name else ""
        return None

    def file_path(self, written: str) -> str | None:
        """The indexed file a path in a log refers to, by longest matching suffix."""
        written = written.lstrip("./")
        candidates = self.by_name.get(written.rsplit("/", 1)[-1], [])
        parts = written.split("/")
        for keep in range(len(parts), 0, -1):
            suffix = "/".join(parts[-keep:])
            found = [p for p in candidates if p == suffix or p.endswith("/" + suffix)]
            if len(found) == 1:
                return found[0]
        return None

    def literals(self) -> list[tuple[list[str], str, int, str]]:
        """(fixed parts, path, line, literal) for every message-like string in the code."""
        if self._literals is None:
            found = []
            for path, text in self.db.execute("SELECT path, text FROM file"):
                for number, line in enumerate(text.splitlines(), 1):
                    for literal in LITERAL.findall(line):
                        if len(literal) < MIN_LITERAL or " " not in literal:
                            continue
                        parts = [p.strip() for p in PLACEHOLDER.split(literal)]
                        parts = [p for p in parts if p]
                        if any(len(p) >= MIN_FRAGMENT for p in parts):
                            found.append((parts, path, number, literal))
            self._literals = found
        return self._literals

    def evidence(self, pasted: str, limit: int = 15) -> Evidence:
        text = normalise(pasted)
        result = Evidence()
        frames: Counter[tuple[str, int, str]] = Counter()
        missing: Counter[str] = Counter()
        for dotted, method, _file, line in JAVA_FRAME.findall(text):
            path = self.class_path(dotted)
            if path:
                frames[(path, int(line), method)] += 1
            else:
                missing[dotted] += 1
        for written, line, symbol in PY_FRAME.findall(text):
            path = self.file_path(written)
            if path:
                frames[(path, int(line), symbol)] += 1
            else:
                missing[written] += 1
        for written, line in PATH_FRAME.findall(text):
            path = self.file_path(written)
            if path and not any(k[0] == path and k[1] == int(line) for k in frames):
                frames[(path, int(line), "")] += 1
        for (path, line, symbol), count in list(frames.items())[:limit]:  # in order of appearance
            result.frames.append(Frame(path, line, symbol, count, self._line(path, line)))

        in_frames = Counter(d.split("$", 1)[0] for d, *_ in JAVA_FRAME.findall(text))
        mentions = Counter(DOTTED_CLASS.findall(text))
        named: list[ClassMention] = []
        for dotted, count in mentions.items():
            outside = count - in_frames[dotted]  # a logger name or exception type, not a frame
            path = self.class_path(dotted) if outside > 0 else None
            if path:
                named.append(ClassMention(dotted, path, outside))
        result.classes = sorted(named, key=lambda m: -m.count)[:limit]

        # Each log line goes to the most specific literal that explains it.
        candidates = [item for item in self.literals() if max(item[0], key=len) in text]
        best: Counter[tuple[str, int, str]] = Counter()
        weights: dict[tuple[str, int, str], int] = {}
        for line in text.splitlines():
            scored = []
            for parts, path, number, literal in candidates:
                position = 0
                for part in parts:
                    position = line.find(part, position)
                    if position < 0:
                        break
                    position += len(part)
                else:
                    scored.append((sum(len(part) for part in parts), (path, number, literal)))
            top = max((weight for weight, _ in scored), default=0)
            for weight, key in scored:
                if weight == top:
                    best[key] += 1
                    weights[key] = weight
        ordered = sorted(best, key=lambda key: (-weights[key], key))
        result.messages = [MessageSource(*key, best[key]) for key in ordered[:limit]]
        result.unresolved = [name for name, _ in missing.most_common(8)]
        return result
