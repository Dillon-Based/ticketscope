"""The fixture's best-match pair, shared by unit and smoke tests.

`snapshot/fixture.jsonl` holds issue TARGET_NUMBER written to match TARGET_QUERY best.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SNAPSHOT_DIR = REPO / "snapshot"

TARGET_QUERY = "zephyrcache eviction stalls node drain"
TARGET_NUMBER = 900003
NO_MATCH_QUERY = "xylophone quokka"
