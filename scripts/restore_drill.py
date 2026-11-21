#!/usr/bin/env python3
"""Compare a restored cluster with its source, and render the masked drill record (story 5.7, R9).

    python3 scripts/restore_drill.py compare SOURCE.json RESTORED.json --expected N
    uv run python scripts/restore_drill.py expected-issues
    python3 scripts/restore_drill.py record --result RESULT.json --log LOG --out FILE

A snapshot is the JSON `scripts/restore-drill.sh` gathers from one cluster: `corpus_meta` (the one
row, as an object), `issues` (the issue count) and `digest` (md5 of the ordered issue numbers).
`compare` exits 0 when the two match and equal the pinned Release's count, 1 when they differ (each
difference is named), 2 when an input cannot be trusted: unreadable, malformed or incomplete. An
unreadable snapshot never reads as a match. `expected-issues` prints the `Issues:` count of the
pinned snapshot's Release (the way tests/eks/test_public_smoke.py reads it). `record` masks the
log and writes the markdown record. This module makes no cluster or AWS call.
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
VALUES = REPO / "deploy" / "charts" / "ticketscope" / "values.yaml"

_MASKS = [
    (re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"), "<access-key-id>"),
    (re.compile(r"[A-Za-z0-9-]+\.[a-z0-9]+\.[a-z0-9-]+\.eks\.amazonaws\.com"), "<eks-endpoint>"),
    (re.compile(r"[A-Za-z0-9.-]+\.elb\.amazonaws\.com"), "<load-balancer>"),
    (re.compile(r"\b\d{12}\b"), "<account>"),
]


def mask(text: str) -> str:
    """The text with account ids, access keys and private AWS hostnames replaced."""
    for pattern, replacement in _MASKS:
        text = pattern.sub(replacement, text)
    return text


def _check(name: str, snap: Any) -> dict[str, Any]:
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


def compare(source: Any, restored: Any, expected: int) -> list[str]:
    """Each way the restored snapshot differs from the source or the Release; empty is a match."""
    src, res = _check("source", source), _check("restored", restored)
    found: list[str] = []
    for key in sorted(set(src["corpus_meta"]) | set(res["corpus_meta"])):
        a, b = src["corpus_meta"].get(key), res["corpus_meta"].get(key)
        if a != b:
            found.append(f"corpus_meta.{key}: source {a}, restored {b}")
    if src["issues"] != res["issues"]:
        found.append(f"issues: source {src['issues']}, restored {res['issues']}")
    if src["digest"] != res["digest"]:
        found.append(f"digest: source {src['digest']}, restored {res['digest']}")
    if res["issues"] != expected:
        found.append(f"release: restored {res['issues']}, the pinned Release publishes {expected}")
    return found


def render_record(result: dict[str, Any], log: str) -> str:
    """The drill record as markdown, masked: verdict, stage timings, snapshots and the log."""
    stages = "\n".join(f"| {s['stage']} | {s['seconds']} |" for s in result["stages"])
    differences = "\n".join(f"- {d}" for d in result["differences"]) or "- none"
    body = f"""# Restore drill (story 5.7, R9)

Result: {result["verdict"]}

The source cluster's backup was restored into a new cluster (`ticketscope-restore`) through the
Barman Cloud Plugin, and the two were compared. Identifying values are masked.

## Timings

| stage | seconds |
| --- | ---: |
{stages}

## Comparison

- Pinned Release's issue count: {result["expected"]}
- Source: {json.dumps(result["source"], sort_keys=True)}
- Restored: {json.dumps(result["restored"], sort_keys=True)}

Differences:

{differences}

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


def release_issue_count() -> int:
    """`Issues: N` from the body of the pinned snapshot's GitHub Release."""
    from ticketscope.adapters.release import read_snapshot_pin

    pin = read_snapshot_pin(VALUES)
    match = re.search(r"github\.com/([^/]+/[^/]+)/releases/download", pin["baseUrl"])
    if match is None:
        raise ValueError(f"cannot find the repository in {pin['baseUrl']}")
    request = urllib.request.Request(
        f"https://api.github.com/repos/{match.group(1)}/releases/tags/snapshot-{pin['version']}",
        headers={"Accept": "application/vnd.github+json"},
    )
    if token := os.environ.get("GITHUB_TOKEN"):
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        body = str(json.load(response).get("body", ""))
    found = re.search(r"Issues:\s*(\d+)", body)
    if found is None:
        raise ValueError("the Release body has no `Issues:` line")
    return int(found.group(1))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    cmp = sub.add_parser("compare")
    cmp.add_argument("source")
    cmp.add_argument("restored")
    cmp.add_argument("--expected", type=int, required=True)
    sub.add_parser("expected-issues")
    rec = sub.add_parser("record")
    rec.add_argument("--result", required=True)
    rec.add_argument("--log", required=True)
    rec.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "compare":
            differences = compare(_load(args.source), _load(args.restored), args.expected)
            for difference in differences:
                print(difference)
            if differences:
                return 1
            print("restore drill: OK")
            return 0
        if args.command == "expected-issues":
            print(release_issue_count())
            return 0
        result = _load(args.result)
        log = Path(args.log).read_text(encoding="utf-8")
        Path(args.out).write_text(render_record(result, log), encoding="utf-8")
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(f"restore-drill: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
