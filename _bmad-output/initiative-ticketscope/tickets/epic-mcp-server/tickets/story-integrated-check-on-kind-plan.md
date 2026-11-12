---
title: 'Integrated check on kind (epic 4)'
type: 'feature'
ticket: '7'
created: '2026-11-12'
status: 'built'
baseline_revision: '986551f'
route: 'oneshot'
route_source: 'auto'
risk: 'medium'
review: ''
review_source: ''
lenses_ran: []
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `tests/mcp` already covers both tools with and without a mode, `get_issue` by a key from a search, unknown mode and key errors, the Claude Desktop replay and the Tempo trace, but nothing proves R3's unreachable-API case, and `mcp-e2e.yml` runs one pytest invocation.

**Approach:** Add `tests/mcp/test_unreachable_api.py`, which scales `api` to zero in its own pytest invocation after the main suite and restores it in a finalizer (R-009). `mcp-e2e.yml` runs the main suite with that file deselected, then the file.

</frozen-after-approval>

## Implementation Notes

Oneshot: the existing suite already covers every other Done-when line CI can run, so the change is one test file and a workflow edit. Files: `tests/mcp/test_unreachable_api.py`, `.github/workflows/mcp-e2e.yml`.

Not done here, because tickets are never written by the build: the epic's Notes must link story 2's recorded session for R4 and cite this story's `mcp-e2e.yml` run URL (C-7). The closure's repeated Claude Desktop session is a person's step. The new test has not run on a cluster; the PR's `mcp-e2e` run is its first.

## Verification

**Commands:**
- `uv run ruff check tests/mcp && uv run pyright tests/mcp && uv run lint-imports` -- expected: clean
- `uv run pytest -m kind tests/mcp --collect-only` -- expected: collects the new test
- PR's `mcp-e2e / deploy` check -- expected: both invocations pass and api is Ready afterwards
