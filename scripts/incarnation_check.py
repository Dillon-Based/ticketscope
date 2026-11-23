#!/usr/bin/env python3
"""Refuse a bad backup incarnation before `terraform apply` (story 5.9, R11, R2).

    python3 scripts/incarnation_check.py --incarnation ID --listing FILE
                                         [--restore-from ID --base-listing FILE]

FILE is the JSON of `aws s3api list-objects-v2 --prefix backups/ --delimiter / --query
'{CommonPrefixes: CommonPrefixes}'` (the key is always present, null when the bucket holds no
folder); the raw response works too. `--base-listing` is the same call for
`--prefix backups/<restore_from>/base/`, where the Barman Cloud Plugin keeps each base backup.

The plugin refuses to archive into a folder that already holds WAL ("Expected empty archive"), and
that failure shows only at archive time, after an apply has been paid for. So this runs first:

- the incarnation and `restore_from` match `^[a-z0-9][a-z0-9-]{0,62}$`;
- the incarnation's folder is not in the bucket;
- `restore_from` (when set) differs from the incarnation, has a folder, and has a base backup.

Exit 0 when the check passes, 1 when it refuses (each reason is printed), 2 when a listing cannot
be trusted: unreadable, malformed or lacking `CommonPrefixes`. An unreadable listing never reads as
"absent". This module makes no AWS call.
"""

import argparse
import json
import re
import sys
from pathlib import Path

NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
ROOT = "backups/"


class ListingError(Exception):
    """A listing that cannot be trusted; the check fails on it."""


def folders(path: Path, parent: str) -> set[str]:
    """The folder names directly under `parent` (`backups/` or `backups/<id>/base/`)."""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ListingError(f"{path}: unreadable listing ({error})") from error
    if not isinstance(doc, dict) or "CommonPrefixes" not in doc:
        raise ListingError(f"{path}: not a listing with CommonPrefixes")
    raw = doc["CommonPrefixes"]
    if raw is None:
        return set()
    if not isinstance(raw, list):
        raise ListingError(f"{path}: CommonPrefixes is not a list")
    found: set[str] = set()
    for item in raw:
        prefix = item.get("Prefix") if isinstance(item, dict) else item
        if not isinstance(prefix, str) or not prefix.startswith(parent) or not prefix.endswith("/"):
            raise ListingError(f"{path}: unexpected prefix {item!r} under {parent}")
        name = prefix[len(parent) : -1]
        if not name or "/" in name:
            raise ListingError(f"{path}: unexpected prefix {item!r} under {parent}")
        found.add(name)
    return found


def check(
    incarnation: str,
    restore_from: str,
    prefixes: set[str],
    base_backups: set[str] | None = None,
) -> list[str]:
    """Each reason to refuse; empty means the incarnation may be applied.

    `prefixes` are the folder names under `backups/`; `base_backups` the base-backup folders under
    the `restore_from` folder, or None when they were not listed (never read as "none").
    """
    problems: list[str] = []
    if not NAME.fullmatch(incarnation):
        problems.append(f"incarnation {incarnation!r} does not match {NAME.pattern}")
    if restore_from and not NAME.fullmatch(restore_from):
        problems.append(f"restore_from {restore_from!r} does not match {NAME.pattern}")
    if problems:
        return problems
    if incarnation in prefixes:
        problems.append(
            f"{ROOT}{incarnation}/ already exists in the bucket; an incarnation archives into an "
            "empty folder"
        )
    if restore_from:
        if restore_from == incarnation:
            problems.append("restore_from equals the incarnation; a restore reads another folder")
        elif restore_from not in prefixes:
            problems.append(f"restore_from: {ROOT}{restore_from}/ is not in the bucket")
        elif base_backups is None:
            problems.append(f"restore_from: the base backups of {ROOT}{restore_from}/ not listed")
        elif not base_backups:
            problems.append(f"restore_from: {ROOT}{restore_from}/ has no base backup")
    return problems


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--incarnation", required=True)
    parser.add_argument("--restore-from", default="")
    parser.add_argument("--listing", type=Path, required=True)
    parser.add_argument("--base-listing", type=Path)
    args = parser.parse_args(argv)
    try:
        prefixes = folders(args.listing, ROOT)
        base: set[str] | None = None
        if args.base_listing is not None:
            base = folders(args.base_listing, f"{ROOT}{args.restore_from}/base/")
    except ListingError as error:
        print(f"incarnation-check: FAIL, {error}", file=sys.stderr)
        return 2
    problems = check(args.incarnation, args.restore_from, prefixes, base)
    for problem in problems:
        print(f"incarnation-check: FAIL, {problem}", file=sys.stderr)
    if problems:
        return 1
    mode = f"restores from {args.restore_from}" if args.restore_from else "starts fresh"
    print(f"incarnation-check: OK, {args.incarnation} {mode}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
