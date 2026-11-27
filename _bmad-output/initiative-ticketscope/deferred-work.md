# Deferred work

### DW-1: duplicate_target does not check link_type, so a non-Duplicate link in duplicate_links could become the duplicate target and /v1 ref.
origin: spec-deferred 98c5dbcafc93
location: src/ticketscope/core/derive.py duplicate_target
source_spec: `tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md`
severity: medium
reason: Unverified (maybe-false). AD-26 names "any Duplicate-mapped link"; the spike filters by jira_issue_linktype_mapping.json. Harmless if story 13's ingest writes only Duplicate-mapped links into duplicate_links; settle in story 13 by filtering at ingest or by having core check link_type. (declared severity: medium (unverified))
status: done 2026-11-07
resolution: settled by story 1.13 (aac2796): ingest keeps only Duplicate-mapped links (src/ticketscope/jobs/ingest/jira.py is_duplicate_linktype), so duplicate_links never holds another link type

### DW-2: The kind smoke test (3) test_load_log_has_the_report fails when the suite runs right after an in-place kind-up.sh upgrade of an already-loaded cluster.
origin: spec-deferred 041265e3f274
location: tests/smoke/test_gateway.py (section 3); scripts/kind-up.sh
source_spec: `tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md`
severity: low
reason: The same-pin load is a no-op, so the newest Succeeded load pod logs no "load report:" line; only (5)'s forced reload restores it, so a rerun passes. Reproduced twice in this build, after each in-place upgrade. It predates this change: test (3) and the no-op load come from story 1.5. Also, kind-up.sh reuses the HEAD-SHA tag, so an in-place re-run with uncommitted code does not roll the api pod; `kubectl rollout restart` was needed.
status: done 2026-11-07
resolution: resolved by story 10 (refactor sweep): smoke (3) forces a reload when the newest load was a no-op, and kind-up.sh restarts api after rebuilding the app image under an existing release

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-a-regressing-pr-cannot-merge-plan.md`
  summary: Eval gate diffs against the event's `pull_request.base.sha`, which can be stale on a rerun.
  evidence: If main advanced and a baseline update landed, a rerun's `git diff <base.sha> HEAD` includes it, so `baseline_changed` is true for a PR that did not touch the baseline. Diff against the merge commit's first parent instead.

### DW-3: Embedder reference vectors (test-design oracle) are not committed; they need the model run outside this code path.
origin: spec-deferred 14119ac8a05e
location: n/a
source_spec: `tickets/epic-hybrid-retrieval/tickets/story-tracer-dense-search-answers-through-v1-on-kind-plan.md`
severity: medium
reason: No red-mode session ran; the cosine fixture was committed, reference vectors were not producible in-code.
status: resolved 2026-11-20
resolution: resolved by story 5.13: scripts/reference_vectors.py (onnxruntime and tokenizers, no fastembed) made tests/fixtures/embedder_reference.json, pinned by test_embedder_reference_pinned.py and compared to the image embedder by tests/image/test_app_image.py on amd64 and arm64
carried_to: epic-eks-environment (5), raised at its refinement together with DW-6 and the R-004 embedding parity row (retro A6); carried at epic 3's closure (user, 2026-11-11)

### DW-4: Kind run (EMBEDDINGS_COMPUTE=1 and flag-off kind-up), Tempo trace check, OOM and api memory measurement on kind were not run.
origin: spec-deferred 166db8a1336b
location: n/a
source_spec: `tickets/epic-hybrid-retrieval/tickets/story-tracer-dense-search-answers-through-v1-on-kind-plan.md`
severity: medium
reason: Verified instead with a local Docker run of migrate, load, api and a --network none embed; ci.yml and eval.yml have not run on a PR.
status: done 2026-11-11
resolution: resolved by story 3.6's measurement (deploy/charts/ticketscope/values.yaml api resources, with the measured memory, CPU and embedding time) and story 3.8's integrated check on kind (tests/integrated/test_dense_kind.py); ci run 42910706544 integrated-check / deploy success (retro A8)

### DW-5: tests/postgres (the only tests of the dense SQL, vector literal and embedding transaction) skip in CI because nothing sets TICKETSCOPE_TEST_PG_IMAGE.
origin: spec-deferred 7e859249ed86
location: tests/postgres/conftest.py
source_spec: `tickets/epic-hybrid-retrieval/tickets/story-tracer-dense-search-answers-through-v1-on-kind-plan.md`
severity: medium
reason: grep of .github, scripts and pyproject finds no setter; a regression in _DENSE_SQL would stay green.
status: done 2026-11-11
resolution: resolved by PR #55 (74c1225, retro A3): ci.yml's containers job sets TICKETSCOPE_TEST_PG_IMAGE (.github/workflows/ci.yml:145) with TICKETSCOPE_REQUIRE_CONTAINER_TESTS=1, so a missing image fails instead of skipping; ci run 42915486385 containers success

### DW-6: Model download has no revision pin or file checksum (test-design C-7), and fastembed resolves a quantized Qdrant export.
origin: spec-deferred 016b9d8214a7
location: images/app.Dockerfile
source_spec: `tickets/epic-hybrid-retrieval/tickets/story-tracer-dense-search-answers-through-v1-on-kind-plan.md`
severity: medium
reason: images/app.Dockerfile downloads BAAI/bge-small-en-v1.5 unpinned; a changed upstream file would change retrieval under the same model_id.
status: resolved 2026-11-20
resolution: resolved by story 5.13: images/fetch_model.py downloads Qdrant/bge-small-en-v1.5-onnx-Q at EMBEDDING_MODEL_REVISION and fails unless model_optimized.onnx matches EMBEDDING_MODEL_SHA256 (tests/unit/test_model_pin.py)
carried_to: epic-eks-environment (5), the first epic to build the app image for a non-kind environment; overlaps the NFR CONCERNS on cross-machine ranking reproducibility (R-004, retro A6); carried at epic 3's closure (user, 2026-11-11)

### DW-7: Corpus identity and retrieval use separate connections, so a concurrent reload can label results with the previously read corpus version.
origin: spec-deferred a5abd69c08c2
location: src/ticketscope/http/app.py:224; src/ticketscope/adapters/postgres.py
source_spec: `tickets/epic-hybrid-retrieval/tickets/story-tracer-dense-search-answers-through-v1-on-kind-plan.md`
severity: medium
reason: The API reads corpus_version before mode availability and retrieval, each using a separate Postgres connection. Baseline keyword requests already have the same race. A concurrent old/new snapshot reload can therefore interleave with a response; request-snapshot consistency needs its own design.
status: open
carried_to: epic-eks-environment (5), where corpus reloads first run under live traffic; carried at epic 3's closure (user, 2026-11-11)

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-claude-desktop-answers-from-ticketscope-through-a-tunnel-plan.md`
  summary: The api HTTPRoute pins hostnames only when `hostname` is set, so with an empty `hostname` the tunnel host would also reach `/v1` and `/`.
  evidence: deploy/charts/ticketscope/templates/api.yaml:99 renders `hostnames` inside `with .Values.hostname`; kind and every real environment set it, so it needs a misconfigured release, but a chart guard (fail when mcp.tunnelHostname is set and hostname is empty) would close it.

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-tracer-setup-the-aws-account-and-bootstrap-layer-exist-plan.md`
  summary: The deploy role can still attach any managed policy to the `ticketscope-env-*` roles it creates, so CI can escalate through a new role.
  evidence: infra/bootstrap/policies/deploy-permissions.json.tftpl allows iam:AttachRolePolicy and iam:PutRolePolicy on `ticketscope-env-*` with no permissions boundary or iam:PolicyARN condition; story 5.2 shows which policies env needs, then a boundary closes it.

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-tracer-setup-the-aws-account-and-bootstrap-layer-exist-plan.md`
  summary: The read-only agent role may read `bootstrap/` state objects through ReadOnlyAccess (unverified).
  evidence: Would be settled by `aws s3 cp` of the bootstrap state under the read-only profile; state holds no secrets, so a deny on `bootstrap/*` is low value.

