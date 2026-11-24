#!/usr/bin/env python3
"""Compare two incarnations of the environment and render the masked drill record (story 5.9, R11).

    python3 scripts/recreate_drill.py compare FIRST.json SECOND.json
    python3 scripts/recreate_drill.py archive-diff BEFORE.json AFTER.json
    python3 scripts/recreate_drill.py record --result RESULT.json --log LOG --out FILE

A facts file is the JSON `scripts/eks-corpus-facts.sh` prints for one incarnation: `corpus_meta`
(the one row, as an object), `issues` (the count) and `digest` (md5 of the ordered issue numbers).
It may also carry `hostname` and `certificate` (what the smoke check saw over HTTPS); when both
files carry one, the two must be equal. Equal `loaded_at` in `corpus_meta` is the proof the second
incarnation restored the corpus and did not load it again.

An archive listing is the JSON of `aws s3api list-objects-v2 --prefix backups/<first>/`: `Contents`
rows with `Key`, `Size` and `ETag`. `archive-diff` exits 0 when the key, size and ETag sets of the
two are identical (nothing was written to or deleted from the first incarnation's folder).

`compare` and `archive-diff` exit 0 on a match, 1 on a difference (each is printed), 2 when an
input cannot be trusted: unreadable, malformed or empty. An unreadable input never reads as a
match. `record` masks the log with `restore_drill.mask` and writes the markdown. This module makes
no cluster or AWS call.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from scripts.restore_drill import mask
except ImportError:  # run as `python3 scripts/recreate_drill.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from restore_drill import mask  # type: ignore[no-redef]  # pyright: ignore[reportMissingImports]


def _facts(name: str, snap: Any) -> dict[str, Any]:
    if not isinstance(snap, dict):
        raise ValueError(f"{name}: not an object")
    meta = snap.get("corpus_meta")
    if not isinstance(meta, dict) or not meta:
        raise ValueError(f"{name}: no corpus_meta row")
    issues = snap.get("issues")
    if isinstance(issues, bool) or not isinstance(issues, int):
        raise ValueError(f"{name}: issues is not an integer")
    digest = snap.get("digest")
    if not isinstance(digest, str) or not digest:
        raise ValueError(f"{name}: no digest")
    return snap


def compare(first: Any, second: Any) -> list[str]:
    """Each way the second incarnation's corpus facts differ from the first's; empty is a match."""
    one, two = _facts("first", first), _facts("second", second)
    found: list[str] = []
    for key in sorted(set(one["corpus_meta"]) | set(two["corpus_meta"])):
        a, b = one["corpus_meta"].get(key), two["corpus_meta"].get(key)
        if a != b:
            found.append(f"corpus_meta.{key}: first {a}, second {b}")
    for key in ("issues", "digest", "hostname", "certificate"):
        if key in ("hostname", "certificate") and (key not in one or key not in two):
            continue
        if one.get(key) != two.get(key):
            found.append(f"{key}: first {one.get(key)}, second {two.get(key)}")
    return found


def _objects(name: str, listing: Any) -> set[tuple[str, int, str]]:
    if not isinstance(listing, dict):
        raise ValueError(f"{name}: not an object")
    rows = listing.get("Contents")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{name}: no Contents; an empty listing proves nothing")
    found: set[tuple[str, int, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{name}: a row is not an object")
        key, size, etag = row.get("Key"), row.get("Size"), row.get("ETag")
        if not isinstance(key, str) or not isinstance(etag, str):
            raise ValueError(f"{name}: a row has no Key or ETag")
        if isinstance(size, bool) or not isinstance(size, int):
            raise ValueError(f"{name}: {key} has no integer Size")
        found.add((key, size, etag))
    return found


def archive_diff(before: Any, after: Any) -> list[str]:
    """Each object added, removed or changed between two listings of the first prefix."""
    a, b = _objects("before", before), _objects("after", after)
    found: list[str] = []
    old, new = {k: (s, e) for k, s, e in a}, {k: (s, e) for k, s, e in b}
    for key in sorted(old.keys() - new.keys()):
        found.append(f"removed: {key}")
    for key in sorted(new.keys() - old.keys()):
        found.append(f"added: {key}")
    for key in sorted(old.keys() & new.keys()):
        if old[key] != new[key]:
            found.append(f"changed: {key} {old[key]} -> {new[key]}")
    return found


def render_record(result: dict[str, Any], log: str) -> str:
    """The drill record as markdown, masked: verdict, runs, facts, archive check, notes, log."""
    runs = "\n".join(f"| {r['step']} | {r['run']} | {r['result']} |" for r in result["runs"])
    facts = "\n".join(
        f"- {name}: {json.dumps(result[name], sort_keys=True)}" for name in ("first", "second")
    )
    differences = "\n".join(f"- {d}" for d in result["differences"]) or "- none"
    archive = "\n".join(f"- {d}" for d in result["archive_differences"]) or "- none"
    notes = "\n".join(f"- {n}" for n in result.get("notes", [])) or "- none"
    body = f"""# Recreate drill (story 5.9, R11, R2)

Result: {result["verdict"]}

An environment was brought up, backed up on its way down (`backup_first`), destroyed, and a second
environment was brought up with `restore_from` naming the first one's backup folder. The second
archives under its own `serverName`; the two were compared. Identifying values are masked.

## Runs

| step | run | result |
| --- | --- | --- |
{runs}

## Corpus facts

{facts}

Differences (equal `loaded_at` means the second did not load again):

{differences}

## The first incarnation's folder, listed before and after the second environment

Differences in key, size and ETag:

{archive}

## Notes

{notes}

## Commands and output

```text
{log.rstrip()}
```
"""
    return mask(body)


def _load(path: str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"{path}: {error}") from error


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    cmp = sub.add_parser("compare")
    cmp.add_argument("first")
    cmp.add_argument("second")
    diff = sub.add_parser("archive-diff")
    diff.add_argument("before")
    diff.add_argument("after")
    rec = sub.add_parser("record")
    rec.add_argument("--result", required=True)
    rec.add_argument("--log", required=True)
    rec.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command in ("compare", "archive-diff"):
            if args.command == "compare":
                differences = compare(_load(args.first), _load(args.second))
            else:
                differences = archive_diff(_load(args.before), _load(args.after))
            for difference in differences:
                print(difference)
            if differences:
                return 1
            print(f"recreate drill: {args.command} OK")
            return 0
        result = _load(args.result)
        log = Path(args.log).read_text(encoding="utf-8")
        Path(args.out).write_text(render_record(result, log), encoding="utf-8")
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(f"recreate-drill: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
