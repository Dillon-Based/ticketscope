"""Pin story 4.4's key oracle to its red commit's content and check it against the snapshot.

The build must not author or edit `tests/key_oracle.py`. A git diff against the red commit needs
history a shallow CI checkout lacks, so the file is pinned by byte length and SHA-256 instead,
as `test_eval_oracle_pinned.py` does. The file may only grow: each pin hashes a prefix.

The second test needs no production code: it checks the oracle's table against the snapshot v2
`key` field, the source the url parser under test is independent of.
"""

import hashlib
import json
import re

import pytest

from tests.key_oracle import HOSTILE_KEYS, KEY_PATTERN, URL_TO_KEY
from tests.target import REPO, SNAPSHOT_DIR

ORACLE = REPO / "tests" / "key_oracle.py"

# (red commit, bytes written by it, SHA-256 of those bytes)
PINS = [
    (
        "story 4.4 red session",
        2063,
        "12359039cb4c5d1038cc47c88d8f9130b324c7a2ce9b43f0c4d36efe7834da0f",
    ),
]


@pytest.mark.criterion("ticketscope--e4-s4--AC-1")
@pytest.mark.parametrize(("commit", "length", "digest"), PINS, ids=[pin[0] for pin in PINS])
def test_the_key_oracle_is_unchanged_since_its_red_commit(
    commit: str, length: int, digest: str
) -> None:
    data = ORACLE.read_bytes()
    assert len(data) >= length, f"tests/key_oracle.py lost content written at {commit}"
    assert hashlib.sha256(data[:length]).hexdigest() == digest, (
        f"tests/key_oracle.py no longer starts with its {commit} content"
    )


@pytest.mark.criterion("ticketscope--e4-s4--AC-1")
def test_the_key_oracle_agrees_with_the_snapshot_and_the_key_pattern() -> None:
    pattern = re.compile(KEY_PATTERN)
    for _url, snapshot_key, expected in URL_TO_KEY:
        assert expected == snapshot_key
        assert expected is None or pattern.fullmatch(expected)
    assert not any(pattern.fullmatch(key) for key in HOSTILE_KEYS)

    lines = (SNAPSHOT_DIR / "fixture.jsonl").read_text(encoding="utf-8").splitlines()
    issues = [json.loads(line) for line in lines]
    assert issues
    for issue in issues:
        key = issue.get("key")
        if key is not None:
            assert pattern.fullmatch(key)
            assert issue["url"] == f"https://bugs.mojang.com/browse/{key}"
