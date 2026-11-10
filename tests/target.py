"""The fixture's best-match pair and expected kinds, shared by unit and smoke tests.

`snapshot/fixture.jsonl` holds issue TARGET_NUMBER written to match TARGET_QUERY best.
`snapshot/fixture-kinds.json` records each fixture issue's expected kind, outside the
schema; `load` never reads it.
"""

import json
from pathlib import Path

from ticketscope.adapters.release import read_embeddings_pin, read_snapshot_pin

REPO = Path(__file__).resolve().parent.parent
SNAPSHOT_DIR = REPO / "snapshot"

TARGET_QUERY = "zephyrcache eviction stalls node drain"
TARGET_NUMBER = 900003
NO_MATCH_QUERY = "xylophone quokka"


def read_kinds(path: Path) -> dict[int, str]:
    """A kinds sidecar (fixture or ingest's): issue number to expected kind."""
    raw: dict[str, str] = json.loads(path.read_text(encoding="utf-8"))
    return {int(number): kind for number, kind in raw.items()}


def fixture_kinds() -> dict[int, str]:
    return read_kinds(SNAPSHOT_DIR / "fixture-kinds.json")


CHART_VALUES = REPO / "deploy" / "charts" / "ticketscope" / "values.yaml"


def snapshot_pin() -> dict[str, str]:
    """`snapshot.version`, `sha256` and `baseUrl` from the chart's values.yaml."""
    return read_snapshot_pin(CHART_VALUES)


def embeddings_pin() -> dict[str, str]:
    """`embeddings.modelId`, `assetVersion` and `sha256` from the chart's values.yaml."""
    return read_embeddings_pin(CHART_VALUES)
