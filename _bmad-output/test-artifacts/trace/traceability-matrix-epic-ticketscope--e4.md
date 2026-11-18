---
workflowType: 'testarch-trace'
runScope: 'epic'
runKey: 'epic-ticketscope--e4'
targetType: 'epic'
targetId: 'ticketscope--e4'
targetLabel: 'Epic 4: Claude Desktop calls search_similar_issues on a remote MCP server'
gateType: 'epic'
workflowStatus: 'completed'
stepsCompleted: ['step-01-load-context', 'step-02-discover-tests', 'step-03-map-criteria', 'step-04-analyze-gaps', 'step-05-gate-decision']
lastStep: 'step-05-gate-decision'
lastSaved: '2026-11-12'
sourceSha: '4dccc85d66f3e85682c6b43e3e673a93f61cbe51'
collectionMode: 'contract_static'
collectionStatus: 'COLLECTED'
coverageBasis: 'acceptance_criteria'
oracleConfidence: 'high'
oracleResolutionMode: 'formal_requirements'
externalPointerStatus: 'not_used'
oracleGranularity: 'requirements'
oracleSources:
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/epic-mcp-server.md
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-tracer-an-mcp-client-calls-search-similar-issues-through-the-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-claude-desktop-answers-from-ticketscope-through-a-tunnel-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-tool-errors-carry-the-api-s-problem-detail-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-get-issue-takes-the-issue-key-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-one-mcp-tool-call-yields-one-trace-in-tempo-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-refactor-sweep-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-integrated-check-on-kind-plan.md
  - _bmad-output/test-artifacts/test-design/test-design-epic-4.md
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/epic-mcp-server.md
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-tracer-an-mcp-client-calls-search-similar-issues-through-the-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-claude-desktop-answers-from-ticketscope-through-a-tunnel-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-tool-errors-carry-the-api-s-problem-detail-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-get-issue-takes-the-issue-key-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-one-mcp-tool-call-yields-one-trace-in-tempo-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-refactor-sweep-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-integrated-check-on-kind-plan.md
  - _bmad-output/test-artifacts/test-design/test-design-epic-4.md
  - _bmad-output/test-artifacts/live-verification-results.json
  - _bmad-output/test-artifacts/gate-waivers.md
