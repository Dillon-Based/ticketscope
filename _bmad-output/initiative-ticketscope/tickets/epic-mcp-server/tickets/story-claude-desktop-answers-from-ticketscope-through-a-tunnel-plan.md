---
title: 'Claude Desktop answers from ticketscope through a tunnel'
type: 'feature'
ticket: '2'
created: '2026-11-11'
status: 'in-review'
baseline_revision: '5355ad32c976f3d328fac7057a70171bc0e6cd83'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick]
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `/mcp` is reachable only inside kind, so Claude Desktop (R4) cannot call it, and Claude Desktop's real request shapes are unchecked in CI (R-003). The kind Gateway listener's hostname `ticketscope.kind.internal` makes Envoy 404 any other Host before the server sees it (R-006).

**Approach:** One environment value, the tunnel hostname, is added to the platform Gateway listener, the `/mcp` route's hostnames and `allowed_hosts`. A committed script runs the tunnel to the kind Gateway. A person connects Claude Desktop, and its captured requests are committed and replayed in `mcp-e2e.yml`.

## Boundaries & Constraints

**Always:** Tunnel hostname empty by default in chart values, rendering no extra listener, route host or allowed host; `ticketscope.kind.internal` keeps working. The tunnel host reaches only `/mcp` (404 for `/v1/search` and `/`). No credential committed; the script reads the tunnel credential from the environment and the tunnel stops when the script exits. Server changes Claude Desktop needs are made in `ticketscope.mcp` with a test. Each tool result carries a text content block with the serialised JSON beside `structuredContent`. kind-up.sh defaults the host to the stand-in `tunnel.ticketscope.test`, set in kind values.

**Never:** Rewrite the Host header at the tunnel; run a tunnel in CI; commit captured credentials; edit the captured requests in later stories (a pin test guards their bytes); touch retrieval defaults or `api` keys.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior |
|----------|--------------|---------------------------|
| Stand-in host | `tools/list`, `Host: tunnel.ticketscope.test` | 200 from `/mcp` |
| Tunnel host, other paths | same Host, `/v1/search` and `/` | 404 |
| Kind host | `Host: ticketscope.kind.internal` | still 200 |
| Host not in allowed_hosts | on listener and route only | refused by mcp |
| Value unset | default values | no extra listener, route host or allowed host |
| Tunnel stopped | script exited | hostname no longer reaches the cluster |
| Replay | captured initialize, tools/list, tools/call | protocol version accepted, both tools listed, `structuredContent` and text block returned |

</frozen-after-approval>

## Code Map

- `deploy/charts/platform/templates/gateway.yaml` — listener `http` carries `gateway.hostname`; add a second listener for `gateway.tunnelHostname` when set. `values.yaml` (`gateway:` at line 3) gets `tunnelHostname: ""`; `values-kind.yaml` sets the stand-in.
- `deploy/charts/ticketscope/templates/_helpers.tpl:70` `ticketscope.mcpHosts` — feeds both the `/mcp` HTTPRoute hostnames and `TICKETSCOPE_MCP_ALLOWED_HOSTS` in `templates/mcp.yaml`; append `mcp.tunnelHostname` there (one change, two places). Keep wildcard and empty refusal. Verify the `api` routes list their own hostnames so the tunnel host 404s on them.
- `deploy/charts/ticketscope/values.yaml:86` `mcp:` gets `tunnelHostname: ""`; `values-kind.yaml` sets the stand-in.
- `scripts/kind-up.sh` — pass `TUNNEL_HOSTNAME` (default: the stand-in from kind values) with `--set-string` to both `helm upgrade` calls (platform ~line 108, ticketscope ~line 149).
- New `scripts/tunnel.sh` — start the chosen tunnel to the Gateway URL (macOS: the 18080 port-forward kind-up opens), reading the credential from env, `trap` to stop on exit.
- `src/ticketscope/mcp/server.py` — tool returns `SearchResponse`; confirm the text content block is serialised JSON, add if not; adjust protocol/response shape only as the capture shows.
- `tests/mcp/` — extend `test_search_tool.py` (uses `_gateway()`, Host header) with the stand-in-host checks; add `tests/mcp/captured/` and a replay test plus a pin test on its bytes. `.github/workflows/mcp-e2e.yml` already runs `pytest -m kind tests/mcp`.
- Chart unit tests: `tests/unit/test_chart_mcp.py` (render with value unset and set; no wildcard).
- Docs: add Claude Desktop custom-connector steps (no auth) and the tunnel choice to the repo docs.

