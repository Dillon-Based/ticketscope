"""Independent oracle for `jobs.eval`'s metrics (epic-eval-gate test design, risk R-005).

Committed by a red-mode TEA session before story 2.1's build. The build session does not
author or edit anything here: the independent review on story 2.1 checks that this file is
unchanged since its red commit, and a change in any later story's diff is a review finding.
Story 2.2's red session adds the cluster-relevance values in its own commit.

Every expected value is an exact fraction worked by hand from `RANKINGS`; compare the
scorer's floats to them within `TOLERANCE`. Issue numbers are fixed on purpose: an oracle is
only independent if a person can redo the arithmetic below from this file alone.
"""

from fractions import Fraction
from typing import Final, Literal, TypedDict

type Kind = Literal["short", "log_heavy"]


class Pair(TypedDict):
    """One line of `eval/pairs/<snapshot>.jsonl`: numbers and kind, no text."""

    query: int
    target: int
    kind: Kind


# Duplicate links, read from the duplicate side ("duplicates"); each target mirrors its link
# as "duplicated_by". Clusters: {1, 2, 3}, {4, 5}, {6, 7}, {8, 9}.
DUPLICATE_LINKS: Final[tuple[tuple[int, int], ...]] = ((2, 1), (3, 1), (5, 4), (7, 6), (9, 8))

# One pair per duplicate issue, its target from `core.duplicate_target` (AD-26).
PAIRS: Final[tuple[Pair, ...]] = (
    {"query": 2, "target": 1, "kind": "short"},
    {"query": 3, "target": 1, "kind": "short"},
    {"query": 5, "target": 4, "kind": "short"},
    {"query": 7, "target": 6, "kind": "log_heavy"},
    {"query": 9, "target": 8, "kind": "log_heavy"},
)

# Issues in no cluster, used to pad every ranking to ten hits.
FILLERS: Final[tuple[int, ...]] = tuple(range(100, 110))

# Each query's scripted top 10, best first, as a retriever returns it after excluding the
# query issue. A number missing from a ranking is "rank 11": not in the top 10.
RANKINGS: Final[dict[int, tuple[int, ...]]] = {
    # Target 1 at rank 3; sibling 3 at rank 2 (a sibling outranks the target).
    2: (100, 3, 1, 101, 102, 103, 104, 105, 106, 107),
    # Target 1 absent (rank 11); sibling 2 at rank 4. A miss under target-only relevance.
    3: (100, 101, 102, 2, 103, 104, 105, 106, 107, 108),
    # Target 4 at rank 1.
    5: (4, 100, 101, 102, 103, 104, 105, 106, 107, 108),
    # Target 6 at rank 10: the MRR@10 boundary, 1/10.
    7: (100, 101, 102, 103, 104, 105, 106, 107, 108, 6),
    # Target 8 absent (rank 11): MRR@10 contributes 0.
    9: (100, 101, 102, 103, 104, 105, 106, 107, 108, 109),
}

# Story 2.1: relevance is the linked target only (epic Decision, 2026-11-08); overall, 5 pairs.
# Hits in the top 10: queries 2, 5 and 7, so 3 of 5.
TARGET_ONLY_RECALL_AT_10: Final = Fraction(3, 5)
# Reciprocal ranks 1/3, 0, 1, 1/10, 0: their sum 43/30, over 5 queries.
TARGET_ONLY_MRR_AT_10: Final = Fraction(43, 150)

TOLERANCE: Final = 1e-9