criterionLedger:
  - {"id": "ticketscope--e4-s1--AC-1", "localId": "AC-1", "story": "ticketscope--e4-s1", "name": "Given a PR touching kind paths, when `mcp-e2e.yml` runs, then it deploys to kind and `pytest -m kind tests/mcp` passes: tools/list; a no-mode call whose `mode` equals `retrieval.defaultMode`; a `mode=keyword` call equal to direct `POST /v1/search`; each result valid against the advertised `outputSchema`; a call with no `initialize`; 20 fresh-connection calls with tool-call logs on both pods; a foreign Host refused", "text": "Given a PR touching kind paths, when `mcp-e2e.yml` runs, then it deploys to kind and `pytest -m kind tests/mcp` passes: tools/list; a no-mode call whose `mode` equals `retrieval.defaultMode`; a `mode=keyword` call equal to direct `POST /v1/search`; each result valid against the advertised `outputSchema`; a call with no `initialize`; 20 fresh-connection calls with tool-call logs on both pods; a foreign Host refused (R1).", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-tracer-an-mcp-client-calls-search-similar-issues-through-the-plan.md:85", "priority": "P0", "priorityBasis": "inferred", "declaredLinks": ["R1"], "validLinks": ["R1"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s1--AC-2", "localId": "AC-2", "story": "ticketscope--e4-s1", "name": "Given the in-process server and a fake `/v1`, when a tool call omits `mode`, then the fake receives no `mode` key; given `mode=\"bogus\"`, then it receives `\"bogus\"`", "text": "Given the in-process server and a fake `/v1`, when a tool call omits `mode`, then the fake receives no `mode` key; given `mode=\"bogus\"`, then it receives `\"bogus\"` (R1, R-005).", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-tracer-an-mcp-client-calls-search-similar-issues-through-the-plan.md:86", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R1"], "validLinks": ["R1"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s1--AC-3", "localId": "AC-3", "story": "ticketscope--e4-s1", "name": "Given `helm template` with kind values, when rendered, then the `mcp` Deployment has 2 replicas, probes that never call api, no database Secret, the in-cluster API URL, and hosts from values; given `*` or no hosts, then render fails", "text": "Given `helm template` with kind values, when rendered, then the `mcp` Deployment has 2 replicas, probes that never call api, no database Secret, the in-cluster API URL, and hosts from values; given `*` or no hosts, then render fails (R1).", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-tracer-an-mcp-client-calls-search-similar-issues-through-the-plan.md:87", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R1"], "validLinks": ["R1"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s1--AC-4", "localId": "AC-4", "story": "ticketscope--e4-s1", "name": "Given a same-tag image rebuild, when `kind-up.sh` finishes, then `ticketscope-mcp` was restarted and is Ready", "text": "Given a same-tag image rebuild, when `kind-up.sh` finishes, then `ticketscope-mcp` was restarted and is Ready (R1, R-011).", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-tracer-an-mcp-client-calls-search-similar-issues-through-the-plan.md:88", "priority": "P2", "priorityBasis": "inferred", "declaredLinks": ["R1"], "validLinks": ["R1"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s1--AC-5", "localId": "AC-5", "story": "ticketscope--e4-s1", "name": "Given the changes, when `uv run lint-imports`, ruff, pyright and `pytest` run, then all pass with 10 contracts kept, and `ci.yml`'s `charts` job lists the new chart tests", "text": "Given the changes, when `uv run lint-imports`, ruff, pyright and `pytest` run, then all pass with 10 contracts kept, and `ci.yml`'s `charts` job lists the new chart tests (R1).", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-tracer-an-mcp-client-calls-search-similar-issues-through-the-plan.md:89", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R1"], "validLinks": ["R1"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s2--AC-1", "localId": "AC-1", "story": "ticketscope--e4-s2", "name": "Given the stand-in host in kind values, when `mcp-e2e.yml` sends `tools/list` with it, then `/mcp` answers 200, `/v1/search` and `/` answer 404, and `ticketscope.kind.internal` still works.", "text": "Given the stand-in host in kind values, when `mcp-e2e.yml` sends `tools/list` with it, then `/mcp` answers 200, `/v1/search` and `/` answer 404, and `ticketscope.kind.internal` still works.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-claude-desktop-answers-from-ticketscope-through-a-tunnel-plan.md:75", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R4"], "validLinks": ["R4"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s2--AC-2", "localId": "AC-2", "story": "ticketscope--e4-s2", "name": "Given the tunnel value unset, when the charts render, then no extra listener, route host or allowed host appears.", "text": "Given the tunnel value unset, when the charts render, then no extra listener, route host or allowed host appears.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-claude-desktop-answers-from-ticketscope-through-a-tunnel-plan.md:76", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R4"], "validLinks": ["R4"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s2--AC-3", "localId": "AC-3", "story": "ticketscope--e4-s2", "name": "Given the captured requests, when `mcp-e2e.yml` replays them, then they pass and no credential appears in them.", "text": "Given the captured requests, when `mcp-e2e.yml` replays them, then they pass and no credential appears in them.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-claude-desktop-answers-from-ticketscope-through-a-tunnel-plan.md:77", "priority": "P0", "priorityBasis": "inferred", "declaredLinks": ["R4"], "validLinks": ["R4"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s2--AC-4", "localId": "AC-4", "story": "ticketscope--e4-s2", "name": "Given the script has exited, when the tunnel hostname is requested, then it no longer reaches the cluster.", "text": "Given the script has exited, when the tunnel hostname is requested, then it no longer reaches the cluster.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-claude-desktop-answers-from-ticketscope-through-a-tunnel-plan.md:78", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R4"], "validLinks": ["R4"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s2--AC-5", "localId": "AC-5", "story": "ticketscope--e4-s2", "name": "Given a person's Claude Desktop session, when they ask a triage question, then a committed screenshot shows the tool call and an answer citing returned issues.", "text": "Given a person's Claude Desktop session, when they ask a triage question, then a committed screenshot shows the tool call and an answer citing returned issues.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-claude-desktop-answers-from-ticketscope-through-a-tunnel-plan.md:79", "priority": "P0", "priorityBasis": "inferred", "declaredLinks": ["R4"], "validLinks": ["R4"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s3--AC-1", "localId": "AC-1", "story": "ticketscope--e4-s3", "name": "Given an unknown mode, when the tool is called on kind, then `is_error` is true and its text equals the API's 422 detail.", "text": "Given an unknown mode, when the tool is called on kind, then `is_error` is true and its text equals the API's 422 detail.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-tool-errors-carry-the-api-s-problem-detail-plan.md:67", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R3"], "validLinks": ["R3"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s3--AC-2", "localId": "AC-2", "story": "ticketscope--e4-s3", "name": "Given any of 422, 404, 500, 503, refused connection, timeout, HTML 502, or a 200 failing the contract, when the tool is called, then the result is `isError: true` with the specified text and no JSON-RPC `error`.", "text": "Given any of 422, 404, 500, 503, refused connection, timeout, HTML 502, or a 200 failing the contract, when the tool is called, then the result is `isError: true` with the specified text and no JSON-RPC `error`.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-tool-errors-carry-the-api-s-problem-detail-plan.md:68", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R3"], "validLinks": ["R3"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s3--AC-3", "localId": "AC-3", "story": "ticketscope--e4-s3", "name": "Given a successful call, then structured output, text block and outputSchema are unchanged and `mcp-e2e.yml`'s Claude Desktop replay still passes.", "text": "Given a successful call, then structured output, text block and outputSchema are unchanged and `mcp-e2e.yml`'s Claude Desktop replay still passes.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-tool-errors-carry-the-api-s-problem-detail-plan.md:69", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R1", "R3"], "validLinks": ["R1", "R3"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s4--AC-1", "localId": "AC-1", "story": "ticketscope--e4-s4", "name": "Given a search result's key, when `get_issue` is called with it, then the issue with that key and its outcome returns, valid against the generated schema.", "text": "Given a search result's key, when `get_issue` is called with it, then the issue with that key and its outcome returns, valid against the generated schema.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-get-issue-takes-the-issue-key-plan.md:75", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R2"], "validLinks": ["R2"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s4--AC-2", "localId": "AC-2", "story": "ticketscope--e4-s4", "name": "Given an unknown key, when `get_issue` is called, then `is_error` carries the API's detail.", "text": "Given an unknown key, when `get_issue` is called, then `is_error` carries the API's detail.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-get-issue-takes-the-issue-key-plan.md:76", "priority": "P0", "priorityBasis": "inferred", "declaredLinks": ["R3"], "validLinks": ["R3"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s4--AC-3", "localId": "AC-3", "story": "ticketscope--e4-s4", "name": "Given any hostile key, when `get_issue` is called, then `is_error` and no other issue is fetched.", "text": "Given any hostile key, when `get_issue` is called, then `is_error` and no other issue is fetched.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-get-issue-takes-the-issue-key-plan.md:77", "priority": "P0", "priorityBasis": "inferred", "declaredLinks": ["R2", "R3"], "validLinks": ["R2", "R3"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s4--AC-4", "localId": "AC-4", "story": "ticketscope--e4-s4", "name": "Given two bodies differing only in `issue.key`, when the parity script compares with the option, then it passes; any other difference fails.", "text": "Given two bodies differing only in `issue.key`, when the parity script compares with the option, then it passes; any other difference fails.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-get-issue-takes-the-issue-key-plan.md:78", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R2"], "validLinks": ["R2"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s4--AC-5", "localId": "AC-5", "story": "ticketscope--e4-s4", "name": "Given the existing suite, when run, then it passes with `eval/baseline.json` unchanged.", "text": "Given the existing suite, when run, then it passes with `eval/baseline.json` unchanged.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-get-issue-takes-the-issue-key-plan.md:79", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R2"], "validLinks": ["R2"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s5--AC-1", "localId": "AC-1", "story": "ticketscope--e4-s5", "name": "Given a `search_similar_issues` call with no caller context, when the trace is read from Tempo on kind, then one trace has the `ticketscope-mcp` tool span as its root with the CLIENT `POST`, `api`'s `POST /v1/search`, `retrieval hybrid`, `embeddings {model}` and the db query beneath it.", "text": "Given a `search_similar_issues` call with no caller context, when the trace is read from Tempo on kind, then one trace has the `ticketscope-mcp` tool span as its root with the CLIENT `POST`, `api`'s `POST /v1/search`, `retrieval hybrid`, `embeddings {model}` and the db query beneath it.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-one-mcp-tool-call-yields-one-trace-in-tempo-plan.md:73", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R5"], "validLinks": ["R5"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s5--AC-2", "localId": "AC-2", "story": "ticketscope--e4-s5", "name": "Given `_meta.traceparent` (alone, or with a different HTTP `traceparent`), when a tool is called, then the tool span's trace id is the `_meta` one.", "text": "Given `_meta.traceparent` (alone, or with a different HTTP `traceparent`), when a tool is called, then the tool span's trace id is the `_meta` one.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-one-mcp-tool-call-yields-one-trace-in-tempo-plan.md:74", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R5"], "validLinks": ["R5"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s5--AC-3", "localId": "AC-3", "story": "ticketscope--e4-s5", "name": "Given a tool error, when the span is read, then its status is ERROR; and `get_issue` yields its own trace the same way.", "text": "Given a tool error, when the span is read, then its status is ERROR; and `get_issue` yields its own trace the same way.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-one-mcp-tool-call-yields-one-trace-in-tempo-plan.md:75", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R5"], "validLinks": ["R5"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s5--AC-4", "localId": "AC-4", "story": "ticketscope--e4-s5", "name": "Given default settings, when any tool is called, then no span carries query text, and the tool span's attribute keys equal the constants list.", "text": "Given default settings, when any tool is called, then no span carries query text, and the tool span's attribute keys equal the constants list.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-one-mcp-tool-call-yields-one-trace-in-tempo-plan.md:76", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R5"], "validLinks": ["R5"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s5--AC-5", "localId": "AC-5", "story": "ticketscope--e4-s5", "name": "Given `apiclient` in a unit test, when it sends a request inside a tool span, then the outgoing `traceparent` carries the tool span's trace id.", "text": "Given `apiclient` in a unit test, when it sends a request inside a tool span, then the outgoing `traceparent` carries the tool span's trace id.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-one-mcp-tool-call-yields-one-trace-in-tempo-plan.md:77", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R5"], "validLinks": ["R5"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s5--AC-6", "localId": "AC-6", "story": "ticketscope--e4-s5", "name": "Given the existing suite, when run (`pytest`, `lint-imports`, ruff, pyright), then it passes, including the Claude Desktop replay and captured-pin tests.", "text": "Given the existing suite, when run (`pytest`, `lint-imports`, ruff, pyright), then it passes, including the Claude Desktop replay and captured-pin tests.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-one-mcp-tool-call-yields-one-trace-in-tempo-plan.md:78", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R1", "R5"], "validLinks": ["R1", "R5"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s6--AC-1", "localId": "AC-1", "story": "ticketscope--e4-s6", "name": "Given the refactor, when `helm template` runs, then output equals the pre-change render.", "text": "Given the refactor, when `helm template` runs, then output equals the pre-change render.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-refactor-sweep-plan.md:51", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R1", "R2", "R3", "R5"], "validLinks": ["R1", "R2", "R3", "R5"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s6--AC-2", "localId": "AC-2", "story": "ticketscope--e4-s6", "name": "Given the refactor, when unit tests, ruff, pyright and lint-imports run, then all pass.", "text": "Given the refactor, when unit tests, ruff, pyright and lint-imports run, then all pass.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-refactor-sweep-plan.md:52", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R1", "R2", "R3", "R5"], "validLinks": ["R1", "R2", "R3", "R5"], "invalidLinks": [], "exception": "none"}
  - {"id": "ticketscope--e4-s7--verify", "localId": "verify", "story": "ticketscope--e4-s7", "name": "On a fresh kind cluster, mcp-e2e.yml's integrated suite passes in CI covering each Done when line of the epic that CI can run (R1, R2, R3, R5), including the Claude Desktop replay (R4); with api at zero, mcp stays Ready and the tool returns is_error with the unreachable detail within the timeout plus a margin, not a Gateway 503, and api is restored afterwards (R3); the epic's Notes link story 2's recorded Claude Desktop session for R4 and cite this story's mcp-e2e.yml run URL as the CI evidence (C-7).", "text": "On a fresh kind cluster, mcp-e2e.yml's integrated suite passes in CI covering each Done when line of the epic that CI can run (R1, R2, R3, R5), including the Claude Desktop replay (R4); with api at zero, mcp stays Ready and the tool returns is_error with the unreachable detail within the timeout plus a margin, not a Gateway 503, and api is restored afterwards (R3); the epic's Notes link story 2's recorded Claude Desktop session for R4 and cite this story's mcp-e2e.yml run URL as the CI evidence (C-7).", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/tickets.toml:91", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": ["R1", "R2", "R3", "R4", "R5"], "validLinks": ["R1", "R2", "R3", "R4", "R5"], "invalidLinks": [], "exception": "none"}
oracleLedger:
  - {"id": "ticketscope--e4--R1", "kind": "requirement", "requirement": "An MCP client calls `search_similar_issues` with a query and an optional mode and k on the remote server at `/mcp`, and receives the `/v1/search` body as structured output whose schema is generated from `ticketscope.contract`. It is met when the CI client test on kind calls it with and without a mode and the results validate against that schema.", "parent": "parent R4", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/epic-mcp-server.md:32", "priority": "P0", "priorityBasis": "contributors", "contributors": ["ticketscope--e4-s1--AC-1", "ticketscope--e4-s1--AC-2", "ticketscope--e4-s1--AC-3", "ticketscope--e4-s1--AC-4", "ticketscope--e4-s1--AC-5", "ticketscope--e4-s3--AC-3", "ticketscope--e4-s5--AC-6", "ticketscope--e4-s6--AC-1", "ticketscope--e4-s6--AC-2", "ticketscope--e4-s7--verify"]}
  - {"id": "ticketscope--e4--R2", "kind": "requirement", "requirement": "An MCP client calls `get_issue` with an issue's readable key and receives that issue and its outcome as structured output. It is met when the CI client test takes a key from a search result, fetches it, and gets the issue with that key back.", "parent": "parent R4", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/epic-mcp-server.md:33", "priority": "P0", "priorityBasis": "contributors", "contributors": ["ticketscope--e4-s4--AC-1", "ticketscope--e4-s4--AC-3", "ticketscope--e4-s4--AC-4", "ticketscope--e4-s4--AC-5", "ticketscope--e4-s6--AC-1", "ticketscope--e4-s6--AC-2", "ticketscope--e4-s7--verify"]}
  - {"id": "ticketscope--e4--R3", "kind": "requirement", "requirement": "A failed tool call comes back as an MCP tool error carrying the API's problem detail, never as a protocol failure or an empty result. It is met when an unknown mode, an unknown key and an unreachable API each return a tool error with that detail in the CI client test.", "parent": "parent R4", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/epic-mcp-server.md:34", "priority": "P0", "priorityBasis": "contributors", "contributors": ["ticketscope--e4-s3--AC-1", "ticketscope--e4-s3--AC-2", "ticketscope--e4-s3--AC-3", "ticketscope--e4-s4--AC-2", "ticketscope--e4-s4--AC-3", "ticketscope--e4-s6--AC-1", "ticketscope--e4-s6--AC-2", "ticketscope--e4-s7--verify"]}
  - {"id": "ticketscope--e4--R4", "kind": "requirement", "requirement": "Claude Desktop, connected through a tunnel with a fixed hostname to the kind cluster, calls `search_similar_issues` and answers from its results. It is met when a recorded session shows the tool call and an answer citing returned issues.", "parent": "parent R4", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/epic-mcp-server.md:35", "priority": "P0", "priorityBasis": "contributors", "contributors": ["ticketscope--e4-s2--AC-1", "ticketscope--e4-s2--AC-2", "ticketscope--e4-s2--AC-3", "ticketscope--e4-s2--AC-4", "ticketscope--e4-s2--AC-5", "ticketscope--e4-s7--verify"]}
  - {"id": "ticketscope--e4--R5", "kind": "requirement", "requirement": "One trace spans the MCP tool call, the HTTP hop to the API, retrieval and the database, and continues the caller's trace context from the MCP request's `_meta` when present. It is met when a CI check on kind finds one trace in Tempo with that span tree under a `ticketscope-mcp` root, and a call carrying a `traceparent` in `_meta` lands in the caller's trace.", "parent": "parent R8", "source": "_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/epic-mcp-server.md:36", "priority": "P1", "priorityBasis": "contributors", "contributors": ["ticketscope--e4-s5--AC-1", "ticketscope--e4-s5--AC-2", "ticketscope--e4-s5--AC-3", "ticketscope--e4-s5--AC-4", "ticketscope--e4-s5--AC-5", "ticketscope--e4-s5--AC-6", "ticketscope--e4-s6--AC-1", "ticketscope--e4-s6--AC-2", "ticketscope--e4-s7--verify"]}
---

# Traceability Matrix & Gate Decision — Epic 4: Claude Desktop calls search_similar_issues on a remote MCP server

## Gate Decision: FAIL

**Rationale:** P0 coverage is 0% (required: 100%). 4 critical requirement(s) below FULL coverage. All four P0 requirements (R1 to R4) are PARTIAL, and R5 (P1) is PARTIAL too. Overall FULL coverage is 0% (minimum 80%) and P1 is 0% (minimum 80%).

Of the 27 criteria, 18 are FULL, 8 are PARTIAL and 1 is NONE. The nine that fall short are:

- story 1: AC-4 (`kind-up.sh` restarts `mcp`) and AC-5 (`ruff`, `pyright` and `pytest` pass);
- story 2: AC-4 (the tunnel hostname stops reaching the cluster) and AC-5 (Claude Desktop answers; NONE);
- story 4: AC-5 (suite passes, `eval/baseline.json` unchanged);
- story 5: AC-6 (suite passes, replay and pin tests);
- story 6: AC-1 (render equals the pre-change render) and AC-2 (checks pass);
- story 7: verify.

**Date:** 2026-11-12. **Evaluator:** Claude Code / Master Test Architect. **Source:** `4dccc85d66f3e85682c6b43e3e673a93f61cbe51` (`main`, clean). **Gate type:** epic. This is the first trace for this key.

**What the FAIL means.** The behaviour the epic builds is well covered: 18 of 27 criteria are FULL, including every P0 behaviour a test can reach (the `get_issue` key guarantees, the captured Claude Desktop replay and pin, and the tool's `/v1` body on kind). A requirement is FULL only when every contributor is FULL, and every requirement here has at least one contributor whose clause is a process observation, so none reaches FULL:

- a PR's CI run passing (`ruff`, `pyright`, `pytest`, `eval/baseline.json` unchanged);
- a person's Claude Desktop session and the tunnel going away after the script exits;
- a same-tag `kind-up.sh` rebuild with `mcp` deployed;
- the `helm template` output matching the pre-refactor render.

Trace never records live verification itself, and `live-verification-results.json` holds no epic 4 records. The R4 gap is the largest: story 2 AC-5 is a P0 criterion with no test and no live record, because the screenshot was waived and the session is recorded only in the plan's prose.

**How to close it:**

1. Record live verification at the commit under trace for the process clauses (story 2 AC-4 and AC-5, story 1 AC-5, story 4 AC-5, story 5 AC-6, story 6 AC-2, story 7 verify), citing CI runs such as `mcp-e2e` run 43252341547. These alone lift R1 to R5 toward FULL, but live-only evidence caps the run at CONCERNS.
2. Add three small static tests that make the live clauses re-runnable: a stubbed `kind-up.sh` run for `mcp` (story 1 AC-4), a before/after `helm template` comparison over default, kind and tunnel-host values (story 6 AC-1), and a check that the diff leaves `eval/baseline.json` untouched (story 4 AC-5).
3. Have the PO add the two links the epic Notes still lack: story 2's recorded session and the `mcp-e2e.yml` run URL (story 7, C-7). Fix the marker in `tests/mcp/test_unreachable_api.py:25` to `ticketscope--e4-s7--verify`.

## Coverage Summary

| Priority | Total | FULL | Coverage |
| --- | ---: | ---: | ---: |
| P0 | 4 | 0 | 0% |
| P1 | 1 | 0 | 0% |
| P2 | 0 | 0 | 100% |
| P3 | 0 | 0 | 100% |
| Overall | 5 | 0 | 0% |

Gate rows: 0 FULL, 5 PARTIAL, 0 NONE.

Criteria: 18 FULL, 8 PARTIAL, 1 NONE (67% FULL).

Accepted evidence: 89 test cases across 20 files: 20 e2e (kind), 35 API (in-process MCP server or `/v1` app over ASGI/TestClient), 25 unit, 2 integration (Postgres), 7 other (static file checks). Kind and Postgres tests are accepted as static evidence under `collection_mode: contract_static`. This trace did not run them. Their latest results are informational:

- `mcp-e2e` run 43252341547 (PR #66, story 4.7 head `5a6a0af`, merged as `4dccc85`): its `mcp-e2e / deploy` job succeeded, so the integrated suite, including the unreachable case, passed on that head. The later `mcp-e2e` runs on the epic 5 refine PR finished in 8 seconds, which suggests the kind path filter skipped them; they are not evidence.
- `ci` run 43252341626 (PR #66): success.

Local sanity run at HEAD (informational, not counted): `uv run pytest` 1341 passed, 36 skipped, 82 deselected; `uv run lint-imports` 10 kept, 0 broken. The chart tests skip without `helm`; `ci.yml`'s `charts` job runs them with the pinned Helm.

**Oracle.** The oracle is the formal epic requirements R1 to R5, at requirement granularity: a v7 epic with `R<n>` lines and no duplicate ids. Criteria come from each plan's Acceptance Criteria:

- stories 1 to 6 have Acceptance Criteria;
- story 7's plan has none, so its `tickets.toml` `verify` line is the criterion (`-verify`).

Declared links come from the `(R<n>)` tags in each ticket's `verify` text. Where an AC names no requirement, its ticket's `covers` applies. Story 6 has `covers = []`, and its `verify` text tags R1, R2, R3 and R5, so those tags are its links. No criterion is unlinked or invalid-linked.

Criterion priorities are inferred from `test-design-epic-4.md`'s coverage plan, because no plan states one:

- P0: rows (A) `get_issue` returns exactly the issue its key names, (B) Claude Desktop answers and its requests keep working, and (C) `search_similar_issues` returns the `/v1/search` body on kind;
- P1: tunnel admission, the exposed-routes check, the 422 detail, tool errors, chart renders, layering, the trace rows, the closing check and the sweep;
- P2: `kind-up.sh` bring-up.

A requirement takes the highest priority among its contributors.

**Supporting audits:** none exists for epic 4. There is no NFR assessment and no test review, so neither is read.

**Live results.** `live-verification-results.json` holds 30 records, all for epics 1 to 3, recorded at other commits. None names an epic 4 criterion, and none is counted. They are reported once as unmatched in the summary's blockers.

## Requirement Oracle Mapping

| ID | Requirement | Priority | Coverage |
| --- | --- | --- | --- |
| ticketscope--e4--R1 | An MCP client calls `search_similar_issues` with a query and an optional mode and k on the remote server at `/mcp`, and receives the `/v1/search` body as structured output whose schema is generated from `ticketscope.contract`. It is met when the CI client test on kind calls it with and without a mode and the results validate against that schema. | P0 | PARTIAL |
| ticketscope--e4--R2 | An MCP client calls `get_issue` with an issue's readable key and receives that issue and its outcome as structured output. It is met when the CI client test takes a key from a search result, fetches it, and gets the issue with that key back. | P0 | PARTIAL |
| ticketscope--e4--R3 | A failed tool call comes back as an MCP tool error carrying the API's problem detail, never as a protocol failure or an empty result. It is met when an unknown mode, an unknown key and an unreachable API each return a tool error with that detail in the CI client test. | P0 | PARTIAL |
| ticketscope--e4--R4 | Claude Desktop, connected through a tunnel with a fixed hostname to the kind cluster, calls `search_similar_issues` and answers from its results. It is met when a recorded session shows the tool call and an answer citing returned issues. | P0 | PARTIAL |
| ticketscope--e4--R5 | One trace spans the MCP tool call, the HTTP hop to the API, retrieval and the database, and continues the caller's trace context from the MCP request's `_meta` when present. It is met when a CI check on kind finds one trace in Tempo with that span tree under a `ticketscope-mcp` root, and a call carrying a `traceparent` in `_meta` lands in the caller's trace. | P1 | PARTIAL |

## Detailed Mapping

### ticketscope--e4--R1 (P0): An MCP client calls `search_similar_issues` with a query and an optional mode and k on the remote server at `/mcp`, and receives the `/v1/search` body as structured output whose schema is generated from `ticketscope.contract`. It is met when the CI client test on kind calls it with and without a mode and the results validate against that schema.

- **Coverage:** PARTIAL ⚠️
- **Parent:** parent R4
- **Priority basis:** contributors
- **Missing behaviors:** None
- **Contributors:** the table below, one row per contributor.

| Contributor | Story | Status | Tests |
| --- | --- | --- | --- |
| ticketscope--e4-s1--AC-1 | ticketscope--e4-s1 | FULL | `tests/mcp/test_search_tool.py:79` `tests/mcp/test_search_tool.py:90` `tests/mcp/test_search_tool.py:96` `tests/mcp/test_search_tool.py:119` `tests/mcp/test_search_tool.py:172` `tests/mcp/test_search_tool.py:223` `tests/unit/test_mcp_workflow.py:14` |
| ticketscope--e4-s1--AC-2 | ticketscope--e4-s1 | FULL | `tests/unit/test_mcp_server.py:77` `tests/unit/test_mcp_server.py:91` `tests/unit/test_apiclient.py:37` `tests/unit/test_apiclient.py:44` |
| ticketscope--e4-s1--AC-3 | ticketscope--e4-s1 | FULL | `tests/unit/test_chart_mcp.py:26` `tests/unit/test_chart_mcp.py:35` `tests/unit/test_chart_mcp.py:41` `tests/unit/test_chart_mcp.py:47` `tests/unit/test_chart_mcp.py:57` |
| ticketscope--e4-s1--AC-4 | ticketscope--e4-s1 | PARTIAL | `tests/unit/test_mcp_workflow.py:39` |
| ticketscope--e4-s1--AC-5 | ticketscope--e4-s1 | PARTIAL | `tests/unit/test_import_linter_enforcement.py:46` `tests/unit/test_mcp_workflow.py:35` |
| ticketscope--e4-s3--AC-3 | ticketscope--e4-s3 | FULL | `tests/unit/test_mcp_server.py:77` `tests/unit/test_mcp_server.py:208` `tests/unit/test_mcp_server.py:65` `tests/mcp/test_claude_desktop_replay.py:72` `tests/mcp/test_claude_desktop_replay.py:80` |
| ticketscope--e4-s5--AC-6 | ticketscope--e4-s5 | PARTIAL | `tests/unit/test_mcp_captured_pin.py:27` `tests/mcp/test_claude_desktop_replay.py:80` `tests/unit/test_import_linter_enforcement.py:46` |
| ticketscope--e4-s6--AC-1 | ticketscope--e4-s6 | PARTIAL | `tests/unit/test_chart_mcp.py:26` `tests/unit/test_chart_mcp.py:47` `tests/unit/test_chart_tunnel_listener.py:37` |
| ticketscope--e4-s6--AC-2 | ticketscope--e4-s6 | PARTIAL | `tests/unit/test_import_linter_enforcement.py:46` `tests/unit/test_mcp_tempo_helper.py:52` `tests/unit/test_mcp_tempo_helper.py:60` |
| ticketscope--e4-s7--verify | ticketscope--e4-s7 | PARTIAL | `tests/mcp/test_unreachable_api.py:70` `tests/mcp/test_search_tool.py:239` `tests/mcp/test_search_tool.py:102` `tests/mcp/test_claude_desktop_replay.py:60` `tests/mcp/test_trace.py:151` `tests/unit/test_mcp_workflow.py:14` |

- **Gaps:** s1 AC-4 is PARTIAL; s1 AC-5 is PARTIAL; s5 AC-6 is PARTIAL; s6 AC-1 is PARTIAL; s6 AC-2 is PARTIAL; s7 verify is PARTIAL. All behaviours the line states are covered by FULL contributors: the tool call with and without a mode, the `/v1/search` body as structured output, and validation against the generated schema (s1 AC-1). R1 is PARTIAL only through the process contributors.
- **Recommendation:** Record live results for s1 AC-5, s5 AC-6, s6 and s7, and add a stubbed `kind-up.sh` test for `mcp` (s1 AC-4).

### ticketscope--e4--R2 (P0): An MCP client calls `get_issue` with an issue's readable key and receives that issue and its outcome as structured output. It is met when the CI client test takes a key from a search result, fetches it, and gets the issue with that key back.

- **Coverage:** PARTIAL ⚠️
- **Parent:** parent R4
- **Priority basis:** contributors
- **Missing behaviors:** None
- **Contributors:** the table below, one row per contributor.

| Contributor | Story | Status | Tests |
| --- | --- | --- | --- |
| ticketscope--e4-s4--AC-1 | ticketscope--e4-s4 | FULL | `tests/mcp/test_search_tool.py:239` `tests/unit/test_get_issue_by_key.py:216` `tests/postgres/test_issue_by_key_postgres.py:49` |
| ticketscope--e4-s4--AC-3 | ticketscope--e4-s4 | FULL | `tests/unit/test_get_issue_by_key.py:233` `tests/unit/test_get_issue_by_key.py:243` `tests/unit/test_get_issue_by_key_expanded.py:138` `tests/unit/test_get_issue_by_key.py:271` `tests/unit/test_get_issue_by_key.py:152` `tests/unit/test_get_issue_by_key_expanded.py:79` `tests/unit/test_get_issue_by_key.py:253` `tests/unit/test_get_issue_by_key.py:262` `tests/postgres/test_issue_by_key_postgres.py:59` `tests/unit/test_key_oracle_pinned.py:45` `tests/unit/test_key_oracle_pinned.py:34` |
| ticketscope--e4-s4--AC-4 | ticketscope--e4-s4 | FULL | `tests/unit/test_get_issue_by_key.py:316` `tests/unit/test_get_issue_by_key.py:322` `tests/unit/test_get_issue_by_key_expanded.py:161` |
| ticketscope--e4-s4--AC-5 | ticketscope--e4-s4 | PARTIAL | `tests/unit/test_get_issue_by_key.py:98` `tests/unit/test_get_issue_by_key.py:128` `tests/unit/test_get_issue_by_key.py:137` |
| ticketscope--e4-s6--AC-1 | ticketscope--e4-s6 | PARTIAL | `tests/unit/test_chart_mcp.py:26` `tests/unit/test_chart_mcp.py:47` `tests/unit/test_chart_tunnel_listener.py:37` |
| ticketscope--e4-s6--AC-2 | ticketscope--e4-s6 | PARTIAL | `tests/unit/test_import_linter_enforcement.py:46` `tests/unit/test_mcp_tempo_helper.py:52` `tests/unit/test_mcp_tempo_helper.py:60` |
| ticketscope--e4-s7--verify | ticketscope--e4-s7 | PARTIAL | `tests/mcp/test_unreachable_api.py:70` `tests/mcp/test_search_tool.py:239` `tests/mcp/test_search_tool.py:102` `tests/mcp/test_claude_desktop_replay.py:60` `tests/mcp/test_trace.py:151` `tests/unit/test_mcp_workflow.py:14` |

- **Gaps:** s4 AC-5 is PARTIAL; s6 AC-1 is PARTIAL; s6 AC-2 is PARTIAL; s7 verify is PARTIAL. Every stated behaviour is covered: a key taken from a search, fetched with `get_issue`, returns the issue with that key and its outcome (s4 AC-1). R2 is PARTIAL only through the process contributors.
- **Recommendation:** Record live results for s4 AC-5, s6 and s7 with the CI run URLs, and add a test that the diff leaves `eval/baseline.json` untouched.

### ticketscope--e4--R3 (P0): A failed tool call comes back as an MCP tool error carrying the API's problem detail, never as a protocol failure or an empty result. It is met when an unknown mode, an unknown key and an unreachable API each return a tool error with that detail in the CI client test.

- **Coverage:** PARTIAL ⚠️
- **Parent:** parent R4
- **Priority basis:** contributors
- **Missing behaviors:** None
- **Contributors:** the table below, one row per contributor.

| Contributor | Story | Status | Tests |
| --- | --- | --- | --- |
| ticketscope--e4-s3--AC-1 | ticketscope--e4-s3 | FULL | `tests/mcp/test_search_tool.py:102` |
| ticketscope--e4-s3--AC-2 | ticketscope--e4-s3 | FULL | `tests/unit/test_apiclient.py:100` `tests/unit/test_apiclient.py:128` `tests/unit/test_apiclient.py:151` `tests/unit/test_apiclient.py:167` `tests/unit/test_mcp_expanded.py:62` `tests/unit/test_mcp_expanded.py:86` `tests/unit/test_mcp_expanded.py:116` `tests/unit/test_mcp_expanded.py:27` `tests/unit/test_mcp_expanded.py:54` |
| ticketscope--e4-s3--AC-3 | ticketscope--e4-s3 | FULL | `tests/unit/test_mcp_server.py:77` `tests/unit/test_mcp_server.py:208` `tests/unit/test_mcp_server.py:65` `tests/mcp/test_claude_desktop_replay.py:72` `tests/mcp/test_claude_desktop_replay.py:80` |
| ticketscope--e4-s4--AC-2 | ticketscope--e4-s4 | FULL | `tests/mcp/test_search_tool.py:239` `tests/unit/test_get_issue_by_key.py:226` `tests/unit/test_get_issue_by_key.py:144` |
| ticketscope--e4-s4--AC-3 | ticketscope--e4-s4 | FULL | `tests/unit/test_get_issue_by_key.py:233` `tests/unit/test_get_issue_by_key.py:243` `tests/unit/test_get_issue_by_key_expanded.py:138` `tests/unit/test_get_issue_by_key.py:271` `tests/unit/test_get_issue_by_key.py:152` `tests/unit/test_get_issue_by_key_expanded.py:79` `tests/unit/test_get_issue_by_key.py:253` `tests/unit/test_get_issue_by_key.py:262` `tests/postgres/test_issue_by_key_postgres.py:59` `tests/unit/test_key_oracle_pinned.py:45` `tests/unit/test_key_oracle_pinned.py:34` |
| ticketscope--e4-s6--AC-1 | ticketscope--e4-s6 | PARTIAL | `tests/unit/test_chart_mcp.py:26` `tests/unit/test_chart_mcp.py:47` `tests/unit/test_chart_tunnel_listener.py:37` |
| ticketscope--e4-s6--AC-2 | ticketscope--e4-s6 | PARTIAL | `tests/unit/test_import_linter_enforcement.py:46` `tests/unit/test_mcp_tempo_helper.py:52` `tests/unit/test_mcp_tempo_helper.py:60` |
| ticketscope--e4-s7--verify | ticketscope--e4-s7 | PARTIAL | `tests/mcp/test_unreachable_api.py:70` `tests/mcp/test_search_tool.py:239` `tests/mcp/test_search_tool.py:102` `tests/mcp/test_claude_desktop_replay.py:60` `tests/mcp/test_trace.py:151` `tests/unit/test_mcp_workflow.py:14` |

- **Gaps:** s6 AC-1 is PARTIAL; s6 AC-2 is PARTIAL; s7 verify is PARTIAL. Every stated behaviour is covered by contributors: an unknown mode (s3 AC-1), an unknown key (s4 AC-2) and an unreachable API (s3 AC-2 in process; s7 verify on kind) each return a tool error with the detail. R3 is PARTIAL only through the process contributors.
- **Recommendation:** Record a live result for s7 verify, and for s6 (the two process clauses).

### ticketscope--e4--R4 (P0): Claude Desktop, connected through a tunnel with a fixed hostname to the kind cluster, calls `search_similar_issues` and answers from its results. It is met when a recorded session shows the tool call and an answer citing returned issues.

- **Coverage:** PARTIAL ⚠️
- **Parent:** parent R4
- **Priority basis:** contributors
- **Missing behaviors:** None
- **Contributors:** the table below, one row per contributor.

| Contributor | Story | Status | Tests |
| --- | --- | --- | --- |
| ticketscope--e4-s2--AC-1 | ticketscope--e4-s2 | FULL | `tests/mcp/test_search_tool.py:206` `tests/mcp/test_search_tool.py:218` `tests/mcp/test_search_tool.py:212` |
| ticketscope--e4-s2--AC-2 | ticketscope--e4-s2 | FULL | `tests/unit/test_chart_tunnel_listener.py:32` `tests/unit/test_chart_mcp.py:101` `tests/unit/test_chart_mcp.py:121` |
| ticketscope--e4-s2--AC-3 | ticketscope--e4-s2 | FULL | `tests/mcp/test_claude_desktop_replay.py:60` `tests/unit/test_mcp_captured_pin.py:35` `tests/unit/test_mcp_captured_pin.py:27` |
| ticketscope--e4-s2--AC-4 | ticketscope--e4-s2 | PARTIAL | `tests/unit/test_tunnel_script.py:18` |
| ticketscope--e4-s2--AC-5 | ticketscope--e4-s2 | NONE | none |
| ticketscope--e4-s7--verify | ticketscope--e4-s7 | PARTIAL | `tests/mcp/test_unreachable_api.py:70` `tests/mcp/test_search_tool.py:239` `tests/mcp/test_search_tool.py:102` `tests/mcp/test_claude_desktop_replay.py:60` `tests/mcp/test_trace.py:151` `tests/unit/test_mcp_workflow.py:14` |

- **Gaps:** s2 AC-4 is PARTIAL; s2 AC-5 is NONE; s7 verify is PARTIAL. Every stated behaviour is stated by a contributor: the tunnel path (s2 AC-1, AC-2 and AC-4), the replay (s2 AC-3) and the recorded session citing returned issues (s2 AC-5). The session is the one behaviour with no evidence at all.
- **Recommendation:** Record live results for s2 AC-5 (the session and its evidence) and AC-4 (the hostname returns 404 after the script exits). Repeat the session on the final head, as the epic's Done when says.

### ticketscope--e4--R5 (P1): One trace spans the MCP tool call, the HTTP hop to the API, retrieval and the database, and continues the caller's trace context from the MCP request's `_meta` when present. It is met when a CI check on kind finds one trace in Tempo with that span tree under a `ticketscope-mcp` root, and a call carrying a `traceparent` in `_meta` lands in the caller's trace.

- **Coverage:** PARTIAL ⚠️
- **Parent:** parent R8
- **Priority basis:** contributors
- **Missing behaviors:** None
- **Contributors:** the table below, one row per contributor.

| Contributor | Story | Status | Tests |
| --- | --- | --- | --- |
| ticketscope--e4-s5--AC-1 | ticketscope--e4-s5 | FULL | `tests/mcp/test_trace.py:151` `tests/unit/test_mcp_trace.py:150` `tests/unit/test_mcp_trace_expanded.py:18` |
| ticketscope--e4-s5--AC-2 | ticketscope--e4-s5 | FULL | `tests/mcp/test_trace.py:164` `tests/mcp/test_trace.py:185` `tests/unit/test_mcp_trace.py:196` `tests/unit/test_mcp_trace.py:214` `tests/unit/test_mcp_trace.py:222` `tests/unit/test_mcp_trace.py:207` |
| ticketscope--e4-s5--AC-3 | ticketscope--e4-s5 | FULL | `tests/mcp/test_trace.py:203` `tests/mcp/test_trace.py:216` `tests/unit/test_mcp_trace.py:228` `tests/unit/test_mcp_trace.py:283` `tests/unit/test_mcp_trace.py:268` `tests/unit/test_mcp_trace.py:245` |
| ticketscope--e4-s5--AC-4 | ticketscope--e4-s5 | FULL | `tests/unit/test_mcp_trace.py:304` `tests/unit/test_mcp_trace.py:190` `tests/unit/test_mcp_trace.py:311` `tests/unit/test_mcp_trace.py:298` `tests/mcp/test_trace.py:151` |
| ticketscope--e4-s5--AC-5 | ticketscope--e4-s5 | FULL | `tests/unit/test_mcp_trace.py:150` `tests/unit/test_mcp_trace.py:268` `tests/unit/test_mcp_trace.py:177` |
| ticketscope--e4-s5--AC-6 | ticketscope--e4-s5 | PARTIAL | `tests/unit/test_mcp_captured_pin.py:27` `tests/mcp/test_claude_desktop_replay.py:80` `tests/unit/test_import_linter_enforcement.py:46` |
| ticketscope--e4-s6--AC-1 | ticketscope--e4-s6 | PARTIAL | `tests/unit/test_chart_mcp.py:26` `tests/unit/test_chart_mcp.py:47` `tests/unit/test_chart_tunnel_listener.py:37` |
| ticketscope--e4-s6--AC-2 | ticketscope--e4-s6 | PARTIAL | `tests/unit/test_import_linter_enforcement.py:46` `tests/unit/test_mcp_tempo_helper.py:52` `tests/unit/test_mcp_tempo_helper.py:60` |
| ticketscope--e4-s7--verify | ticketscope--e4-s7 | PARTIAL | `tests/mcp/test_unreachable_api.py:70` `tests/mcp/test_search_tool.py:239` `tests/mcp/test_search_tool.py:102` `tests/mcp/test_claude_desktop_replay.py:60` `tests/mcp/test_trace.py:151` `tests/unit/test_mcp_workflow.py:14` |

- **Gaps:** s5 AC-6 is PARTIAL; s6 AC-1 is PARTIAL; s6 AC-2 is PARTIAL; s7 verify is PARTIAL. Every stated behaviour is covered by FULL contributors: one trace from the tool call through the HTTP hop, retrieval and the database, and the continued `_meta` context (s5 AC-1 and AC-2). R5 is PARTIAL only through s5 AC-6, s6 and s7.
- **Recommendation:** Record live results for s5 AC-6, s6 and s7.

### Criterion Detail

#### ticketscope--e4-s1--AC-1 (P0): Given a PR touching kind paths, when `mcp-e2e.yml` runs, then it deploys to kind and `pytest -m kind tests/mcp` passes: tools/list; a no-mode call whose `mode` equals `retrieval.defaultMode`; a `mode=keyword` call equal to direct `POST /v1/search`; each result valid against the advertised `outputSchema`; a call with no `initialize`; 20 fresh-connection calls with tool-call logs on both pods; a foreign Host refused

- **Coverage:** FULL ✅
- **Priority basis:** inferred. Links: R1.

Given a PR touching kind paths, when `mcp-e2e.yml` runs, then it deploys to kind and `pytest -m kind tests/mcp` passes: tools/list; a no-mode call whose `mode` equals `retrieval.defaultMode`; a `mode=keyword` call equal to direct `POST /v1/search`; each result valid against the advertised `outputSchema`; a call with no `initialize`; 20 fresh-connection calls with tool-call logs on both pods; a foreign Host refused (R1).

- e2e `tests/mcp/test_search_tool.py:79` `test_tools_list_advertises_search_similar_issues`. Lists the tools; the advertised `outputSchema` equals `SearchResponse.model_json_schema()`. Asserted at `tests/mcp/test_search_tool.py:85` `tests/mcp/test_search_tool.py:87`.
- e2e `tests/mcp/test_search_tool.py:90` `test_a_call_without_mode_uses_the_server_default_and_matches_the_schema`. A no-mode call returns `mode` equal to `retrieval.defaultMode` read from `values.yaml`, valid against the schema. Asserted at `tests/mcp/test_search_tool.py:92` `tests/mcp/test_search_tool.py:93`.
- e2e `tests/mcp/test_search_tool.py:96` `test_a_keyword_call_equals_the_direct_v1_body`. A `mode=keyword` call is valid against the schema and equals a direct `POST /v1/search`. Asserted at `tests/mcp/test_search_tool.py:98` `tests/mcp/test_search_tool.py:99`.
- e2e `tests/mcp/test_search_tool.py:119` `test_tools_call_works_without_initialize`. A `tools/call` with no `initialize` succeeds. Asserted at `tests/mcp/test_search_tool.py:139` `tests/mcp/test_search_tool.py:140`.
- e2e `tests/mcp/test_search_tool.py:172` `test_fresh_connections_are_served_by_both_replicas`. 20 fresh-connection calls, with tool-call logs on both pods. Asserted at `tests/mcp/test_search_tool.py:174` `tests/mcp/test_search_tool.py:187`.
- e2e `tests/mcp/test_search_tool.py:223` `test_a_foreign_host_is_refused`. A foreign Host is refused with no stack trace. Asserted at `tests/mcp/test_search_tool.py:235`.
- other `tests/unit/test_mcp_workflow.py:14` `test_mcp_e2e_runs_on_pull_request_through_kind_deploy_behind_the_kind_filter`. `mcp-e2e.yml` runs on PRs through `_kind-deploy.yml` behind the kind path filter and runs `pytest -m kind tests/mcp`. Asserted at `tests/unit/test_mcp_workflow.py:16` `tests/unit/test_mcp_workflow.py:17` `tests/unit/test_mcp_workflow.py:20` `tests/unit/test_mcp_workflow.py:24`.

Note: Kind tests are accepted as static evidence under `contract_static`; this trace did not run them.

#### ticketscope--e4-s1--AC-2 (P1): Given the in-process server and a fake `/v1`, when a tool call omits `mode`, then the fake receives no `mode` key; given `mode="bogus"`, then it receives `"bogus"`

- **Coverage:** FULL ✅
- **Priority basis:** inferred. Links: R1.

Given the in-process server and a fake `/v1`, when a tool call omits `mode`, then the fake receives no `mode` key; given `mode="bogus"`, then it receives `"bogus"` (R1, R-005).

- api `tests/unit/test_mcp_server.py:77` `test_a_call_without_mode_sends_none_and_returns_the_body_unchanged`. With the in-process server and a fake `/v1`, a call without `mode` sends no `mode` key. Asserted at `tests/unit/test_mcp_server.py:85` `tests/unit/test_mcp_server.py:87`.
- api `tests/unit/test_mcp_server.py:91` `test_an_unknown_or_empty_mode_is_sent_unchanged`. `mode="bogus"` and `""` reach the fake unchanged. Asserted at `tests/unit/test_mcp_server.py:98`.
- unit `tests/unit/test_apiclient.py:37` `test_omitted_mode_and_k_are_not_in_the_body`. `apiclient` omits `mode` and `k` when they are not given. Asserted at `tests/unit/test_apiclient.py:40`.
- unit `tests/unit/test_apiclient.py:44` `test_mode_is_sent_exactly_as_given`. `apiclient` sends `bogus` exactly as given. Asserted at `tests/unit/test_apiclient.py:47`.

#### ticketscope--e4-s1--AC-3 (P1): Given `helm template` with kind values, when rendered, then the `mcp` Deployment has 2 replicas, probes that never call api, no database Secret, the in-cluster API URL, and hosts from values; given `*` or no hosts, then render fails

- **Coverage:** FULL ✅
- **Priority basis:** inferred. Links: R1.

Given `helm template` with kind values, when rendered, then the `mcp` Deployment has 2 replicas, probes that never call api, no database Secret, the in-cluster API URL, and hosts from values; given `*` or no hosts, then render fails (R1).

- unit `tests/unit/test_chart_mcp.py:26` `test_kind_renders_two_replicas_with_process_only_probes`. Two replicas on kind; probes hit `/healthz` on `mcp` itself, never `/readyz` or `/v1`. Asserted at `tests/unit/test_chart_mcp.py:28` `tests/unit/test_chart_mcp.py:29` `tests/unit/test_chart_mcp.py:31` `tests/unit/test_chart_mcp.py:32`.
- unit `tests/unit/test_chart_mcp.py:35` `test_no_secret_database_or_mode_env`. No Secret, database variable or mode key is rendered. Asserted at `tests/unit/test_chart_mcp.py:38`.
- unit `tests/unit/test_chart_mcp.py:41` `test_api_url_is_the_in_cluster_service`. The API base URL is the in-cluster Service. Asserted at `tests/unit/test_chart_mcp.py:43`.
- unit `tests/unit/test_chart_mcp.py:47` `test_hosts_come_from_values_on_the_deployment_and_the_route`. Hosts come from values onto the Deployment and the route. Asserted at `tests/unit/test_chart_mcp.py:50` `tests/unit/test_chart_mcp.py:52`.
- unit `tests/unit/test_chart_mcp.py:57` `test_wildcard_hosts_are_refused`. `*`, `*.example.org` and no hosts fail the render. Asserted at `tests/unit/test_chart_mcp.py:62`.

#### ticketscope--e4-s1--AC-4 (P2): Given a same-tag image rebuild, when `kind-up.sh` finishes, then `ticketscope-mcp` was restarted and is Ready

- **Coverage:** PARTIAL ⚠️
- **Priority basis:** inferred. Links: R1.

Given a same-tag image rebuild, when `kind-up.sh` finishes, then `ticketscope-mcp` was restarted and is Ready (R1, R-011).

- other `tests/unit/test_mcp_workflow.py:39` `test_kind_up_restarts_and_waits_for_mcp`. `kind-up.sh` reads the deployed `mcp` image, restarts `ticketscope-mcp` on a same-tag rebuild, and waits for `rollout status` before it returns. Asserted at `tests/unit/test_mcp_workflow.py:41` `tests/unit/test_mcp_workflow.py:42` `tests/unit/test_mcp_workflow.py:43` `tests/unit/test_mcp_workflow.py:44` `tests/unit/test_mcp_workflow.py:46`.

Note: Restart and wait wiring is present and ordered; the run itself is not exercised.

Missing: These are text assertions on the script. No test runs `kind-up.sh` against a same-tag rebuild with `mcp` deployed: the stubbed harness in `tests/unit/test_refactor_sweep_expanded.py` answers only for `ticketscope-api`.

#### ticketscope--e4-s1--AC-5 (P1): Given the changes, when `uv run lint-imports`, ruff, pyright and `pytest` run, then all pass with 10 contracts kept, and `ci.yml`'s `charts` job lists the new chart tests

- **Coverage:** PARTIAL ⚠️
- **Priority basis:** inferred. Links: R1.

Given the changes, when `uv run lint-imports`, ruff, pyright and `pytest` run, then all pass with 10 contracts kept, and `ci.yml`'s `charts` job lists the new chart tests (R1).

- unit `tests/unit/test_import_linter_enforcement.py:46` `test_clean_source_copy_keeps_all_layer_contracts`. Lint-imports keeps all 10 contracts on a source copy. Asserted at `tests/unit/test_import_linter_enforcement.py:50`.
- other `tests/unit/test_mcp_workflow.py:35` `test_ci_charts_job_lists_the_mcp_chart_tests`. `ci.yml`'s `charts` job lists `tests/unit/test_chart_mcp.py`. Asserted at `tests/unit/test_mcp_workflow.py:36`.

Missing: `ruff`, `pyright` and the full `pytest` run are `ci.yml` steps, not tests, and no live record covers them.

#### ticketscope--e4-s2--AC-1 (P1): Given the stand-in host in kind values, when `mcp-e2e.yml` sends `tools/list` with it, then `/mcp` answers 200, `/v1/search` and `/` answer 404, and `ticketscope.kind.internal` still works.

- **Coverage:** FULL ✅
- **Priority basis:** inferred. Links: R4.

Given the stand-in host in kind values, when `mcp-e2e.yml` sends `tools/list` with it, then `/mcp` answers 200, `/v1/search` and `/` answer 404, and `ticketscope.kind.internal` still works.

- e2e `tests/mcp/test_search_tool.py:206` `test_the_stand_in_tunnel_host_reaches_mcp`. The stand-in tunnel host reaches `/mcp` with 200 and lists the tool. Asserted at `tests/mcp/test_search_tool.py:208` `tests/mcp/test_search_tool.py:209`.
- e2e `tests/mcp/test_search_tool.py:218` `test_the_tunnel_host_reaches_nothing_but_mcp[/v1/search, /]`. The same host gets 404 for `/v1/search` and `/`. Asserted at `tests/mcp/test_search_tool.py:220`.
- e2e `tests/mcp/test_search_tool.py:212` `test_the_kind_host_still_reaches_mcp`. `ticketscope.kind.internal` still answers 200. Asserted at `tests/mcp/test_search_tool.py:214`.

#### ticketscope--e4-s2--AC-2 (P1): Given the tunnel value unset, when the charts render, then no extra listener, route host or allowed host appears.

- **Coverage:** FULL ✅
- **Priority basis:** inferred. Links: R4.

Given the tunnel value unset, when the charts render, then no extra listener, route host or allowed host appears.

- unit `tests/unit/test_chart_tunnel_listener.py:32` `test_unset_tunnel_hostname_renders_one_listener`. An unset tunnel value renders one Gateway listener and no tunnel text. Asserted at `tests/unit/test_chart_tunnel_listener.py:34`.
- unit `tests/unit/test_chart_mcp.py:101` `test_unset_tunnel_hostname_adds_no_host`. An unset tunnel value adds no allowed host and no route host. Asserted at `tests/unit/test_chart_mcp.py:104` `tests/unit/test_chart_mcp.py:106`.
- unit `tests/unit/test_chart_mcp.py:121` `test_chart_defaults_carry_no_tunnel_host_and_kind_carries_the_stand_in`. Chart defaults carry no tunnel host; kind carries the stand-in. Asserted at `tests/unit/test_chart_mcp.py:122` `tests/unit/test_chart_mcp.py:124`.

#### ticketscope--e4-s2--AC-3 (P0): Given the captured requests, when `mcp-e2e.yml` replays them, then they pass and no credential appears in them.

- **Coverage:** FULL ✅
- **Priority basis:** inferred. Links: R4.

Given the captured requests, when `mcp-e2e.yml` replays them, then they pass and no credential appears in them.

- e2e `tests/mcp/test_claude_desktop_replay.py:60` `test_every_captured_request_is_answered_on_every_replica`. Each captured request is answered 200 with no JSON-RPC `error`, six times so both replicas answer. Asserted at `tests/mcp/test_claude_desktop_replay.py:42` `tests/mcp/test_claude_desktop_replay.py:50`.
- other `tests/unit/test_mcp_captured_pin.py:35` `test_no_captured_request_carries_a_credential`. No captured request carries a credential header or a bearer token. Asserted at `tests/unit/test_mcp_captured_pin.py:38` `tests/unit/test_mcp_captured_pin.py:39`.
- other `tests/unit/test_mcp_captured_pin.py:27` `test_the_captured_requests_are_unchanged`. The captured bytes are pinned by digest. Asserted at `tests/unit/test_mcp_captured_pin.py:32`.

#### ticketscope--e4-s2--AC-4 (P1): Given the script has exited, when the tunnel hostname is requested, then it no longer reaches the cluster.

- **Coverage:** PARTIAL ⚠️
- **Priority basis:** inferred. Links: R4.

Given the script has exited, when the tunnel hostname is requested, then it no longer reaches the cluster.

- other `tests/unit/test_tunnel_script.py:18` `test_the_tunnel_stops_when_the_script_exits`. The script stops the tunnel on exit (`trap cleanup EXIT`, `kill "$PID"`) Asserted at `tests/unit/test_tunnel_script.py:20`.

Missing: No test requests the tunnel hostname after the script exits. The plan's Human Steps Result records that the hostname answered 404 from ngrok's edge, but that is prose with no live verification record.

#### ticketscope--e4-s2--AC-5 (P0): Given a person's Claude Desktop session, when they ask a triage question, then a committed screenshot shows the tool call and an answer citing returned issues.

- **Coverage:** NONE ❌
- **Priority basis:** inferred. Links: R4.

Given a person's Claude Desktop session, when they ask a triage question, then a committed screenshot shows the tool call and an answer citing returned issues.

- No test and no counted live record.

Missing: No test and no live verification record. A person's Claude Desktop session cannot run in CI. The plan's Human Steps Result (2026-11-11) records the session and its citations of MCL-4563, MCL-16049, MCL-20384 and MC-134224, and says the committed screenshot was waived by the user. Trace counts neither.

#### ticketscope--e4-s3--AC-1 (P1): Given an unknown mode, when the tool is called on kind, then `is_error` is true and its text equals the API's 422 detail.

- **Coverage:** FULL ✅
- **Priority basis:** inferred. Links: R3.

Given an unknown mode, when the tool is called on kind, then `is_error` is true and its text equals the API's 422 detail.

- e2e `tests/mcp/test_search_tool.py:102` `test_an_unknown_mode_is_a_tool_error_with_the_api_detail`. On kind, an unknown mode gives `is_error` and its text equals the API's 422 `detail`. Asserted at `tests/mcp/test_search_tool.py:106` `tests/mcp/test_search_tool.py:114` `tests/mcp/test_search_tool.py:116`.

#### ticketscope--e4-s3--AC-2 (P1): Given any of 422, 404, 500, 503, refused connection, timeout, HTML 502, or a 200 failing the contract, when the tool is called, then the result is `isError: true` with the specified text and no JSON-RPC `error`.

- **Coverage:** FULL ✅
- **Priority basis:** inferred. Links: R3.

Given any of 422, 404, 500, 503, refused connection, timeout, HTML 502, or a 200 failing the contract, when the tool is called, then the result is `isError: true` with the specified text and no JSON-RPC `error`.

- unit `tests/unit/test_apiclient.py:100` `test_a_problem_answer_carries_its_detail_verbatim`. 422, 404, 500 and 503 answers recorded from the real app factory carry their `detail` verbatim. Asserted at `tests/unit/test_apiclient.py:106` `tests/unit/test_apiclient.py:107`.
- unit `tests/unit/test_apiclient.py:128` `test_transport_failures_are_unreachable`. A refused connection and a timeout give the unreachable detail. Asserted at `tests/unit/test_apiclient.py:131`.
- unit `tests/unit/test_apiclient.py:151` `test_a_non_problem_failure_names_the_status_and_never_the_body`. An HTML 502 and other non-problem answers name the status and never the body. Asserted at `tests/unit/test_apiclient.py:155` `tests/unit/test_apiclient.py:157` `tests/unit/test_apiclient.py:160` `tests/unit/test_apiclient.py:161`.
- unit `tests/unit/test_apiclient.py:167` `test_a_200_failing_the_contract_is_a_bad_response`. A 200 that fails the contract is a bad-response error. Asserted at `tests/unit/test_apiclient.py:171`.
- api `tests/unit/test_mcp_expanded.py:62` `test_a_recorded_problem_reaches_the_client_as_its_detail`. Through the MCP server, each recorded problem is `isError` with that detail. Asserted at `tests/unit/test_mcp_expanded.py:73` `tests/unit/test_mcp_expanded.py:74`.
- api `tests/unit/test_mcp_expanded.py:86` `test_an_unreachable_api_is_a_named_tool_error`. A refused connection, a read timeout and a lost connection are named tool errors. Asserted at `tests/unit/test_mcp_expanded.py:91` `tests/unit/test_mcp_expanded.py:92`.
- api `tests/unit/test_mcp_expanded.py:116` `test_a_bad_api_answer_is_a_generic_tool_error`. An HTML 502, a truncated 500 and a failing 200 are generic tool errors. Asserted at `tests/unit/test_mcp_expanded.py:118` `tests/unit/test_mcp_expanded.py:119`.
- api `tests/unit/test_mcp_expanded.py:27` `test_k_outside_the_contract_bounds_is_rejected_before_calling_api`. `k=0` and `k=51` are tool errors and never reach the API. Asserted at `tests/unit/test_mcp_expanded.py:30` `tests/unit/test_mcp_expanded.py:31`.
- api `tests/unit/test_mcp_expanded.py:54` `test_a_non_integer_k_is_a_tool_error_and_never_reaches_api`. A non-integer `k` is a tool error and never reaches the API. Asserted at `tests/unit/test_mcp_expanded.py:57` `tests/unit/test_mcp_expanded.py:58`.

Note: `_result` in `tests/unit/test_mcp_server.py:38` reads `["result"]`, so a JSON-RPC `error` would fail every one of these.

#### ticketscope--e4-s3--AC-3 (P1): Given a successful call, then structured output, text block and outputSchema are unchanged and `mcp-e2e.yml`'s Claude Desktop replay still passes.

- **Coverage:** FULL ✅
- **Priority basis:** inferred. Links: R1, R3.

Given a successful call, then structured output, text block and outputSchema are unchanged and `mcp-e2e.yml`'s Claude Desktop replay still passes.

- api `tests/unit/test_mcp_server.py:77` `test_a_call_without_mode_sends_none_and_returns_the_body_unchanged`. A successful call keeps its structured output unchanged. Asserted at `tests/unit/test_mcp_server.py:86` `tests/unit/test_mcp_server.py:87`.
- api `tests/unit/test_mcp_server.py:208` `test_a_result_carries_a_text_block_of_the_serialised_json_beside_structured_content`. The text block still carries the serialised JSON beside the structured output. Asserted at `tests/unit/test_mcp_server.py:214` `tests/unit/test_mcp_server.py:215`.
- api `tests/unit/test_mcp_server.py:65` `test_tools_list_has_the_search_tool_with_the_contract_output_schema`. The `outputSchema` is unchanged. Asserted at `tests/unit/test_mcp_server.py:74`.
- e2e `tests/mcp/test_claude_desktop_replay.py:72` `test_tools_list_returns_the_tool_with_its_schemas`. The Claude Desktop replay still gets both tools with their schemas. Asserted at `tests/mcp/test_claude_desktop_replay.py:74` `tests/mcp/test_claude_desktop_replay.py:76` `tests/mcp/test_claude_desktop_replay.py:77`.
- e2e `tests/mcp/test_claude_desktop_replay.py:80` `test_tools_call_returns_structured_content_and_a_text_block_of_the_same_json`. The replayed `tools/call` returns structured content and a matching text block. Asserted at `tests/mcp/test_claude_desktop_replay.py:82` `tests/mcp/test_claude_desktop_replay.py:86` `tests/mcp/test_claude_desktop_replay.py:87`.

#### ticketscope--e4-s4--AC-1 (P1): Given a search result's key, when `get_issue` is called with it, then the issue with that key and its outcome returns, valid against the generated schema.

- **Coverage:** FULL ✅
- **Priority basis:** inferred. Links: R2.

Given a search result's key, when `get_issue` is called with it, then the issue with that key and its outcome returns, valid against the generated schema.

- e2e `tests/mcp/test_search_tool.py:239` `test_get_issue_round_trips_a_key_taken_from_a_search`. On kind, `get_issue` with a key taken from a search returns the issue with that key, the same number and outcome, valid against the generated schema. Asserted at `tests/mcp/test_search_tool.py:252` `tests/mcp/test_search_tool.py:253` `tests/mcp/test_search_tool.py:254` `tests/mcp/test_search_tool.py:255`.
- api `tests/unit/test_get_issue_by_key.py:216` `test_get_issue_returns_the_issue_valid_against_the_schema`. In process, the same round trip validates against `IssueResponse`. Asserted at `tests/unit/test_get_issue_by_key.py:218` `tests/unit/test_get_issue_by_key.py:220` `tests/unit/test_get_issue_by_key.py:221` `tests/unit/test_get_issue_by_key.py:223`.
- integration `tests/postgres/test_issue_by_key_postgres.py:49` `test_a_loaded_key_returns_its_issue_and_body`. The Postgres lookup returns the issue and its body. Asserted at `tests/postgres/test_issue_by_key_postgres.py:55`.

#### ticketscope--e4-s4--AC-2 (P0): Given an unknown key, when `get_issue` is called, then `is_error` carries the API's detail.

- **Coverage:** FULL ✅
- **Priority basis:** inferred. Links: R3.

Given an unknown key, when `get_issue` is called, then `is_error` carries the API's detail.

- e2e `tests/mcp/test_search_tool.py:239` `test_get_issue_round_trips_a_key_taken_from_a_search`. On kind, an unknown key is `is_error` and its text equals the API's 404 `detail`. Asserted at `tests/mcp/test_search_tool.py:262` `tests/mcp/test_search_tool.py:264`.
- api `tests/unit/test_get_issue_by_key.py:226` `test_an_unknown_key_is_a_tool_error_with_the_api_detail`. In process, an unknown key is a tool error with the API's detail. Asserted at `tests/unit/test_get_issue_by_key.py:228` `tests/unit/test_get_issue_by_key.py:229`.
- api `tests/unit/test_get_issue_by_key.py:144` `test_an_unknown_well_formed_key_is_a_404_problem`. The API answers an unknown well-formed key with a 404 problem+json. Asserted at `tests/unit/test_get_issue_by_key.py:147` `tests/unit/test_get_issue_by_key.py:148`.

#### ticketscope--e4-s4--AC-3 (P0): Given any hostile key, when `get_issue` is called, then `is_error` and no other issue is fetched.

- **Coverage:** FULL ✅
- **Priority basis:** inferred. Links: R2, R3.

Given any hostile key, when `get_issue` is called, then `is_error` and no other issue is fetched.

- api `tests/unit/test_get_issue_by_key.py:233` `test_a_hostile_key_is_a_tool_error_and_no_other_issue_is_fetched`. Each hostile key is a tool error with no structured body, and the forbidden issue number is never fetched. Asserted at `tests/unit/test_get_issue_by_key.py:237` `tests/unit/test_get_issue_by_key.py:238` `tests/unit/test_get_issue_by_key.py:239`.
- api `tests/unit/test_get_issue_by_key.py:243` `test_a_dot_segment_key_stays_under_by_key`. A dot-segment key stays under `/v1/issues/by-key/` as one segment. Asserted at `tests/unit/test_get_issue_by_key.py:246` `tests/unit/test_get_issue_by_key.py:248` `tests/unit/test_get_issue_by_key.py:249` `tests/unit/test_get_issue_by_key.py:250`.
- unit `tests/unit/test_get_issue_by_key_expanded.py:138` `test_get_issue_encodes_all_dot_keys`. `.`, `..` and `...` are percent-encoded. Asserted at `tests/unit/test_get_issue_by_key_expanded.py:147`.
- unit `tests/unit/test_get_issue_by_key.py:271` `test_apiclient_encodes_the_key_as_one_segment`. A key with `?`, `#` and `/` is percent-encoded as one segment. Asserted at `tests/unit/test_get_issue_by_key.py:283`.
- api `tests/unit/test_get_issue_by_key.py:152` `test_a_hostile_key_is_a_404_and_fetches_no_number`. The API answers each hostile key with 404 problem+json and fetches no number. Asserted at `tests/unit/test_get_issue_by_key.py:155` `tests/unit/test_get_issue_by_key.py:156` `tests/unit/test_get_issue_by_key.py:157`.
- api `tests/unit/test_get_issue_by_key_expanded.py:79` `test_by_key_trailing_newline_is_404_not_the_issue`. A trailing newline is a 404, not the issue. Asserted at `tests/unit/test_get_issue_by_key_expanded.py:82`.
- api `tests/unit/test_get_issue_by_key.py:253` `test_a_returned_key_that_differs_is_a_tool_error`. A body whose `issue.key` differs from the one asked for is a tool error. Asserted at `tests/unit/test_get_issue_by_key.py:258` `tests/unit/test_get_issue_by_key.py:259`.
- api `tests/unit/test_get_issue_by_key.py:262` `test_a_body_with_no_key_is_a_tool_error`. A body with no key is a tool error. Asserted at `tests/unit/test_get_issue_by_key.py:268`.
- integration `tests/postgres/test_issue_by_key_postgres.py:59` `test_an_unknown_or_sql_shaped_key_returns_none`. An unknown or SQL-shaped key returns nothing through the Postgres adapter. Asserted at `tests/postgres/test_issue_by_key_postgres.py:63`.
- unit `tests/unit/test_key_oracle_pinned.py:45` `test_the_key_oracle_agrees_with_the_snapshot_and_the_key_pattern`. The key oracle agrees with the snapshot and the key pattern, and no hostile key matches it. Asserted at `tests/unit/test_key_oracle_pinned.py:48` `tests/unit/test_key_oracle_pinned.py:49` `tests/unit/test_key_oracle_pinned.py:50`.
- other `tests/unit/test_key_oracle_pinned.py:34` `test_the_key_oracle_is_unchanged_since_its_red_commit`. The key oracle is pinned to its red-commit content. Asserted at `tests/unit/test_key_oracle_pinned.py:39`.

#### ticketscope--e4-s4--AC-4 (P1): Given two bodies differing only in `issue.key`, when the parity script compares with the option, then it passes; any other difference fails.

- **Coverage:** FULL ✅
- **Priority basis:** inferred. Links: R2.

Given two bodies differing only in `issue.key`, when the parity script compares with the option, then it passes; any other difference fails.

- unit `tests/unit/test_get_issue_by_key.py:316` `test_parity_passes_when_only_issue_key_differs`. The parity script fails on a key-only difference and passes with `--drop-issue-key`. Asserted at `tests/unit/test_get_issue_by_key.py:318` `tests/unit/test_get_issue_by_key.py:319`.
- unit `tests/unit/test_get_issue_by_key.py:322` `test_parity_still_fails_on_any_other_difference`. Any other difference still fails with the option. Asserted at `tests/unit/test_get_issue_by_key.py:324`.
- unit `tests/unit/test_get_issue_by_key_expanded.py:161` `test_drop_issue_key_touches_only_issue_key`. The option drops only `issue.key`. Asserted at `tests/unit/test_get_issue_by_key_expanded.py:169`.

#### ticketscope--e4-s4--AC-5 (P1): Given the existing suite, when run, then it passes with `eval/baseline.json` unchanged.

- **Coverage:** PARTIAL ⚠️
- **Priority basis:** inferred. Links: R2.

Given the existing suite, when run, then it passes with `eval/baseline.json` unchanged.

- api `tests/unit/test_get_issue_by_key.py:98` `test_search_and_issue_bodies_carry_the_key`. Search and issue bodies carry the key. Asserted at `tests/unit/test_get_issue_by_key.py:108` `tests/unit/test_get_issue_by_key.py:110`.
- api `tests/unit/test_get_issue_by_key.py:128` `test_a_body_without_key_still_validates`. A body without `key` still validates. Asserted at `tests/unit/test_get_issue_by_key.py:131`.
- api `tests/unit/test_get_issue_by_key.py:137` `test_by_key_equals_by_number`. By-key returns the same body as by-number. Asserted at `tests/unit/test_get_issue_by_key.py:140` `tests/unit/test_get_issue_by_key.py:141`.

Missing: The clause is a CI observation: the suite passes and `eval/baseline.json` is unchanged. No test asserts the baseline is untouched and no live record carries it.

#### ticketscope--e4-s5--AC-1 (P1): Given a `search_similar_issues` call with no caller context, when the trace is read from Tempo on kind, then one trace has the `ticketscope-mcp` tool span as its root with the CLIENT `POST`, `api`'s `POST /v1/search`, `retrieval hybrid`, `embeddings {model}` and the db query beneath it.

- **Coverage:** FULL ✅
- **Priority basis:** inferred. Links: R5.

Given a `search_similar_issues` call with no caller context, when the trace is read from Tempo on kind, then one trace has the `ticketscope-mcp` tool span as its root with the CLIENT `POST`, `api`'s `POST /v1/search`, `retrieval hybrid`, `embeddings {model}` and the db query beneath it.

- e2e `tests/mcp/test_trace.py:151` `test_a_search_is_one_trace_under_the_tool_span`. On kind, one trace with a single `ticketscope-mcp` SERVER tool span and the tool-span attribute keys equal to the constants list; the helper `_assert_search_tree` (`tests/mcp/test_trace.py:120`) asserts the tool root, CLIENT POST, `POST /v1/search`, `retrieval hybrid`, one `embeddings` span and a db span beneath it. Asserted at `tests/mcp/test_trace.py:156` `tests/mcp/test_trace.py:160` `tests/mcp/test_trace.py:161`.
- api `tests/unit/test_mcp_trace.py:150` `test_plain_call_is_one_trace_with_tool_span_root_and_client_child`. In process, the tool span is the root with the CLIENT POST under it, and `traceparent` carries the tool trace id. Asserted at `tests/unit/test_mcp_trace.py:158` `tests/unit/test_mcp_trace.py:159` `tests/unit/test_mcp_trace.py:162` `tests/unit/test_mcp_trace.py:171` `tests/unit/test_mcp_trace.py:173`.
- unit `tests/unit/test_mcp_trace_expanded.py:18` `test_main_sets_up_telemetry_as_mcp_without_db_instrumentation`. `main` sets up telemetry as `ticketscope-mcp` without database instrumentation. Asserted at `tests/unit/test_mcp_trace_expanded.py:28`.

#### ticketscope--e4-s5--AC-2 (P1): Given `_meta.traceparent` (alone, or with a different HTTP `traceparent`), when a tool is called, then the tool span's trace id is the `_meta` one.

- **Coverage:** FULL ✅
- **Priority basis:** inferred. Links: R5.

Given `_meta.traceparent` (alone, or with a different HTTP `traceparent`), when a tool is called, then the tool span's trace id is the `_meta` one.

- e2e `tests/mcp/test_trace.py:164` `test_meta_traceparent_lands_in_that_trace`. On kind, a `_meta` traceparent lands in that trace id with the caller's span as parent. Asserted at `tests/mcp/test_trace.py:178` `tests/mcp/test_trace.py:179`.
- e2e `tests/mcp/test_trace.py:185` `test_meta_wins_over_a_different_http_traceparent_header`. With both a header and `_meta`, the header's trace id is never used. Asserted at `tests/mcp/test_trace.py:198`.
- api `tests/unit/test_mcp_trace.py:196` `test_meta_traceparent_is_continued`. In process, `_meta` is continued and forwarded to the API. Asserted at `tests/unit/test_mcp_trace.py:201` `tests/unit/test_mcp_trace.py:203` `tests/unit/test_mcp_trace.py:204`.
- api `tests/unit/test_mcp_trace.py:214` `test_meta_wins_over_the_http_traceparent_header`. `_meta` wins over a different HTTP traceparent. Asserted at `tests/unit/test_mcp_trace.py:219`.
- api `tests/unit/test_mcp_trace.py:222` `test_http_header_alone_is_ignored`. An HTTP header alone is ignored. Asserted at `tests/unit/test_mcp_trace.py:225`.
- api `tests/unit/test_mcp_trace.py:207` `test_malformed_meta_traceparent_starts_a_new_trace`. A malformed `_meta` traceparent starts a new trace. Asserted at `tests/unit/test_mcp_trace.py:210`.

#### ticketscope--e4-s5--AC-3 (P1): Given a tool error, when the span is read, then its status is ERROR; and `get_issue` yields its own trace the same way.

- **Coverage:** FULL ✅
- **Priority basis:** inferred. Links: R5.

Given a tool error, when the span is read, then its status is ERROR; and `get_issue` yields its own trace the same way.

- e2e `tests/mcp/test_trace.py:203` `test_an_unknown_mode_gives_an_error_tool_span`. On kind, an unknown mode gives a tool span with status ERROR. Asserted at `tests/mcp/test_trace.py:209`.
- e2e `tests/mcp/test_trace.py:216` `test_get_issue_is_its_own_trace`. On kind, `get_issue` is its own trace: tool root, CLIENT GET, then `GET /v1/issues/by-key/{key}`. Asserted at `tests/mcp/test_trace.py:229` `tests/mcp/test_trace.py:232` `tests/mcp/test_trace.py:234`.
- api `tests/unit/test_mcp_trace.py:228` `test_an_api_422_sets_error_status_on_the_tool_span`. In process, a 422 sets ERROR on the tool span. Asserted at `tests/unit/test_mcp_trace.py:239` `tests/unit/test_mcp_trace.py:242`.
- api `tests/unit/test_mcp_trace.py:283` `test_an_api_404_for_an_unknown_key_sets_error_status_on_the_tool_span`. In process, an unknown key sets ERROR on the `get_issue` tool span. Asserted at `tests/unit/test_mcp_trace.py:294`.
- api `tests/unit/test_mcp_trace.py:268` `test_get_issue_is_its_own_trace_with_a_get_client_span`. In process, `get_issue` has a tool root and a CLIENT GET to the by-key URL. Asserted at `tests/unit/test_mcp_trace.py:274` `tests/unit/test_mcp_trace.py:277` `tests/unit/test_mcp_trace.py:279`.
- api `tests/unit/test_mcp_trace.py:245` `test_an_unreachable_api_sets_error_on_the_client_and_tool_spans`. An unreachable API sets ERROR on the CLIENT and tool spans. Asserted at `tests/unit/test_mcp_trace.py:254` `tests/unit/test_mcp_trace.py:256`.

#### ticketscope--e4-s5--AC-4 (P1): Given default settings, when any tool is called, then no span carries query text, and the tool span's attribute keys equal the constants list.

- **Coverage:** FULL ✅
- **Priority basis:** inferred. Links: R5.

Given default settings, when any tool is called, then no span carries query text, and the tool span's attribute keys equal the constants list.

- api `tests/unit/test_mcp_trace.py:304` `test_no_span_carries_the_query_by_default`. With default settings no span carries the query text. Asserted at `tests/unit/test_mcp_trace.py:307` `tests/unit/test_mcp_trace.py:308`.
- api `tests/unit/test_mcp_trace.py:190` `test_tool_span_keys_equal_the_constants_list`. The tool span's attribute keys equal the constants list. Asserted at `tests/unit/test_mcp_trace.py:193`.
- api `tests/unit/test_mcp_trace.py:311` `test_query_text_is_on_the_tool_span_only_when_opted_in`. Query text appears on the tool span only when the value opts in. Asserted at `tests/unit/test_mcp_trace.py:315` `tests/unit/test_mcp_trace.py:316`.
- api `tests/unit/test_mcp_trace.py:298` `test_the_url_on_the_client_span_never_carries_a_query`. The CLIENT span URL never carries a query string. Asserted at `tests/unit/test_mcp_trace.py:301`.
- e2e `tests/mcp/test_trace.py:151` `test_a_search_is_one_trace_under_the_tool_span`. On kind, `_assert_no_query_text` finds the query on no span. Asserted at `tests/mcp/test_trace.py:155`.

#### ticketscope--e4-s5--AC-5 (P1): Given `apiclient` in a unit test, when it sends a request inside a tool span, then the outgoing `traceparent` carries the tool span's trace id.

- **Coverage:** FULL ✅
- **Priority basis:** inferred. Links: R5.

Given `apiclient` in a unit test, when it sends a request inside a tool span, then the outgoing `traceparent` carries the tool span's trace id.

- api `tests/unit/test_mcp_trace.py:150` `test_plain_call_is_one_trace_with_tool_span_root_and_client_child`. The outgoing request's `traceparent` carries the tool span's trace id. Asserted at `tests/unit/test_mcp_trace.py:171` `tests/unit/test_mcp_trace.py:173`.
- api `tests/unit/test_mcp_trace.py:268` `test_get_issue_is_its_own_trace_with_a_get_client_span`. The same holds for `get_issue`. Asserted at `tests/unit/test_mcp_trace.py:280`.
- api `tests/unit/test_mcp_trace.py:177` `test_client_span_has_http_semconv_attributes`. The CLIENT span has the HTTP semconv attributes. Asserted at `tests/unit/test_mcp_trace.py:180`.

#### ticketscope--e4-s5--AC-6 (P1): Given the existing suite, when run (`pytest`, `lint-imports`, ruff, pyright), then it passes, including the Claude Desktop replay and captured-pin tests.

- **Coverage:** PARTIAL ⚠️
- **Priority basis:** inferred. Links: R1, R5.

Given the existing suite, when run (`pytest`, `lint-imports`, ruff, pyright), then it passes, including the Claude Desktop replay and captured-pin tests.

- other `tests/unit/test_mcp_captured_pin.py:27` `test_the_captured_requests_are_unchanged`. The Claude Desktop captured-pin test. Asserted at `tests/unit/test_mcp_captured_pin.py:32`.
- e2e `tests/mcp/test_claude_desktop_replay.py:80` `test_tools_call_returns_structured_content_and_a_text_block_of_the_same_json`. The replay test. Asserted at `tests/mcp/test_claude_desktop_replay.py:82` `tests/mcp/test_claude_desktop_replay.py:86`.
- unit `tests/unit/test_import_linter_enforcement.py:46` `test_clean_source_copy_keeps_all_layer_contracts`. Lint-imports keeps all 10 contracts. Asserted at `tests/unit/test_import_linter_enforcement.py:50`.

Missing: That `pytest`, `lint-imports`, `ruff` and `pyright` pass is a CI observation. The pin and replay tests exist, but no test or live record carries the passing run.

#### ticketscope--e4-s6--AC-1 (P1): Given the refactor, when `helm template` runs, then output equals the pre-change render.

- **Coverage:** PARTIAL ⚠️
- **Priority basis:** inferred. Links: R1, R2, R3, R5.

Given the refactor, when `helm template` runs, then output equals the pre-change render.

- unit `tests/unit/test_chart_mcp.py:26` `test_kind_renders_two_replicas_with_process_only_probes`. Post-refactor, the `mcp` Deployment still renders as the spine requires. Asserted at `tests/unit/test_chart_mcp.py:28` `tests/unit/test_chart_mcp.py:29` `tests/unit/test_chart_mcp.py:31`.
- unit `tests/unit/test_chart_mcp.py:47` `test_hosts_come_from_values_on_the_deployment_and_the_route`. Post-refactor, the route and allowed hosts still come from values. Asserted at `tests/unit/test_chart_mcp.py:50` `tests/unit/test_chart_mcp.py:52` `tests/unit/test_chart_mcp.py:53`.
- unit `tests/unit/test_chart_tunnel_listener.py:37` `test_tunnel_hostname_adds_a_second_listener_and_keeps_the_kind_host`. Post-refactor, the Gateway's second listener renders for the tunnel host. Asserted at `tests/unit/test_chart_tunnel_listener.py:45` `tests/unit/test_chart_tunnel_listener.py:46` `tests/unit/test_chart_tunnel_listener.py:47`.

Missing: No test compares `helm template` output with the pre-change render. Each render test asserts the current output, not equality with the output before the refactor.

#### ticketscope--e4-s6--AC-2 (P1): Given the refactor, when unit tests, ruff, pyright and lint-imports run, then all pass.

- **Coverage:** PARTIAL ⚠️
- **Priority basis:** inferred. Links: R1, R2, R3, R5.

Given the refactor, when unit tests, ruff, pyright and lint-imports run, then all pass.

- unit `tests/unit/test_import_linter_enforcement.py:46` `test_clean_source_copy_keeps_all_layer_contracts`. Lint-imports keeps all 10 contracts. Asserted at `tests/unit/test_import_linter_enforcement.py:50`.
- unit `tests/unit/test_mcp_tempo_helper.py:52` `test_hex_and_base64_ids_parse_to_the_same_span`. The unified Tempo helper still parses hex and base64 ids. Asserted at `tests/unit/test_mcp_tempo_helper.py:52`.
- unit `tests/unit/test_mcp_tempo_helper.py:60` `test_int_value_strings_become_ints`. The unified Tempo helper still parses string `intValue`s. Asserted at `tests/unit/test_mcp_tempo_helper.py:60`.

Missing: That the unit tests, `ruff` and `pyright` pass is a CI observation with no test or live record.

#### ticketscope--e4-s7--verify (P1): On a fresh kind cluster, mcp-e2e.yml's integrated suite passes in CI covering each Done when line of the epic that CI can run (R1, R2, R3, R5), including the Claude Desktop replay (R4); with api at zero, mcp stays Ready and the tool returns is_error with the unreachable detail within the timeout plus a margin, not a Gateway 503, and api is restored afterwards (R3); the epic's Notes link story 2's recorded Claude Desktop session for R4 and cite this story's mcp-e2e.yml run URL as the CI evidence (C-7).

- **Coverage:** PARTIAL ⚠️
- **Priority basis:** inferred. Links: R1, R2, R3, R4, R5.

On a fresh kind cluster, mcp-e2e.yml's integrated suite passes in CI covering each Done when line of the epic that CI can run (R1, R2, R3, R5), including the Claude Desktop replay (R4); with api at zero, mcp stays Ready and the tool returns is_error with the unreachable detail within the timeout plus a margin, not a Gateway 503, and api is restored afterwards (R3); the epic's Notes link story 2's recorded Claude Desktop session for R4 and cite this story's mcp-e2e.yml run URL as the CI evidence (C-7).

- e2e `tests/mcp/test_unreachable_api.py:70` `test_mcp_stays_ready_and_both_tools_return_the_unreachable_detail`. With `api` at zero, `mcp` stays Ready and both tools return `is_error` with the unreachable detail within the timeout plus a margin; the module fixture scales `api` back and waits for it (lines 55 to 57) Asserted at `tests/mcp/test_unreachable_api.py:71` `tests/mcp/test_unreachable_api.py:85` `tests/mcp/test_unreachable_api.py:87` `tests/mcp/test_unreachable_api.py:88`.
- e2e `tests/mcp/test_search_tool.py:239` `test_get_issue_round_trips_a_key_taken_from_a_search`. Both tools, `get_issue` by a key from a search, and the unknown-key error on kind. Asserted at `tests/mcp/test_search_tool.py:252` `tests/mcp/test_search_tool.py:264`.
- e2e `tests/mcp/test_search_tool.py:102` `test_an_unknown_mode_is_a_tool_error_with_the_api_detail`. The unknown-mode error on kind. Asserted at `tests/mcp/test_search_tool.py:116`.
- e2e `tests/mcp/test_claude_desktop_replay.py:60` `test_every_captured_request_is_answered_on_every_replica`. The Claude Desktop replay. Asserted at `tests/mcp/test_claude_desktop_replay.py:42` `tests/mcp/test_claude_desktop_replay.py:50`.
- e2e `tests/mcp/test_trace.py:151` `test_a_search_is_one_trace_under_the_tool_span`. One trace from the tool call to the database on kind. Asserted at `tests/mcp/test_trace.py:156` `tests/mcp/test_trace.py:160`.
- other `tests/unit/test_mcp_workflow.py:14` `test_mcp_e2e_runs_on_pull_request_through_kind_deploy_behind_the_kind_filter`. The unreachable case runs in its own pytest invocation after the main suite. Asserted at `tests/unit/test_mcp_workflow.py:24` `tests/unit/test_mcp_workflow.py:25`.

Missing: Two clauses have no test or live record. First, that the integrated suite passes in CI on a fresh cluster. Second, that the epic's Notes link story 2's recorded session and cite this story's `mcp-e2e.yml` run URL: `epic-mcp-server.md` Notes (lines 78 to 91) hold neither. Also, `tests/mcp/test_unreachable_api.py:25` marks `ticketscope--e4-s7--AC-1`, an id that is not in the ledger (story 7 has only `verify`).

### Invalid and Unlinked Criteria

None. Every criterion names at least one defined requirement. Story 6's ticket has `covers = []`, but its `verify` text tags R1, R2, R3 and R5, and those tags are its links.

## Gaps & Recommendations

| # | Priority | Gap | Closes | Action |
| --- | --- | --- | --- | --- |
| 1 | P0 (via R4) | s2 AC-5: Claude Desktop answers from ticketscope. No test, no live record; the screenshot was waived | R4 | Record live verification at this commit, with the session evidence from the plan's Human Steps Result. Repeat the session on the final head for epic closure. This caps the run at CONCERNS. |
| 2 | P1 | s2 AC-4: the tunnel hostname stops reaching the cluster after the script exits | R4 | Record a live result, or add a test that runs `scripts/tunnel.sh` with a stub `ngrok` and checks the process is gone |
| 3 | P1 | s6 AC-1: no before/after render comparison | R1, R2, R3, R5 | Add a test that renders the `ticketscope` and `platform` charts for default, kind and tunnel-host values and compares them with committed goldens, or record a live result |
| 4 | P1 | Process clauses: s1 AC-5, s4 AC-5, s5 AC-6, s6 AC-2, s7 verify | R1 to R5 | Record live results citing the `ci`, `eval` and `mcp-e2e` runs for the PR heads; add a test that `eval/baseline.json` is untouched by the diff (s4 AC-5) |
| 5 | P2 | s1 AC-4: `kind-up.sh` restart and wait for `mcp` is asserted as text only | R1 | Extend the stubbed `kind_up` harness in `tests/unit/test_refactor_sweep_expanded.py` to answer for `ticketscope-mcp` |
| 6 | P1 | s7 verify: the epic's Notes lack the s2 session link and the `mcp-e2e.yml` run URL (C-7); a stale marker `ticketscope--e4-s7--AC-1` | R1 to R5 | PO adds the links; rename the marker in `tests/mcp/test_unreachable_api.py:25` to `ticketscope--e4-s7--verify` |

**Coverage heuristics.** Endpoints: `POST /v1/search`, `GET /v1/issues/{number}`, `GET /v1/issues/by-key/{key}` and `/mcp` each have a direct test, so none is uncovered. Auth: the epic has none by design (epic 6 adds it), so there is no negative path to miss. Error paths: unknown mode and key, `k` out of bounds, 4xx and 5xx problems, an HTML 502, a failing 200, refused and timed-out connections and an unreachable API are all tested, so no criterion is happy-path-only.

**Rejected evidence.** None. Every test cited asserts part of the criterion it is mapped to.

## Waiver Register Review

`_bmad-output/test-artifacts/gate-waivers.md` holds one waiver, W-001, which covers six `ticketscope--e1` criteria. It names none of this run's rows, so it cannot apply. No waiver is filed for `ticketscope--e4`, and none is applied. The derived decision stays FAIL.

## Next Actions

1. Record live verification results for the process clauses, with the CI run URLs and the Claude Desktop session evidence, and add the three small tests listed above. Then re-run `bmad-tea-trace` for `epic-ticketscope--e4`.
2. Have the PO add the two missing epic Notes links before the closing Claude Desktop session on the final head.
3. Run `/bmad-tea-nfr` and `/bmad-tea-test-review` for epic 4: neither exists yet, and the trace cites neither.

## Gate Decision Summary

```text
GATE DECISION: FAIL

Coverage Analysis:
- P0 Coverage: 0% (Required: 100%) -> NOT_MET
- P1 Coverage: 0% (PASS target: 90%, minimum: 80%) -> NOT_MET
- Overall Coverage: 0% (Minimum: 80%) -> NOT_MET

Decision Rationale:
P0 coverage is 0% (required: 100%). 4 critical requirement(s) below FULL coverage.

Critical Gaps: 4 (P0 requirements below FULL coverage: R1, R2, R3, R4)
Waivers Filed: 1 (W-001, for ticketscope--e1). None applied; the decision above is the derived one.
Full Report: _bmad-output/test-artifacts/trace/traceability-matrix-epic-ticketscope--e4.md

GATE: FAIL - Release BLOCKED until coverage improves
```

### Requirement Aggregation

```json
{
  "criterionMatrix": [
    {
      "id": "ticketscope--e4-s1--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e4-s1--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e4-s1--AC-3",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e4-s1--AC-4",
      "coverage": "PARTIAL"
    },
    {
      "id": "ticketscope--e4-s1--AC-5",
      "coverage": "PARTIAL"
    },
    {
      "id": "ticketscope--e4-s2--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e4-s2--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e4-s2--AC-3",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e4-s2--AC-4",
      "coverage": "PARTIAL"
    },
    {
      "id": "ticketscope--e4-s2--AC-5",
      "coverage": "NONE"
    },
    {
      "id": "ticketscope--e4-s3--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e4-s3--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e4-s3--AC-3",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e4-s4--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e4-s4--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e4-s4--AC-3",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e4-s4--AC-4",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e4-s4--AC-5",
      "coverage": "PARTIAL"
    },
    {
      "id": "ticketscope--e4-s5--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e4-s5--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e4-s5--AC-3",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e4-s5--AC-4",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e4-s5--AC-5",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e4-s5--AC-6",
      "coverage": "PARTIAL"
    },
    {
      "id": "ticketscope--e4-s6--AC-1",
      "coverage": "PARTIAL"
    },
    {
      "id": "ticketscope--e4-s6--AC-2",
      "coverage": "PARTIAL"
    },
    {
      "id": "ticketscope--e4-s7--verify",
      "coverage": "PARTIAL"
    }
  ],
  "traceabilityMatrix": [
    {
      "id": "ticketscope--e4--R1",
      "kind": "requirement",
      "coverage": "PARTIAL",
      "contributors": [
        {
          "id": "ticketscope--e4-s1--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s1--AC-2",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s1--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s1--AC-4",
          "coverage": "PARTIAL"
        },
        {
          "id": "ticketscope--e4-s1--AC-5",
          "coverage": "PARTIAL"
        },
        {
          "id": "ticketscope--e4-s3--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s5--AC-6",
          "coverage": "PARTIAL"
        },
        {
          "id": "ticketscope--e4-s6--AC-1",
          "coverage": "PARTIAL"
        },
        {
          "id": "ticketscope--e4-s6--AC-2",
          "coverage": "PARTIAL"
        },
        {
          "id": "ticketscope--e4-s7--verify",
          "coverage": "PARTIAL"
        }
      ],
      "missingBehaviors": []
    },
    {
      "id": "ticketscope--e4--R2",
      "kind": "requirement",
      "coverage": "PARTIAL",
      "contributors": [
        {
          "id": "ticketscope--e4-s4--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s4--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s4--AC-4",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s4--AC-5",
          "coverage": "PARTIAL"
        },
        {
          "id": "ticketscope--e4-s6--AC-1",
          "coverage": "PARTIAL"
        },
        {
          "id": "ticketscope--e4-s6--AC-2",
          "coverage": "PARTIAL"
        },
        {
          "id": "ticketscope--e4-s7--verify",
          "coverage": "PARTIAL"
        }
      ],
      "missingBehaviors": []
    },
    {
      "id": "ticketscope--e4--R3",
      "kind": "requirement",
      "coverage": "PARTIAL",
      "contributors": [
        {
          "id": "ticketscope--e4-s3--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s3--AC-2",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s3--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s4--AC-2",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s4--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s6--AC-1",
          "coverage": "PARTIAL"
        },
        {
          "id": "ticketscope--e4-s6--AC-2",
          "coverage": "PARTIAL"
        },
        {
          "id": "ticketscope--e4-s7--verify",
          "coverage": "PARTIAL"
        }
      ],
      "missingBehaviors": []
    },
    {
      "id": "ticketscope--e4--R4",
      "kind": "requirement",
      "coverage": "PARTIAL",
      "contributors": [
        {
          "id": "ticketscope--e4-s2--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s2--AC-2",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s2--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s2--AC-4",
          "coverage": "PARTIAL"
        },
        {
          "id": "ticketscope--e4-s2--AC-5",
          "coverage": "NONE"
        },
        {
          "id": "ticketscope--e4-s7--verify",
          "coverage": "PARTIAL"
        }
      ],
      "missingBehaviors": []
    },
    {
      "id": "ticketscope--e4--R5",
      "kind": "requirement",
      "coverage": "PARTIAL",
      "contributors": [
        {
          "id": "ticketscope--e4-s5--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s5--AC-2",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s5--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s5--AC-4",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s5--AC-5",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e4-s5--AC-6",
          "coverage": "PARTIAL"
        },
        {
          "id": "ticketscope--e4-s6--AC-1",
          "coverage": "PARTIAL"
        },
        {
          "id": "ticketscope--e4-s6--AC-2",
          "coverage": "PARTIAL"
        },
        {
          "id": "ticketscope--e4-s7--verify",
          "coverage": "PARTIAL"
        }
      ],
      "missingBehaviors": []
    }
  ]
}
```