## Tasks & Acceptance

**Execution (unattended):**
- [ ] Platform chart: second listener from `gateway.tunnelHostname`; kind values stand-in; chart test for set and unset.
- [ ] ticketscope chart: `mcp.tunnelHostname` into `mcpHosts`; kind values stand-in; chart test.
- [ ] `scripts/kind-up.sh`: `TUNNEL_HOSTNAME` to both releases.
- [ ] `scripts/tunnel.sh` plus a credential-scan unit test.
- [ ] Text content block in tool results, with a test.
- [ ] `tests/mcp` stand-in-host admission tests, replay test and pin test (replay fixtures arrive after the human step).

**Human steps (this story is HITL):**
- [ ] Before choosing ngrok: curl the tunnel's `/mcp` from outside with a non-browser client; confirm no interstitial, an intact streamed response, and that the free bandwidth limit covers a demo. Otherwise use Tailscale Funnel. Record the choice and why in this plan.
- [ ] Create the tunnel account, reserve the hostname, run `scripts/tunnel.sh` against kind.
- [ ] Add `https://<host>/mcp` as a custom connector in Claude Desktop (no auth), ask a triage question, confirm `search_similar_issues` is called and the answer cites returned issues; commit a screenshot and link it here.
- [ ] Capture `initialize`, `notifications/initialized`, `tools/list`, `tools/call` with protocol version and headers, no credentials; commit under `tests/mcp/captured/`.

**Acceptance Criteria:**
- Given the stand-in host in kind values, when `mcp-e2e.yml` sends `tools/list` with it, then `/mcp` answers 200, `/v1/search` and `/` answer 404, and `ticketscope.kind.internal` still works.
- Given the tunnel value unset, when the charts render, then no extra listener, route host or allowed host appears.
- Given the captured requests, when `mcp-e2e.yml` replays them, then they pass and no credential appears in them.
- Given the script has exited, when the tunnel hostname is requested, then it no longer reaches the cluster.
- Given a person's Claude Desktop session, when they ask a triage question, then a committed screenshot shows the tool call and an answer citing returned issues.

## Verification

- `uv run pytest tests/unit -k "chart or tunnel"` (chart renders, credential scan).
- `uv run pytest -m kind tests/mcp` after `scripts/kind-up.sh` (admission and replay).
- `helm template` both charts with and without the tunnel value.

## Tunnel choice

_Recorded at the human step: ngrok free static domain or Tailscale Funnel, and why._

## Review Triage Log

| Finding | Verdict | Route | Evidence |
|---|---|---|---|
| `sleep infinity` on macOS | medium | patch | BSD sleep rejects it; replaced with a `while :; do sleep 3600; done` loop |
| Tailscale host vs `TUNNEL_HOSTNAME` | medium | patch | Funnel serves the node name; script now refuses on a mismatch, docs say so |
| `funnel reset` cleanup too broad | low | patch | Cleanup now only undoes a Funnel this script started |
| allowed_hosts matrix row untested | false | none | `tests/unit/test_mcp_server.py::test_a_foreign_host_is_refused_without_a_stack_trace` proves the server's own check |
| Unset-default and stand-in tests weak | low | patch | Added a defaults render plus a kind-values check |
| api route open when `hostname` empty | low | defer | Only a misconfigured release; recorded in deferred-work.md |
| kind-up cannot disable the tunnel host | low | patch | `${TUNNEL_HOSTNAME-...}` now honours an explicit empty value |
| Import reflow | low | rejected | Cosmetic, no harm |
| Text block only unit-tested | false | none | The unit test asserts the text block; the SDK default is verified there |
