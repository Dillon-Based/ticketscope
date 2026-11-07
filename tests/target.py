"""The fixture's best-match pair and expected kinds, shared by unit and smoke tests.

`snapshot/fixture.jsonl` holds issue TARGET_NUMBER written to match TARGET_QUERY best.
`snapshot/fixture-kinds.json` records each fixture issue's expected kind, outside the
schema; `load` never reads it.
"""

import json
import re
from pathlib import Path

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
_SNAPSHOT_BLOCK = re.compile(r"^snapshot:\n((?:[ \t]+.*\n|[ \t]*#.*\n|\n)+)", re.MULTILINE)
_PIN_FIELD = re.compile(
    r'^[ \t]+(version|sha256|baseUrl):[ \t]*"?([^"\n#]*?)"?[ \t]*$', re.MULTILINE
)


def snapshot_pin() -> dict[str, str]:
    """`snapshot.version`, `sha256` and `baseUrl` from the chart's values.yaml (no YAML
    dependency: the block is flat)."""
    block = _SNAPSHOT_BLOCK.search(CHART_VALUES.read_text(encoding="utf-8"))
    if block is None:
        raise ValueError(f"{CHART_VALUES}: no top-level snapshot: block")
    pin = dict(_PIN_FIELD.findall(block.group(1)))
    missing = {"version", "sha256", "baseUrl"} - set(pin)
    if missing:
        raise ValueError(f"{CHART_VALUES}: snapshot block lacks {sorted(missing)}")
    return pin
