"""Pin the hand-computed oracle fixture to the content its red commits wrote.

Stories 2.1 and 2.2 each require that the oracle a ATDD red session committed is not edited by
the build. A git diff against the red commit needs history a shallow CI checkout lacks, so the
fixture is pinned by byte length and SHA-256 instead. The file may only grow: each pin hashes a
prefix, so a later story can append its own oracle without breaking the earlier pins.
"""

import hashlib

import pytest

from tests.target import REPO

ORACLE = REPO / "tests" / "eval_oracle.py"

# (red commit, bytes written by it, SHA-256 of those bytes)
PINS = [
    (
        "b7be713 (story 2.1)",
        2877,
        "18d5fb34df7892936b6e5a9b9b5982d9f9cf5b2a84de0a7b34391f854825baa3",
    ),
    (
        "7ea485a (story 2.2)",
        5848,
        "8fd96287e723246e78c14927f9f4fb1fbd1c87753ee499e5652b94ab9635d589",
    ),
]


@pytest.mark.criterion("ticketscope--e2-s1--AC-1", "ticketscope--e2-s2--AC-1")
@pytest.mark.parametrize(("commit", "length", "digest"), PINS, ids=[pin[0] for pin in PINS])
def test_the_oracle_fixture_is_unchanged_since_its_red_commit(
    commit: str, length: int, digest: str
) -> None:
    data = ORACLE.read_bytes()
    assert len(data) >= length, f"tests/eval_oracle.py lost content written at {commit}"
    assert hashlib.sha256(data[:length]).hexdigest() == digest, (
        f"tests/eval_oracle.py no longer starts with its {commit} content"
    )
