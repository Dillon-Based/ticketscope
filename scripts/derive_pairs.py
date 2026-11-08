#!/usr/bin/env python3
"""Derive `eval/pairs/<version>.jsonl` from the pinned snapshot (AD-26, epic-eval-gate R1).

    uv run python scripts/derive_pairs.py            # write the pairs file
    uv run python scripts/derive_pairs.py --check    # exit 1 unless it equals the committed file

Fetches the pinned Release asset (`snapshot:` in the chart's values.yaml), verified
against its SHA-256, into `--snapshot-dir` (reused when already there). Prints
`<total> pairs: <short> short, <log_heavy> log_heavy`, which must equal the Release notes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ticketscope.adapters.release import fetch_snapshot, read_snapshot_pin
from ticketscope.core.pairs import count_by_kind, derive_pairs, pairs_jsonl
from ticketscope.jobs.load.main import read_snapshot

ROOT = Path(__file__).resolve().parent.parent
CHART_VALUES = ROOT / "deploy" / "charts" / "ticketscope" / "values.yaml"
PAIRS_DIR = ROOT / "eval" / "pairs"


def snapshot_pin(values: Path = CHART_VALUES) -> dict[str, str]:
    """`snapshot.version`, `sha256` and `baseUrl` from the chart's values.yaml."""
    return read_snapshot_pin(values)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare with the committed pairs file instead of writing it; exit 1 on difference",
    )
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=ROOT / "snapshots",
        help="where the pinned asset is cached (default: snapshots/)",
    )
    parser.add_argument("--pairs-dir", type=Path, default=PAIRS_DIR)
    args = parser.parse_args(argv)

    pin = snapshot_pin()
    asset = fetch_snapshot(
        pin["baseUrl"], pin["version"], args.snapshot_dir, pin["sha256"], timeout=300
    )
    pairs = derive_pairs(read_snapshot(asset))
    data = pairs_jsonl(pairs)
    counts = count_by_kind(pairs)
    print(f"{counts['total']} pairs: {counts['short']} short, {counts['log_heavy']} log_heavy")

    path: Path = args.pairs_dir / f"{pin['version']}.jsonl"
    if args.check:
        if not path.is_file():
            print(f"{path}: missing; run scripts/derive_pairs.py", file=sys.stderr)
            return 1
        if path.read_bytes() != data:
            print(f"{path}: differs from the regenerated pairs", file=sys.stderr)
            return 1
        print(f"{path}: byte-identical")
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
