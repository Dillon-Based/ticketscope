"""Independent oracle for story 4.4's issue key (epic-mcp-server test design, risk R-007).

Committed by a red-mode TEA session before story 4.4's build. The build session does not
author or edit anything here: a change to this file in any later story's diff is a review
finding, and `tests/unit/test_key_oracle_pinned.py` pins its bytes.

The expected values come from the snapshot v2 `key` field and from the table in
`test-design-epic-4.md` ("Independent Oracles"), never from the url parser under test.
"""

from typing import Final

# The pattern C-4 fixes: matched exactly, with no case or whitespace normalisation.
KEY_PATTERN: Final[str] = r"^[A-Z][A-Z0-9]*-[1-9][0-9]*$"

# (url, snapshot key or None, expected `issue.key`).
URL_TO_KEY: Final[tuple[tuple[str, str | None, str | None], ...]] = (
    ("https://bugs.mojang.com/browse/MCL-6629", "MCL-6629", "MCL-6629"),
    ("https://bugs.mojang.com/browse/REALMS-12", "REALMS-12", "REALMS-12"),
    ("https://bugs.mojang.com/browse/MCD-1", "MCD-1", "MCD-1"),
    # A v1-shaped fixture: not a browse url.
    ("https://github.com/o/r/issues/7", None, None),
    # A suffix after the key.
    ("https://bugs.mojang.com/browse/MCL-6629/extra", None, None),
    # Not `core.derive.MOJANG_BROWSE_URL`: http, not https.
    ("http://bugs.mojang.com/browse/MCL-6629", None, None),
)

# Inputs to `get_issue(key)`. Each must come back as a tool error and never as another issue:
# `6629` is never issue number 6629, and no dot-segment key reaches `GET /v1/issues/6629`.
HOSTILE_KEYS: Final[tuple[str, ...]] = (
    "6629",
    "../6629",
    "..%2F6629",
    "MCL-6629/..",
    "mcl-6629",
    " MCL-6629 ",
    "MCL-6629?x=1",
    "MCL-6629#a",
    "",
    "MCL-1' OR '1'='1",
)

# The subset whose request path, if `apiclient` joined it unescaped, would resolve to
# `/v1/issues/6629` (httpx2 2.16 removes the dot segment). Used by the spy-transport row.
DOT_SEGMENT_KEYS: Final[tuple[str, ...]] = ("../6629", "MCL-6629/..")

# The one number a hostile key must never fetch.
FORBIDDEN_NUMBER: Final[int] = 6629
