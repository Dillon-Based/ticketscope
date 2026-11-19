#!/usr/bin/env python3
"""Reduce a GitHub Actions run log (`gh run view <id> --log`) to the lines that say what happened.

    gh run view <id> --log | python3 scripts/run_summary.py [--max-lines N]

`scripts/run-summary.sh <id>` is the usual entry point. Keeps stage markers, errors, denials,
leftover and DNS verdicts, Terraform's completion lines and the stage-time tables of
eks-deploy.sh and eks-teardown.sh. Drops echoed script source, step env dumps, ANSI colour and
Terraform's refresh chatter. Account ids print as <acct>: the output is pasted into chat and
committed notes. Each kept line prints as `job | step | HH:MM:SS | text`.
"""

import argparse
import re
import sys
from collections.abc import Iterable, Iterator

ANSI = re.compile(r"\x1b\[[0-9;]*m|\^\[\[[0-9;]*m")
ACCOUNT = re.compile(r"\b\d{12}\b")
TIMESTAMP = re.compile(r"^﻿?(\d{4}-\d{2}-\d{2}T(\d{2}:\d{2}:\d{2})\.\d+Z) ?(.*)$")
ECHOED_SOURCE = "\x1b[36;1m"
KEEP = re.compile(
    r"stage: |\bError\b|error:|##\[error\]|::error|\bFAIL\b|LEFTOVER|\bGONE\b|leftover-check:|"
    r"eks-teardown:|eks-deploy:|bootstrap-drift:|Destroy complete|Apply complete|AccessDenied|"
    r"not authorized|UnauthorizedOperation|still exists|condition met|\bis gone\b|\bare gone\b|"
    r"Sleeping \d+s|Dispatched env-down|Remedy|timed out|did not answer|\.\s+(A|AAAA)$"
)
NOISE = re.compile(r"Refreshing state|: Reading\.\.\.|Read complete after|^\s+[A-Z][A-Z0-9_]*: ")
TABLE_START = re.compile(r"^--- eks-(deploy|teardown) stage times ---$")


def summarise(lines: Iterable[str]) -> Iterator[str]:
    in_table = False
    for raw in lines:
        parts = raw.rstrip("\n").split("\t", 2)
        if len(parts) != 3:
            continue
        job, step, rest = parts
        if ECHOED_SOURCE in rest or "^[[36;1m" in rest:
            continue
        match = TIMESTAMP.match(rest)
        clock, text = (match.group(2), match.group(3)) if match else ("--:--:--", rest)
        text = ANSI.sub("", text).rstrip()
        if TABLE_START.match(text):
            in_table = True
        elif in_table and not re.match(r"^\S+\s+\d+s$", text):
            in_table = False
        if not (in_table or TABLE_START.match(text)) and (
            not KEEP.search(text) or NOISE.search(text)
        ):
            continue
        yield ACCOUNT.sub("<acct>", f"{job} | {step} | {clock} | {text}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--max-lines", type=int, default=150)
    args = parser.parse_args(argv)
    kept = list(summarise(sys.stdin))
    if len(kept) > args.max_lines:
        dropped = len(kept) - args.max_lines
        head, tail = args.max_lines // 3, args.max_lines - args.max_lines // 3
        kept = [*kept[:head], f"... {dropped} lines omitted ...", *kept[-tail:]]
    print("\n".join(kept) if kept else "(no notable lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
