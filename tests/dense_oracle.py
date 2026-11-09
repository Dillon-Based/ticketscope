"""Independent oracle for dense search's cosine score (epic-hybrid-retrieval test design,
risk R-001, "Independent Oracles").

The cosine fixture is worked by hand from `VECTORS` against `QUERY`; compare a ranking's
floats to the fractions within `TOLERANCE`. No red-mode session ran before story 3.1's
build, so the build session committed this from the test design's table (recorded in the
story's Implementation Notes); `test_dense_oracle_pinned.py` pins its bytes from here on.
Never edit it: a change in a later diff is a review finding.

A distance returned as the score reverses the order; an inner product scores issues 1 and 2
both 1.
"""

from fractions import Fraction
from typing import Final

TOLERANCE: Final = 1e-9

QUERY: Final[tuple[float, float]] = (1.0, 0.0)

# Issue number -> 2-dimensional vector (the unsized column allows any dimension).
VECTORS: Final[dict[int, tuple[float, float]]] = {
    1: (1.0, 0.0),
    2: (1.0, 1.0),
    3: (0.0, 1.0),
    4: (-1.0, 0.0),
}

# Expected dense order, best first, and each issue's exact cosine to QUERY.
ORDER: Final[tuple[int, ...]] = (1, 2, 3, 4)
# Issue 2's cosine is 1/sqrt(2), irrational, so it is given as a float to 15 places.
COSINE: Final[dict[int, Fraction | float]] = {
    1: Fraction(1),
    2: 0.707106781186548,
    3: Fraction(0),
    4: Fraction(-1),
}
