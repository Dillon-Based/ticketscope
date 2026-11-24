#!/usr/bin/env python3
"""Work out what a node loss cost, and render the masked drill record (story 5.8, R10).

    python3 scripts/failure_drill.py analyze --probe PROBE.log --events EVENTS.json
    python3 scripts/failure_drill.py record --result RESULT.json --log LOG --out FILE

`PROBE.log` has one line per public search probe, `<epoch seconds> <http status>` (000 when the
request itself failed); a probe succeeded when its status is 200. `EVENTS.json` holds
`terminated_at`, `promoted_at` (null when no standby took over) and `archive`: the Cluster's
ContinuousArchiving condition, `lastArchivedWAL` before and after a forced WAL switch on the new
primary, `lastFailedWAL`, and the plugin `serverName` before and after. `analyze` prints the result
as JSON and exits 0 when the failure was survived and archiving is clean, 1 when not (each
problem is named in the result), 2 when an input cannot be trusted. `record` masks and renders
markdown. This module makes no cluster or AWS call.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from restore_drill import mask as _mask

_MASKS = [
    (re.compile(r"\bip-\d+-\d+-\d+-\d+(?:\.[a-z0-9.-]+)?"), "<node>"),
    (re.compile(r"\bi-[0-9a-f]{8,17}\b"), "<instance>"),
]


def mask(text: str) -> str:
    """The text with account ids, keys, private hostnames, node names and instance ids replaced."""
    for pattern, replacement in _MASKS:
        text = pattern.sub(replacement, text)
    return _mask(text)


def placement_ok(nodes: list[str]) -> bool:
    """True when there are at least two instances and every one is on its own node."""
    return len(nodes) >= 2 and len(set(nodes)) == len(nodes)


def _segment(name: str) -> str | None:
    """The name when it is a 24-hex WAL segment (timeline then position); `.history`, `.backup`
    and `.partial` names do not order against segments, so they are None."""
    return name if re.fullmatch(r"[0-9A-Fa-f]{24}", name) else None


def archive_problems(archive: dict[str, Any], switched: bool = True) -> list[str]:
    """Ways the Cluster's archive status is not clean after promotion; empty is clean.
    `switched` is False when no standby was promoted, so no WAL switch was forced."""
    found: list[str] = []
    if archive["continuous_archiving"] != "True":
        found.append(
            f"archiving is not continuing: ContinuousArchiving {archive['continuous_archiving']!r}"
        )
    if not archive["server_before"] or not archive["server_after"]:
        raise ValueError("events: the Cluster's plugin serverName is empty")
    before = str(archive["last_archived_before"])
    after = str(archive["last_archived_after"])
    failed = str(archive["last_failed"])
    new, old = _segment(after), _segment(before)
    if switched and (new is None or (old is not None and new <= old)):
        found.append(f"archiving did not advance after a WAL switch: {before!r} then {after!r}")
    failed_segment = _segment(failed)
    if failed_segment and (new is None or failed_segment > new):
        found.append(f"a WAL failed to archive and was not retried: lastFailedWAL {failed}")
    if archive["server_before"] != archive["server_after"]:
        found.append(
            f"serverName changed: {archive['server_before']} then {archive['server_after']}"
        )
    return found


def _probes(lines: list[str]) -> list[tuple[int, bool]]:
    out: list[tuple[int, bool]] = []
    for line in lines:
        parts = line.split()
        if len(parts) != 2 or not parts[0].isdigit() or not re.fullmatch(r"\d{3}", parts[1]):
            raise ValueError(f"probe log: bad line {line!r}")
        out.append((int(parts[0]), parts[1] == "200"))
    if not out:
        raise ValueError("probe log: no probes")
    return out


def analyze(probe_lines: list[str], events: dict[str, Any]) -> dict[str, Any]:
    """The drill's figures and verdict from the probe log and the event timestamps."""
    probes = _probes(probe_lines)
    try:
        terminated = int(events["terminated_at"])
        promoted = events["promoted_at"]
        archive = events["archive"]
        archive_found = archive_problems(archive, switched=promoted is not None)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"events: missing or malformed {error}") from error
    problems: list[str] = []
    after = [(t, ok) for t, ok in probes if t >= terminated]
    if not after:
        raise ValueError("probe log: no probe at or after the termination")
    failures = [t for t, ok in after if not ok]
    recovery: int | None = 0
    if failures:
        later = [t for t, ok in after if ok and t > max(failures)]
        if not later:
            recovery = None
            problems.append("the public search probe never succeeded again after the failure")
        else:
            recovery = min(later) - terminated
    promotion = None if promoted is None else int(promoted) - terminated
    if promotion is None:
        problems.append("no standby was promoted")
    problems += archive_found
    return {
        "verdict": "FAILED" if problems else "OK",
        "problems": problems,
        "failed_requests": len(failures),
        "recovery_seconds": recovery,
        "promotion_seconds": promotion,
        "probes": len(probes),
        "archive": archive,
    }


def render_record(result: dict[str, Any], log: str) -> str:
    """The drill record as markdown, masked: verdict, figures, placement, archive status, log."""
    nodes = "\n".join(
        f"- instance {i + 1} on node {i + 1}" for i, _ in enumerate(result.get("placement", []))
    )
    problems = "\n".join(f"- {p}" for p in result["problems"]) or "- none"
    body = f"""# Failure drill (story 5.8, R10)

Result: {result["verdict"]}

The node holding the primary was terminated while a probe searched through the public hostname
every second. Identifying values are masked.

## Placement before the failure

{nodes or "- not recorded"}

Instances on different nodes: {"yes" if placement_ok(result.get("placement", [])) else "NO"}.

## Figures

- Promotion seconds: {result["promotion_seconds"]}
- Recovery seconds: {result["recovery_seconds"]}
- Failed requests: {result["failed_requests"]}
- Probes: {result["probes"]}
- Archive status: {json.dumps(result["archive"], sort_keys=True)}

Problems:

{problems}

## Commands and output

```text
{log.rstrip()}
```
"""
    return mask(body)


def _read(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"{path}: {error}") from error


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    ana = sub.add_parser("analyze")
    ana.add_argument("--probe", required=True)
    ana.add_argument("--events", required=True)
    rec = sub.add_parser("record")
    rec.add_argument("--result", required=True)
    rec.add_argument("--log", required=True)
    rec.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "analyze":
            result = analyze(_read(args.probe).splitlines(), json.loads(_read(args.events)))
            print(json.dumps(result, sort_keys=True))
            return 0 if result["verdict"] == "OK" else 1
        result = json.loads(_read(args.result))
        Path(args.out).write_text(render_record(result, _read(args.log)), encoding="utf-8")
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(f"failure-drill: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
