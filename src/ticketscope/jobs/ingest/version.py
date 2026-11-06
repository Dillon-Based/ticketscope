"""Snapshot versions: `YYYY.MM.N`, the next free N for the run month (AD-6, AD-12).

A published version is never reused, so N is one past the highest N of the month
among existing `snapshot-*` tags, even when an earlier one was taken down.

    gh api ... --jq '.[].ref' | python -m ticketscope.jobs.ingest.version --month 2026.11
"""

import argparse
import re
import sys
from collections.abc import Iterable

TAG_PREFIX = "snapshot-"
_MONTH = re.compile(r"^\d{4}\.(0[1-9]|1[0-2])$")
_TAG = re.compile(r"^(?:refs/tags/)?snapshot-(\d{4}\.\d{2})\.([1-9]\d*)$")


def next_version(tags: Iterable[str], month: str) -> str:
    """The next free `YYYY.MM.N` for `month` (`YYYY.MM`) among `tags`."""
    if not _MONTH.match(month):
        raise ValueError(f"month must be YYYY.MM, got {month!r}")
    taken = [
        int(match.group(2))
        for tag in tags
        if (match := _TAG.match(tag.strip())) and match.group(1) == month
    ]
    return f"{month}.{max(taken, default=0) + 1}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print the next free snapshot version.")
    parser.add_argument("--month", required=True, help="YYYY.MM, the run month (UTC)")
    args = parser.parse_args(argv)
    print(next_version(sys.stdin.read().split(), args.month))
    return 0


if __name__ == "__main__":
    sys.exit(main())
