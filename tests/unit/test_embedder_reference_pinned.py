"""Pin the embedder's reference vectors to the bytes they were committed with.

`scripts/reference_vectors.py` made `tests/fixtures/embedder_reference.json` once, outside
fastembed, for story 5.13 (DW-3). A git diff needs history a shallow CI checkout lacks, so the
file is pinned by byte length and SHA-256, as `test_dense_oracle_pinned.py` does. The file may
only grow: each pin hashes a prefix. Never edit an existing oracle file.
"""

import hashlib
import json

import pytest

from tests.target import REPO

REFERENCE = REPO / "tests" / "fixtures" / "embedder_reference.json"

# (commit, bytes written by it, SHA-256 of those bytes)
PINS = [
    (
        "story 5.13 build",
        94712,
        "5c65fce1d8d7eae3e5f51ccf20ece83dc9621698ff1486c4b63adb8dc0839f64",
    ),
]


@pytest.mark.criterion("ticketscope--e5-s13--AC-3")
def test_the_embedder_reference_is_unchanged_since_it_was_committed() -> None:
    data = REFERENCE.read_bytes()
    for commit, length, digest in PINS:
        assert len(data) >= length, f"embedder_reference.json lost content written at {commit}"
        assert hashlib.sha256(data[:length]).hexdigest() == digest, (
            f"embedder_reference.json no longer starts with its {commit} content"
        )


@pytest.mark.criterion("ticketscope--e5-s13--AC-3")
def test_the_reference_has_a_384_dimension_vector_per_text() -> None:
    ref = json.loads(REFERENCE.read_text(encoding="utf-8"))
    assert len(ref["texts"]) == len(ref["vectors"]) >= 8
    assert all(len(v) == 384 for v in ref["vectors"])
    assert ref["tolerance"] == {"min_cosine": 0.9999, "max_component_diff": 2e-3}
