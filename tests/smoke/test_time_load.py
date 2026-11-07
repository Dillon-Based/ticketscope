"""Timed loads through `scripts/time-load.sh` (initiative R10: load within 600 s).

Marker `kind` so they run in the kind CI job, which has Docker and has already built
the Postgres image: set `POSTGRES_IMAGE` to it (CI passes `ticketscope-postgres:18-<sha>`)
or the script builds `ticketscope-postgres:18-local`. They need no cluster.

- Story 5 AC-5: the pinned asset, alone in its directory, loads with exit 0 in under 600 s.
- Story 13 AC-3: the committed v2 fixture loads, printing a load time, with exit 0.
"""

import gzip
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.target import REPO, SNAPSHOT_DIR, snapshot_pin
from ticketscope.adapters.release import fetch_snapshot

pytestmark = pytest.mark.kind

BUDGET_SECONDS = 600
SCRIPT = REPO / "scripts" / "time-load.sh"


def _time_load(snapshot_dir: Path, version: str) -> float:
    result = subprocess.run(
        [str(SCRIPT), str(snapshot_dir), version],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=BUDGET_SECONDS + 300,
        check=False,
    )
    assert result.returncode == 0, (
        f"time-load.sh exit {result.returncode}:\n{result.stderr[-4000:]}"
    )
    lines = result.stdout.strip().splitlines()
    assert lines, f"time-load.sh printed no load time:\n{result.stderr[-4000:]}"
    return float(lines[-1])


@pytest.mark.criterion("ticketscope--e1-s5--AC-5")
def test_pinned_asset_alone_loads_within_budget(
    pytestconfig: pytest.Config, tmp_path: Path
) -> None:
    pin = snapshot_pin()
    cached = fetch_snapshot(
        pin["baseUrl"],
        pin["version"],
        pytestconfig.cache.mkdir("ticketscope-snapshot"),
        pin["sha256"],
        timeout=300,
    )
    only_asset = tmp_path / "snapshot"
    only_asset.mkdir()
    shutil.copy2(cached, only_asset / cached.name)
    assert [p.name for p in only_asset.iterdir()] == [f"{pin['version']}.jsonl.gz"]

    seconds = _time_load(only_asset, pin["version"])
    assert 0 < seconds < BUDGET_SECONDS


@pytest.mark.criterion("ticketscope--e1-s13--AC-3")
def test_v2_fixture_loads_and_prints_a_time(tmp_path: Path) -> None:
    fixture = SNAPSHOT_DIR / "fixture.jsonl"
    with fixture.open("rb") as raw, gzip.open(tmp_path / "fixture.jsonl.gz", "wb") as packed:
        shutil.copyfileobj(raw, packed)

    seconds = _time_load(tmp_path, "fixture")
    assert seconds > 0
