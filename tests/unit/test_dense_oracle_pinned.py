"""Pin the cosine oracle fixture to the bytes it was committed with.

Story 3.1 had no red-mode session, so the build committed `tests/dense_oracle.py` from the
test design's table. A git diff needs history a shallow CI checkout lacks, so the fixture is
pinned by byte length and SHA-256, as `test_eval_oracle_pinned.py` does for epic 2. The file
may only grow: each pin hashes a prefix.
"""

import hashlib

from tests.target import REPO

ORACLE = REPO / "tests" / "dense_oracle.py"

# (commit, bytes written by it, SHA-256 of those bytes)
PINS = [
    (
        "story 3.1 build",
        1334,
        "5de7a20d1e531a5380e1954a906f6b4c0deb421444001cd76f14a57b434c37be",
    ),
]


def test_the_cosine_oracle_is_unchanged_since_it_was_committed() -> None:
    data = ORACLE.read_bytes()
    for commit, length, digest in PINS:
        assert len(data) >= length, f"tests/dense_oracle.py lost content written at {commit}"
        assert hashlib.sha256(data[:length]).hexdigest() == digest, (
            f"tests/dense_oracle.py no longer starts with its {commit} content"
        )