- source_plan: none
  summary: A demo consumer outside the service: a small LangGraph agent that triages a new bug report by calling `search_similar_issues` and `get_issue` over MCP and drafts a "likely duplicate of" note.
  evidence: The initiative rules out server-side LLM use (no server-side LLM generation; the MCP client's model writes the answer) and the spine keeps tool-call-behaviour evals out of scope, so a framework agent does not belong in the service. As a separate example or small repo it would show the MCP server works with a client other than Claude Desktop and could illustrate epic 8's README; the langchain-mcp-adapters API was not checked and needs verifying before any promise.

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-tracer-the-page-and-mcp-answer-over-https-on-the-fixed-hostn-plan.md`
  summary: eks-deploy.sh waits for the Gateway to be Programmed before any HTTPRoute exists (unverified, medium if true).
  evidence: If the ALB is only provisioned once a route attaches, the 10m wait fails before the app installs. The live tracer run settles it; if so, move the wait after the ticketscope release.
- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-tracer-the-page-and-mcp-answer-over-https-on-the-fixed-hostn-plan.md`
  summary: The EKS module's load balancer controller IAM policy may not cover the ALB Gateway API path (unverified, high if true).
  evidence: Only the attribute is tested. The live tracer run settles it: the Gateway provisions an ALB or the controller logs AccessDenied.

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-tracer-the-page-and-mcp-answer-over-https-on-the-fixed-hostn-plan.md`
  summary: external-dns wrote no TXT ownership records and so deleted neither DNS record at teardown (story 5.4 teardown must handle it).
  evidence: Tracer run 2026-11-17: after Gateway delete the A and AAAA alias records stayed in the bootstrap zone and no TXT records existed; deleted by hand. Settle why (registry txt for alias records, v0.23) or have env-down delete the records explicitly.
  resolution: the symptom is resolved by bug 5.12: `scripts/eks-teardown.sh` deletes the hostname's A and AAAA records after `terraform destroy` (deploy role statement `DeleteHostnameAddressRecords`). Why external-dns writes no TXT ownership records stays open (user, 2026-11-19).
- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-tracer-the-page-and-mcp-answer-over-https-on-the-fixed-hostn-plan.md`
  summary: The ALB's HTTPS listener uses the default `ELBSecurityPolicy-2016-08`, which allows TLS 1.0 and 1.1.
  evidence: Seen in the controller's built model during the tracer run; set a modern sslPolicy in the LoadBalancerConfiguration.

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-env-down-tears-down-in-order-finds-nothing-left-and-expires-plan.md`
  summary: Confirm that the ALB's and the CNI's ENIs carry the `environment` or `elbv2.k8s.aws/cluster` tag, so the ENI wait and the ENI leg of the leftover check are not vacuous (unverified, medium if true).
  evidence: `scripts/leftover-check.sh` and `scripts/eks-teardown.sh` list ENIs by those tags only; no recorded listing shows ENI tags. The live `--list` run in story 5.4's manual checks should print the ENIs of the Gateway's ALB; if none appear, filter by VPC id instead. `terraform destroy` fails on a leftover ENI, so a leak is loud rather than silent.
  resolution: bug 5.14 added the CNI's own tags (`eks:eni:owner=amazon-vpc-cni` with `cluster.k8s.amazonaws.com/name`) to the ENI wait and the leftover check, and a sweep of detached CNI interfaces in the environment's VPC. Whether the ALB's interfaces carry the `elbv2.k8s.aws/cluster` tag stays unverified, but a leak of them still fails `terraform destroy` loudly.

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-env-down-tears-down-in-order-finds-nothing-left-and-expires-plan.md`
  summary: external-dns writes no TXT ownership records, so policy `sync` never deletes the hostname's A and AAAA records (open since story 5.2; env-down now fails loudly on them).
  evidence: Live env-down 2026-11-19: after an ordered teardown the A and AAAA records stayed in the zone pointing at a dead ALB and broke the next env-up's DNS stage. `scripts/eks-teardown.sh` lists them read-only after `terraform destroy`, prints the delete commands and exits 3; the records are still deleted by hand. Settle why external-dns (registry `txt`) writes no ownership records for the alias records, then let it delete them or have env-down delete them explicitly.
  resolution: the symptom is resolved by bug 5.12: `env-down` now deletes the records explicitly (only the hostname's A and AAAA, DELETE only) and no longer needs a hand step. The cause, external-dns writing no TXT ownership records, stays open (user, 2026-11-19).

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/bug-teardown-leaves-the-hostnames-dns-records-behind-plan.md`
  summary: The deploy role's `route53:ChangeResourceRecordSetsNormalizedRecordNames` condition may not match the hostname as written, which would deny the record delete (unverified, medium if true).
  evidence: The template compares to the bare lowercase hostname; whether AWS normalises with or without the trailing dot is not tested. After the bootstrap re-apply, a live `env-down` that exits 3 with AccessDenied on `change-resource-record-sets` settles it; the fix is the other form of the name in the condition.
  resolution: settled 2026-11-20 by a live `env-down` (run 44774843987): the delete succeeded with the bare lowercase hostname in the condition, so AWS normalises without the trailing dot; no change needed

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-cloudnativepg-backs-up-to-the-bootstrap-bucket-through-an-ir-plan.md`
  summary: Barman Cloud Plugin issue 892: with `inheritFromIAMRole` on, the plugin's Role can read every Secret in the namespace.
  evidence: Accepted for the single-purpose `ticketscope` namespace (story 5.6, epic Notes); the live run records the Secret names and the plugin Role's rules. Not fixed here.

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-cloudnativepg-backs-up-to-the-bootstrap-bucket-through-an-ir-plan.md`
  summary: The ScheduledBackup (`0 0 3 * * *`) has never fired on EKS, and no retention prune has run, so `DeleteObject` on `backups/*` is granted but unexercised.
  evidence: Every environment so far lived under 4 hours and none spanned 03:00 UTC; the render is unit-tested and the on-demand Backup and the restore drill (run 45219791550, 2026-11-23) are live-proven. Story 5.9's longer recreate window, or an `env-up` dispatched before 03:00 UTC, shows the fire; a prune past the retention window shows the delete, or the action is dropped from the policy.

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/bug-teardown-leaves-the-cni-network-interface-and-destroy-fails-plan.md`
  summary: No live `env-down` has yet deleted a leaked CNI interface through the deploy role; the one live denial was on a node's primary interface mid-deletion, read as a race but not decoded.
  evidence: Runs 45219791550/45227025415 (2026-11-23): the leak of run 44619309245 did not recur and the role's three deletes hit interfaces that were already going (two NotFound, one UnauthorizedOperation). The statement simulates as allowed for the CNI tag. The read-only role lacks `sts:DecodeAuthorizationMessage`, so the denial was not decoded; a person can decode it from that run's log. A recurrence shows in the teardown log as `could not remove` followed by a failed destroy.

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-a-recreated-environment-backs-up-to-and-restores-from-the-sa-plan.md`
  summary: `scripts/leftover-check.sh` has no confirmation path for EC2 subnets, so a destroyed environment's tagged subnets read as `LEFTOVER ... (unconfirmed)` and fail `env-down` although nothing remains.
  evidence: Runs 45266017998 and 45272176321 (2026-11-23) both ended with a failed leftover check on subnets from the destroy that had just completed; a subnet from the first run was still listed 40 minutes later (the backstop sweeps at 22:33Z still failed on a stale tagged volume; the 23:22Z sweep found nothing tagged), and `describe-subnets` returned InvalidSubnetID.NotFound for it. Volumes are confirmed through `describe-volumes` and print `GONE (tagging API lag)`. A subnet check needs `describe-subnets` in the confirmations, then it drops a subnet that returns NotFound.

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-an-instance-failure-is-survived-and-the-drill-is-recorded-plan.md`
  summary: The failure drill (`scripts/failure-drill.sh`) has never run live, so R10 (a node loss survived, a standby promoted, search answering) and the plugin #828 question are unproven.
  evidence: Story 5.8 was accepted as built on 2026-11-24 with only the stubbed script tests and the offline render of the placement rule; `docs/drills/failure-drill.md` is the "not yet run" skeleton. A person runs the drill last in the December window with the admin AWS profile and kubeconfig and commits the rendered record; a failed archive check there is the #828 finding to resolve, not a reason to drop the second instance.

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-mcp-oauth/tickets/story-tracer-mcp-refuses-a-tokenless-call-and-answers-a-call-with-plan.md`
  summary: A malformed JWKS entry makes `RSAAlgorithm.from_jwk` raise and the whole key fetch fail, so every token gets 503 once the cache expires; entries with `use: "enc"` are also accepted as signing keys.
  evidence: Fresh review of PR #104 (2026-11-27), `src/ticketscope/mcp/auth.py` `KeyCache._fetch`. Story 6.3 owns unreachable keys and key handling: skip entries that fail to parse or are not `use: sig`, and keep the rest.

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-mcp-oauth/tickets/story-tracer-mcp-refuses-a-tokenless-call-and-answers-a-call-with-plan.md`
  summary: The discovery document's `issuer` is not compared with the configured issuer (RFC 8414 section 3.3) and `jwks_uri` is used whatever its scheme or host.
  evidence: Fresh review of PR #104 (2026-11-27); the story's own review rejected it because the configured issuer is the trust root. Story 6.3 decides: check `issuer` equality and require an https `jwks_uri` on EKS.

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-mcp-oauth/tickets/story-tracer-mcp-refuses-a-tokenless-call-and-answers-a-call-with-plan.md`
  summary: A token signed by a key rotated in shortly after a cache fill is refused with 401 invalid_token for up to `MIN_REFETCH_SECONDS` (30 s), which can push a client to refresh or sign in again.
  evidence: Fresh review of PR #104 (2026-11-27); pinned today by `test_a_new_key_inside_the_refetch_interval_is_refused_not_refetched`. Story 6.3's rotation criterion decides: exempt the first unknown-kid refetch after a fill, or answer 503 while the window blocks it.

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-mcp-oauth/tickets/story-tracer-mcp-refuses-a-tokenless-call-and-answers-a-call-with-plan.md`
  summary: Refusals do not follow RFC 6750 section 3.1: a non-Bearer scheme gets `error="invalid_token"` (it should get a bare challenge), and two Authorization headers get 401 (it should be 400 `invalid_request`).
  evidence: Fresh review of PR #104 (2026-11-27); pinned today by `test_a_malformed_or_non_bearer_header_is_401_invalid_token` and `test_two_authorization_headers_are_401_invalid_token`. Story 6.3 owns the refusal cases.
