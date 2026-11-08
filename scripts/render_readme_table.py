#!/usr/bin/env python3
"""Render the README retrieval-results table from the committed CI results JSON.

    python3 scripts/render_readme_table.py            # --check (default)
    python3 scripts/render_readme_table.py --write

The table comes from `eval/baseline.json` and sits between the generated-section markers
in README.md. `--check` fails when the README section differs from the render or a marker
is missing, duplicated or misordered; `--write` is the only writer of that section.
Standard library only, so CI runs it without installing the project.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

START = "<!-- eval-results:start -->"
END = "<!-- eval-results:end -->"
KINDS = ("short", "log_heavy", "overall")
METRICS = ("recall@1", "recall@5", "recall@10", "mrr@10", "p95_latency_ms")
HEADER = ("Mode", "Kind", "Pairs", "Recall@1", "Recall@5", "Recall@10", "MRR@10", "p95 ms")

REPO = Path(__file__).resolve().parent.parent


class RenderError(Exception):
    """The baseline or the README cannot produce a valid comparison."""


def _number(mode: str, kind: str, key: str, value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RenderError(f"baseline mode {mode!r} kind {kind!r} key {key!r} is not a number")
    if key == "pairs_scored":
        if not isinstance(value, int):
            raise RenderError(f"baseline mode {mode!r} kind {kind!r} key {key!r} is not an integer")
        return str(value)
    return f"{value:.3f}"


def render(results: dict[str, Any]) -> str:
    """The generated section: snapshot version line, blank line, table, one final newline."""
    lineage = results.get("lineage")
    version = lineage.get("snapshot_version") if isinstance(lineage, dict) else None
    if version is None:
        raise RenderError("baseline has no lineage.snapshot_version")
    modes = results.get("modes")
    if not isinstance(modes, dict):
        raise RenderError("baseline has no modes")
    rows = [HEADER]
    for mode in sorted(modes):
        for kind in KINDS:
            cell = modes[mode].get(kind) if isinstance(modes[mode], dict) else None
            if not isinstance(cell, dict):
                raise RenderError(f"baseline mode {mode!r} is missing kind {kind!r}")
            values = []
            for key in ("pairs_scored", *METRICS):
                if key not in cell:
                    raise RenderError(f"baseline mode {mode!r} kind {kind!r} is missing {key!r}")
                values.append(_number(mode, kind, key, cell[key]))
            rows.append((mode, kind, *values))
    lines = [f"Snapshot version: {version}", ""]
    lines.append("| " + " | ".join(rows[0]) + " |")
    lines.append("| " + " | ".join(["---", "---"] + ["---:"] * 6) + " |")
    lines.extend("| " + " | ".join(row) + " |" for row in rows[1:])
    return "\n".join(lines) + "\n"


def _locate(readme: str) -> tuple[int, int]:
    """Offsets of the section start (after the start marker's newline) and the end marker."""
    for marker in (START, END):
        count = readme.count(marker)
        if count == 0:
            raise RenderError(f"README is missing the marker {marker}")
        if count > 1:
            raise RenderError(f"README has the marker {marker} {count} times")
    start, end = readme.index(START), readme.index(END)
    if end < start:
        raise RenderError(f"README has {END} before {START}")
    begin = start + len(START)
    if readme[begin : begin + 1] == "\n":
        begin += 1
    return begin, end


def extract(readme: str) -> str:
    begin, end = _locate(readme)
    return readme[begin:end]


def splice(readme: str, section: str) -> str:
    begin, end = _locate(readme)
    return readme[:begin] + section + readme[end:]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--baseline", type=Path, default=REPO / "eval" / "baseline.json")
    parser.add_argument("--readme", type=Path, default=REPO / "README.md")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="fail on drift (default)")
    mode.add_argument("--write", action="store_true", help="rewrite the README section")
    args = parser.parse_args(argv)

    try:
        section = render(json.loads(args.baseline.read_text(encoding="utf-8")))
        readme = args.readme.read_bytes().decode("utf-8")
        if args.write:
            args.readme.write_bytes(splice(readme, section).encode("utf-8"))
            print(f"wrote the results table to {args.readme}")
            return 0
        if extract(readme) != section:
            print(
                f"{args.readme} results table differs from {args.baseline}; "
                "run: python3 scripts/render_readme_table.py --write",
                file=sys.stderr,
            )
            return 1
    except Exception as error:
        print(f"render_readme_table: {error}", file=sys.stderr)
        return 1
    print("README results table matches the baseline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
