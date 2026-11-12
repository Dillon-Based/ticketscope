---
workflowStatus: 'completed'
totalSteps: 5
stepsCompleted: ['step-01-detect-mode', 'step-02-load-context', 'step-03-risk-and-testability', 'step-04-coverage-plan', 'step-05-generate-output']
lastStep: 'step-05-generate-output'
nextStep: ''
lastSaved: '2026-11-12'
runScope: 'epic'
runKey: 'epic-5'
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-eks-environment/epic-eks-environment.md
  - _bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md
  - _bmad-output/test-artifacts/test-design/test-design-epic-4.md
  - _bmad-output/test-artifacts/gate-waivers.md
  - .github/workflows/ci.yml
  - .github/workflows/mcp-e2e.yml
  - .github/kind-paths.yml
  - deploy/charts/platform/values-kind.yaml
  - deploy/charts/ticketscope/templates/mcp.yaml
  - tests/unit/test_chart_mcp.py
  - tests/unit/test_mcp_workflow.py
  - scripts/time-load.sh
  - pyproject.toml
  - knowledge/risk-governance.md
  - knowledge/probability-impact.md
  - knowledge/test-levels-framework.md
  - knowledge/test-priorities-matrix.md
  - knowledge/nfr-criteria.md
---

# Test Design: Epic 5 - terraform apply brings up the live URL on EKS in under 30 minutes

**Date:** 2026-11-12
**Author:** Dillon
**Status:** Draft

Epic slug: `epic-eks-environment`. Epic requirements R1–R11 (initiative R3, R10, R11). Stories 5.1 to 5.11 from `tickets/tickets.toml`. Story 5.2 is the tracer. Stories 5.1 to 5.4, 5.6, 5.7 and 5.9 form one lane, because each edits `infra/env`, `values-eks.yaml` or the env workflows. Story 5.5 (PR gate) and story 5.8 (failure drill) run beside it. Criterion tags follow `ticketscope--e5-s<n>--AC-<k>`.

---

## Executive Summary

**Scope:** full test design for Epic 5, against the refined epic (`refined: true`, `risk: high`), the adopted architecture spine (AD-13 to AD-18, AD-21 to AD-25, and the open question on the AWS account plan) and the eleven entries in `tickets/tickets.toml`. Every coverage row cites the epic R ids it proves, so the end-of-epic trace can link criteria to requirements.

The epic and its stories are committed on branch `epic-5-refine` (commit `7b8c832`), not yet on `main`. No epic 5 code exists: there is no `infra/`, no `values-eks.yaml`, no `env-up.yml`, `env-down.yml` or `env-check.yml`, and no `eks-deploy.sh`. Every scenario below is planned, and none has run. The epic's own Notes say nothing in its feasibility research was tested live on AWS, and 15 of its 31 claims are unverified.

This is the first epic whose evidence comes from paid, short-lived infrastructure. Three properties shape the plan:

- **Most failures are first visible on AWS.** The Gateway, certificate and DNS chain, the teardown order, the backup role and the instance failure cannot be exercised on kind. The plan therefore keeps every offline check it can in `ci.yml` (renders, Terraform validation, workflow and script logic against recorded AWS output) and spends environment-hours only on what needs AWS.
- **A test run costs money.** The epic budgets about 25 environment-hours a month at $0.22 to $0.32 each. The plan's own live runs are estimated at 15–25 environment-hours (Resource Estimates), which is enough to break R5 for the month that holds them.
- **A passing check can be vacuous.** The leftover check finds resources by tag. If controller-created resources carry no such tag, it reports clean on an environment that leaks. The plan requires a positive control: the check must find the Gateway's ALB, target groups, security group and volumes while the environment is up.

**Risk Summary:**

- Total risks: 11
- High-priority risks (≥6): 6 (R-001, R-002, R-003, R-005, R-007 and R-008, each at 6)
- Critical categories: DATA (archive reuse across incarnations), OPS (teardown and cost), TECH (an unproven Gateway, certificate and DNS chain, and an open plugin bug on failover)

**Coverage Summary:**

- P0 scenarios: 25 (~15–30 hours)
- P1 scenarios: 123 (~49–98 hours)
- P2/P3 scenarios: 19 (~7–14 hours)
- **Total effort**: ~71–142 hours (~2–4 weeks of test work, spread across the eleven stories)

---

## Not in Scope

| Item | Reasoning | Mitigation |
| ---- | --------- | ---------- |
| **OAuth, and auth on the live URL** | "Epic 6's OAuth flow ... run[s] on this URL" (Description). `values-eks.yaml` carries auth off here. | P0 row (D) checks what the public hostname exposes while there is no auth. The allowlist test already admits the auth keys epic 6 will add. |
| **Prometheus, the dashboard, resource headroom for them** | "Prometheus and the dashboard are epic-grafana-dashboard's" (Boundaries). | R-006's row records the memory headroom left on the two nodes, so epic 7 starts from a measured figure. |
| **Recording the demo and the README's live link** | Out per Boundaries (epic-reviewer-package). | The drill records are the evidence epic 8 links. |
| **A second environment, a staging copy, always-on hosting, autoscaling, EKS Auto Mode, Fargate** | Out per Boundaries and AD-16. | The workflows' concurrency group (P1 row on workflow wiring) enforces one environment at a time. |
| **Retrieval quality, default mode, `api` resources, embedding model** | Belong to epics 2 and 3 (Boundaries). | Tests read defaults from `values.yaml` and never hard-code them. The chart rows fail when `values-eks.yaml` overrides them (AD-25). |
| **Page and `/mcp` latency or throughput targets** | No source states a latency or throughput budget for the live URL. | NFR Planning lists the missing thresholds as UNKNOWN. No scenario asserts a number except the 30-minute clock. |
| **Whether sign-up credits cover EKS, EC2 and ELB** | "Open question ... does not gate the build" (epic Notes). | Story 5.1's plan records the console's terms. No test depends on the answer. |
| **Changing kind or CI behaviour** | "Must not change: kind and CI behaviour" (Boundaries). | The kind regression rows (P1) keep `ci.yml`, `mcp-e2e.yml` and `eval.yml` green on every story's PR. |
| **Waiver W-001 remediation** | An open item from epic 2, owned by Dillon. | Not an exit criterion of this epic. |

---

## Risk Assessment

Sources were read in this order: the epic file (Requirements, Constraints, Done when, Boundaries, Notes), the epic's `tickets.toml`, then the spine's AD-13 to AD-18 and AD-21 to AD-25. Each risk opens with the source's own words, then states the failure consequence. IDs follow the order in which each risk's gap statement first appears in those sources. Statements that describe a control as already decided (the workflow installs the Gateway API CRDs, an explicit certificate ARN, the Paid plan, Pod Identity as fallback, the `serverName` per incarnation) are scope constraints and carry coverage rows with `-` in `Risk Link`, not scored risks.

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- | -------- |
| R-001 | DATA | R11 and AD-18: "A cluster recreated with the same name against the same bucket path fails the WAL archive check ('Expected empty archive')", and `skipEmptyWalArchiveCheck` is never used. Story 5.9 adds that "the same-name failure rests on one open plugin issue (767) ... not reproduced on current ones". Mechanisms: (a) the incarnation id is derived from something stable (cluster name, SHA), so a new Cluster meets the old prefix; (b) `serverName` is set on the Cluster but the `ObjectStore` path or the restore's `externalClusters` still names the old one, so a restore reads the wrong archive; (c) a retried `env-up` reuses the id of a half-created environment. Consequence: the second environment cannot archive, or overwrites the first incarnation's WAL, and the backup that R9 and R11 restore from is lost. | 2 | 3 | 6 | `env-up` generates the incarnation id from the run id and attempt, and refuses an id whose prefix already exists before `terraform apply`. `serverName` is one value used by the Cluster plugin entry, the `ObjectStore` path and the recovery `externalClusters`. Row (R-001) runs the recreate sequence. | Dillon; stories 5.6, 5.9 | `serverName` wiring in 5.6; recreate proof in 5.9 |
| R-002 | TECH | "Does external-dns write the Route53 alias from an ALB-backed Gateway end to end? No primary source shows it working or failing" (epic Notes, Open question). Constraints name the fallback (`external-dns.kubernetes.io/target` on the Gateway) and say "If neither works, that is a replan". Consequence: the fixed hostname does not resolve, so R1 and R2 are unproven and the epic is replanned. | 2 | 3 | 6 | Story 5.2 runs the chain by hand and records the certificate mode the controller used, the address source external-dns read, and whether the target annotation was needed. `--policy=sync` runs dry-run first on external-dns 0.24. | Dillon; story 5.2 | First `env-up` (5.2) |
| R-003 | OPS | "a controller removed first leaves the Gateway stuck and its AWS resources behind (source reading, not tested)" (epic Notes, Source conflict on AD-24). Story 5.4 repeats it. Consequence: ALB, target groups, security group, ENIs and EBS volumes keep billing after `env-down`, and `terraform destroy` can stall on the VPC while ENIs and security groups still depend on it, so R3 and the budget (R-004) fail together. | 2 | 3 | 6 | `env-down` runs AD-24's order with the Gateway deleted and its ALB confirmed gone before `platform` is uninstalled. The plan states how long the wait runs and when it gives up, reporting the finalizer and never force-deleting. The tracer's hand teardown (5.2) follows the same order. | Dillon; stories 5.2, 5.4 | Hand teardown in 5.2; workflow in 5.4 |
| R-005 | PERF | Epic Notes: "`env-up` records the time of each stage, so the tracer shows early whether the target is reachable". Story 5.3 notes "the control plane alone takes about 10 to 15 minutes" and "If the run takes 30 minutes or more ... the target moves only with the user". Per-stage budgets are not stated, and the clock includes the corpus load. Mechanisms: control plane and node join, image pulls from ECR over public subnets, two CNPG instances, the corpus load, ALB target health, and DNS visibility. A resolver that cached an NXDOMAIN while the record was absent could delay the smoke check by the SOA negative-cache time (UNKNOWN; Route53's default is believed to be 900 s, not verified). Consequence: the epic's title is false, and the user decides whether the target moves. | 2 | 3 | 6 | Story 5.2 times every stage by hand. Story 5.3 records stage times in the job summary, including a separate `dns_visible` stage measured against the zone's authoritative name servers before the public resolver is polled. A run at or over 30 minutes is recorded as a Decision before the target changes. | Dillon; stories 5.2, 5.3 | Stage times in 5.2; recorded run in 5.3 |
| R-007 | TECH | "Unknown: whether failover with two instances archiving to one archive hits the plugin's open bug #828 ... R10's failure drill runs the two-instance case" (epic Notes). Story 5.8 says a one-instance drill "does not weaken the drill". Consequence: after the primary's node is lost, WAL archiving or the promoted standby breaks, and R10 is unmet. A one-instance drill would not satisfy initiative R3. | 2 | 3 | 6 | Story 5.8 runs the two-instance case. If #828 bites, the record keeps exactly what failed and proposes the fix or the limit. The Barman Cloud Plugin is pinned to 0.16.0 or later. | Dillon; story 5.8 | Drill in 5.8 |
| R-008 | TECH | "Unknown: the exact minimum S3 IAM policy for backup, WAL archive, restore and retention. No document publishes one, and the candidate set in the research is inferred and untested" (epic Notes). The bootstrap bucket also holds Terraform state, so the role has to be prefix-scoped. Consequence: a policy too narrow makes archiving, restore or retention fail, and WAL piles up on the primary's volume (UNVERIFIED mechanism); a policy too wide lets the backup role read or overwrite the Terraform state objects. | 3 | 2 | 6 | Story 5.6 starts from the candidate set and tightens it against failures, recording the exact set that was needed. The policy is prefix-scoped to the backup prefix and excludes the state prefix. The role is checked with IAM policy simulation under the read-only profile. | Dillon; story 5.6 | Before 5.7 and 5.9 rely on it |

Score rationale:

- **R-001:** probability 2, because AD-18 and story 5.9 both design around it and one open issue stands behind it. Impact 3, because every recreated environment writes to the same bucket, so a collision damages the evidence R9 and R11 depend on.
- **R-002:** probability 2, because the sources show no failure, only no success, and a fallback exists. Impact 3, because no live hostname blocks R1, R2, epic 6 and epic 8.
- **R-003:** probability 2, because the controller behaviour is a source reading and the teardown order is designed against it. Impact 3, because a leaked ALB and ENIs bill silently and block the next environment's VPC.
- **R-005:** probability 2, because the fixed stages alone use 10–15 minutes of the 30 and nothing is measured yet. Impact 3, because it is the epic's title and Outcome.
- **R-007:** probability 2, because the research reads the bug as likely avoided only by a one-instance demo. Impact 3, because R10 cannot be met by weakening the drill.
- **R-008:** probability 3, because the policy is inferred and untested. Impact 2, because the fix is a policy edit once the failure is seen.

### Medium-Priority Risks (Score 3-4)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- |
| R-004 | OPS | "one forgotten day breaks it at every node size" (Constraints, Teardown) and "The month's cost is tight, not comfortable: $7.84 ... about $13.20 after one forgotten day ... orphaned volumes or ALBs from a bad teardown are not in the estimate" (Notes). Every live run in this plan also spends environment-hours ($0.22 to $0.32 each, `tickets.toml` header). Consequence: the billing figure for the month that holds the recorded runs exceeds $10, and R5 fails. | 2 | 2 | 4 | A $8 budget alarm in Terraform, a 4-hour expiry stamped by `env-up`, and an hourly sweep. The plan schedules live runs across more than one calendar month and shares one environment between stories 5.6, 5.7 and 5.8 (Resource Estimates). C-1 and C-3 clarify how the figure is measured. | Dillon; stories 5.1, 5.3, 5.4, 5.11 |
| R-006 | PERF | "`t4g.large` ($9.52) is the fallback if the `platform` pods and two database instances do not fit in 8 GiB" (Notes). The fit is not measured: epic 3's chart defaults feed it, and epic 7 adds Prometheus later. Consequence: pods go Pending or OOMKilled on two `t4g.medium` nodes and `env-up` never reaches Ready. | 2 | 2 | 4 | Story 5.2 starts at `t4g.medium` and records requests, limits and node memory headroom after a full install. The documented fallback is one value change. | Dillon; story 5.2 |
| R-009 | OPS | "Does a new account's activation delay land inside the schedule? AWS says up to 24 hours, with community reports of 5 to 9 days that blocked domain purchase" (Notes). The deadline is 2026-12-31. Consequence: story 5.1, and so the whole lane, cannot start. | 2 | 2 | 4 | Create the account now, in parallel with epic 4. Story 5.1 starts only when the account answers `sts get-caller-identity` and a domain availability check succeeds. | Dillon; story 5.1 |
| R-010 | TECH | "Likely more than 800 added lines (infra/env, two values files, platform chart templates, script, tests): run the independent review on it; if the plan estimates well over 800 lines, split at the plan checkpoint" (story 5.2 notes). Story 5.2 also "commits the deploy script story 3's workflow calls". Consequence: a defect in the shared script or values reaches stories 5.3 to 5.9. | 2 | 2 | 4 | Story 5.2 keeps `plan_checkpoint = true` and names the independent review or the split. Story 5.3's workflow calls `scripts/eks-deploy.sh` unchanged. | Dillon; story 5.2 |

### Low-Priority Risks (Score 1-2)

| Risk ID | Category | Description | Probability | Impact | Score | Action |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ------ |
| R-011 | SEC | "Plugin issue 892 grants read access to every Secret in the namespace when inheritFromIAMRole is on; it is acceptable in this single-purpose namespace and is recorded, not fixed here" (story 5.6 notes). Consequence: a pod using the plugin's role can read every Secret in the namespace, so a future Secret placed there is exposed. | 2 | 1 | 2 | Accept, as the story does. Story 5.6 records the namespace's Secret names and the Role's rules, and the row fails if a Secret appears that the chart does not own. |

### Clarifications for the PO (not scored)

The sources are silent or unclear on these points. Each entry gives the question and the proposal. Dillon decided all eight on 2026-11-12, taking the recommended option each time (see "Decisions" below). "Proposed Story Updates" carries the wording into the stories, which the PO has not yet applied.

- **C-1, how the month's billing figure treats the domain.** R5 asks for "the billing figure for a month that holds recorded runs ... under $10", domain included. The epic's $7.84 amortises a $16 `.com` over twelve months. If Cost Explorer books the registration fee in the month it is charged (expected, not verified), a month holding the purchase shows at least $16 and fails R5 whatever the runs cost. *Proposed:* state the measure (amortised: annual fee divided by 12), or pick a month with no domain charge and say so in story 5.11. The plan records the figure both ways.
- **C-2, where live verification runs, and what the deploy role admits.** GitHub runs a `schedule` trigger only from the default branch, and dispatching a workflow that exists only on a feature branch is not supported (from GitHub's documentation as recalled; not re-checked in this session). Story 5.1's deploy role trusts "this repo's main branch and a named environment". Stories 5.3, 5.4 and 5.9 observe dispatched and scheduled runs. *Proposed:* each of those stories' plans states whether its live check runs from the branch, through the named environment's branch rule, or after merge to `main`. The scheduled-expiry check in 5.4 can only be observed after merge.
- **C-3, what "expires within 4 hours" means, and how reliable the sweep is.** "Every environment [the agent] dispatches expires within 4 hours" (Agent access) and AD-24's expiry stamp are read by an hourly sweep, so an environment lives up to its expiry plus up to one hour plus the teardown time. If the repository is public, GitHub also disables scheduled workflows after 60 days without repository activity (from documentation as recalled; not verified), which would silently end the sweep. The $8 alarm warns but destroys nothing. *Proposed:* define the bound as "expiry + sweep period + teardown time", and decide whether the alarm is a sufficient backstop. The plan asserts the bound at story 5.4.
- **C-4, the `values-eks.yaml` allowlist.** AD-25 lists hostname, gateway class, storage class, backup endpoint, auth, issuer and replica counts. Story 5.6 adds an IRSA role annotation and the `serverName`, and story 5.8 adds a required placement rule for the two instances, none of which AD-25 names. *Proposed:* the allowlist test in story 5.5 names these keys explicitly, and AD-25 gains one line saying so, so a later epic cannot widen the file unnoticed.
- **C-5, public exposure of the EKS API and the nodes.** The environment uses public subnets with no NAT, so nodes hold public IPs, and GitHub-hosted runners reach the cluster over the network. Neither the endpoint's access mode nor the node security-group rules are stated. *Proposed:* state the intended endpoint mode, and let P0 row (D) assert it together with node security groups that admit no inbound traffic from the internet apart from the load balancer's listener ports.
- **C-6, tag propagation to controller-created resources.** R3's check finds leftovers by the environment tag. The AWS Load Balancer Controller and the EBS CSI driver create ALBs, target groups, security groups and volumes, and tag them only if told to (the charts' default-tag and extra-volume-tag settings; names from memory, to confirm in the plan). *Proposed:* story 5.2's plan sets those values, and story 5.4's check includes the positive control in row (R-003).
- **C-7, what "corpus loaded" is checked against.** Story 5.3's verify checks that a search returns results. Story 5.9 prints `corpus_meta` and the issue count. A load that stops partway still returns results. *Proposed:* the smoke check compares the issue count with the pinned snapshot's manifest count, which the load did not produce, from story 5.3 on.
- **C-8, sharing one environment between stories 5.6, 5.7 and 5.8.** All three are hitl and need a live environment. *Proposed:* run the backup, restore drill and node-loss drill in one environment window, the destructive node loss last, which fits the 4-hour expiry and saves two to four environment-hours.

**Decisions (Dillon, 2026-11-12):**

- **C-1:** amortised. Story 5.11 counts the domain as the annual fee divided by 12 and also records the raw Cost Explorer figure.
- **C-2, C-3:** the deploy role trusts a named GitHub environment whose branch rule admits story branches. The scheduled sweep is observed after merge. The expiry bound is "expiry + sweep period (1 hour) + teardown time".
- **C-4:** AD-25 gains one line naming the IRSA role annotation and the instance placement rule as environment facts. Story 5.5's allowlist names them.
- **C-5:** the EKS API endpoint is public and IAM-authenticated. P0 row (C) asserts that node security groups admit no inbound internet traffic except the ALB's listener ports.
- **C-6:** story 5.2 sets the controller and EBS tag settings and captures real `aws` output. Story 5.4's check includes the positive control.
- **C-7:** the smoke check compares the issue count with the pinned manifest count from story 5.3 on.
- **C-8:** stories 5.6, 5.7 and 5.8 share one environment window, node loss last.

Applied on 2026-11-12 to `tickets.toml`, the epic Notes and AD-25.

### Risk Category Legend

- **TECH**: Technical/Architecture (flaws, integration, scalability)
- **SEC**: Security (access controls, auth, data exposure)
- **PERF**: Performance (SLA violations, degradation, resource limits)
- **DATA**: Data Integrity (loss, corruption, inconsistency)
- **BUS**: Business Impact (UX harm, logic errors, revenue)
- **OPS**: Operations (deployment, config, monitoring)

---

## NFR Planning

**Purpose:** Capture epic-specific NFR thresholds, planned validation, and evidence expected for later `nfr-assess`. This is not a final evidence audit.

| NFR Category | Requirement / Threshold | Risk Link | Planned Validation | Evidence Needed |
| ------------ | ----------------------- | --------- | ------------------ | --------------- |
| Performance | `env-up` under 30 minutes, from the start of `terraform apply` until the page and `/mcp` answer over HTTPS (R1). Per-stage budgets, page latency and failover time targets are UNKNOWN. | R-005 | E2E: a recorded `env-up` with stage times, cross-checked against GitHub's own step timestamps. Unit: the summary's stages add up and start at `terraform apply`. | Job summary and artifact; `gh run view` step times |
| Security | No AWS key in repo secrets or variables; deploy role trusts only this repo (R6); backups through IRSA; Grafana, Tempo and SeaweedFS never public (AD-14); no credential, account id or alert email in committed files. | R-008, R-011 | Unit: rendered trust and backup policies, secret scan, workflow parse. E2E: policy simulation, public-edge probes, `gh` listing of secrets and variables. | `ci.yml` report; recorded probe output; story 5.1 and 5.6 plans |
| Reliability | Two instances in every environment; a promoted standby keeps search answering (R10); a backup restores with matching `corpus_meta` and issue count (R9); a recreated environment backs up to and restores from the same bucket (R11). No recovery-time or failed-request threshold is stated, only "recorded". | R-001, R-007 | E2E: the three drills and the recreate sequence, each with an independent oracle. | `docs/drills/` records; `env-check.yml` run |
| Cost | Under $10 for a month, bootstrap and domain included (R5); $8 alarm; about 25 environment-hours a month; 4-hour default expiry. | R-003, R-004 | Unit: alarm and expiry default in Terraform and workflow. E2E: expiry sweep, leftover check with positive control. Recorded: Cost Explorer figure, both measures (C-1). | Story 5.11's Notes entry; Cost Explorer under the read-only profile |
| Maintainability | The same `platform` and `ticketscope` charts install on kind and EKS; `values-eks.yaml` holds environment facts only (R7); Terraform owns only AWS resources (AD-23); fmt and validate pass for both stacks. | R-010 | Unit: render of both environments, allowlist and override test, `terraform fmt`, `validate`, `terraform test`. | `ci.yml` report |

**Unknown thresholds:**

- per-stage time budgets inside the 30 minutes;
- page and `/mcp` latency over the ALB;
- a target for failover time and for failed requests during it;
- memory and CPU headroom on two `t4g.medium` nodes (R-006);
- data-transfer cost, which the epic "assumed at a few cents and unpriced from a source";
- the sweep's tolerance: how long past expiry an environment may live (C-3).

Story 5.2 records the first stage times and node headroom. Story 5.11 records the cost figures.

---

## Independent Oracles

Several rows compare a result with something the code under test did not produce. Each oracle below comes from a different tool, API or source than the code it checks.

**Protocol:**

1. Story 5.2 captures real `aws` list output for the environment's resources while it is up and after the hand teardown, from the read-only profile, with account ids and addresses masked. The leftover check's unit tests use these recordings. The build session does not write them from its own assumptions.
2. A red-mode `/bmad-tea-automate` session writes the P0 trust-policy and bootstrap-protection tests before stories 5.1 and 5.4 build (Follow-on Workflows).
3. Recorded fixtures get pin tests that guard their bytes, as `tests/unit/test_key_oracle_pinned.py` does for epic 4.

| What is checked | Independent oracle | Row |
| --------------- | ------------------ | --- |
| The leftover check sees controller-created resources | Controller-owned tags and the cluster tag on the ALB, target groups, security groups and volumes, listed through `aws elbv2` and `aws ec2` calls that do not filter on our environment tag | R-003 |
| Nothing but the environment was destroyed | `terraform plan -lock=false` of `infra/bootstrap` under the read-only profile shows no change after `env-down` | P0 (B) |
| The deploy role cannot delete bootstrap resources | IAM policy simulation of the real role against the bootstrap bucket, zone, certificate and ECR ARNs, not a read of the policy text | P0 (B) |
| The 30-minute clock | GitHub's job and step start and completion times from `gh run view --json jobs`, compared with `env-up`'s own recorded time | R-005 |
| The corpus is complete after load and after restore | The pinned snapshot's manifest issue count, and an ordered digest of issue numbers computed by a separate query on the source and the restored cluster | P1 restore drill |
| Failed requests during failover | The external probe's own log, cross-checked against the ALB's CloudWatch 5xx and healthy-host metrics (optional; names not verified) | R-007 |
| The backup role's effective permissions | IAM policy simulation of the role against the backup prefix and the state prefix | R-008 |
| The month's cost | Cost Explorer's EKS, EC2, ELB and Route53 lines against the summed environment-hours in the job summaries | R-004 |

---

## Entry Criteria

- [x] Architecture spine adopted, with AD-14, AD-18 and AD-24 amended for the EKS research (2026-11-12)
- [x] Epic refined, with eleven entries planned in `tickets.toml`
- [ ] Branch `epic-5-refine` merged to `main`, so the epic and stories are on `main`
- [ ] Stories 1.11 (epic 1 integrated check), 3.8 (epic 3 chart defaults and embedding assets) and 4.7 (epic 4 integrated check) done, as stories 5.2 and 5.3 require
- [ ] AWS account created and active, on the Paid plan, with MFA on the root user (R-009)
- [x] C-1 to C-8 decided (Dillon, 2026-11-12)
- [x] C-1 to C-8 written into the stories, the epic Notes and AD-25 (Proposed Story Updates; applied 2026-11-12)
- [ ] Story 5.1's plan records the read-only profile name and the way to assume it, without any account id
- [ ] `.gitignore` covers Terraform state, plan files, `.terraform/` and `*.tfvars` before story 5.1's first commit (P0 row (E))

## Exit Criteria

- [ ] All P0 tests passing
- [ ] All P1 tests passing (or failures triaged)
- [ ] No open high-priority / high-severity bugs
- [ ] A recorded `env-up` under 30 minutes, with stage times, and `env-check.yml` green on one SHA with the leftover check clean (R1, R3, R4)
- [ ] Restore, failure and recreate records committed and linked from the epic Notes (R9, R10, R11)
- [ ] The month's billing figure recorded under $10, by the measure C-1 settles (R5)
- [ ] `ci.yml`, `mcp-e2e.yml` and `eval.yml` pass on the closing PR head with `eval/baseline.json` unchanged
- [ ] R-001, R-002, R-003, R-005, R-007 and R-008 mitigations complete

---

## Test Coverage Plan

P0, P1, P2 and P3 are priorities, not execution timing. The Execution Strategy section decides when each test runs. The Owner column names the story whose build writes the test or performs the run. The R ids column names the epic requirements each row proves.

Test Level uses the template's canonical names:

- **Unit:** functions, scripts, Terraform plans against mocked providers, chart renders and workflow files, with no AWS and no cluster. Scripts run against stub CLIs and recorded AWS output.
- **Integration:** one owned store. No row needs one: this epic adds no database code, and `tests/postgres` is untouched.
- **API:** one service's HTTP boundary in process. No row needs one: the page and `/mcp` contracts belong to epics 1 and 4, and are exercised here only through the live hostname, which is E2E.
- **E2E:** a run on EKS (a person's, an agent's dispatch, or `env-check.yml`), or a read of the real AWS account.

Live scenarios in different rows often share one run. A run is listed once in Resource Estimates, however many rows read its result.

### P0 (Critical)

**Criteria**: Critical business, security, data-integrity, or compliance impact with no safe
workaround. Risk score is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| (A) The deploy role trusts only this repo, and no workflow or file holds an AWS key | R6 | Unit | - | 6 | Stories 5.1, 5.3 | Constraint: "no cloud key is stored in the repo or its secrets" (R6, Constraints). Consequence: a wildcard or missing `sub` condition lets any GitHub repository assume a role that can create EKS, so an attacker spends the account's money, and nothing signals it. No workaround after the fact except deleting the provider. Scenarios, on the rendered trust policy (`terraform test` with a mocked provider, or the plan JSON): (1) the OIDC provider's audience is `sts.amazonaws.com`. (2) The role's `sub` condition equals this repo's `main` ref or its named environment, with `StringEquals`, never `StringLike` and no `*`. (3) No other principal is trusted. (4) No workflow file contains `aws-access-key-id`, `AWS_SECRET_ACCESS_KEY` or `secrets.AWS_`. (5) `id-token: write` appears only on jobs that assume the role, and `contents: read` otherwise. (6) The credentials step names `role-to-assume` from a variable that holds no secret. |
| (B) `env-down`, its leftover check and the deploy role never touch the bootstrap layer | R3 | Unit | - | 5 | Stories 5.1, 5.2, 5.4 | Constraint: "bootstrap is never touched" (story 5.4). Consequence: deleting the zone, certificate, state bucket or ECR repositories loses the fixed hostname, the Terraform state and every backup, and the hostname's re-validation and name-server changes follow. No safe workaround. Scenarios: (1) The leftover check's filters select only resources carrying the environment tag, and a recorded bootstrap resource is never listed, never selected, never deleted. (2) `infra/env` declares no `resource` of the zone, certificate, state bucket, ECR or budget kinds, only reads them as `data` or outputs. (3) `env-down` has no command that names a bootstrap ARN. (4) The deploy role's policy, rendered, denies delete on the bootstrap bucket (state prefix included), zone, certificate and ECR. (5) *Live read, story 5.4:* IAM policy simulation of the real role against those ARNs returns denied, and `terraform plan -lock=false` of `infra/bootstrap` after the recorded `env-down` shows no change. Items 1 to 4 run offline in `ci.yml`. Item 5 is a read-only AWS check by the agent and is a Unit row only in that it needs no environment. |
| (C) Nothing is public except `/`, `/v1` and `/mcp` | R6 | E2E | - | 6 | Stories 5.2, 5.3 | Constraint: "Grafana, Tempo and SeaweedFS are never public" (Exposure, AD-14). There is no auth until epic 6. Consequence: an unauthenticated Grafana, Tempo or database path on the open internet, on a personal account. No workaround once exposed except teardown. Scenarios, probed from the runner against the live hostname: (1) `/`, `/v1/search` and `/mcp` answer. (2) Paths for Grafana, Tempo and SeaweedFS return 404 on the hostname. (3) `kubectl get httproute -A` in the workflow's smoke step lists only the `ticketscope` routes. (4) The ALB's security group admits inbound traffic only on its listener ports. (5) The node security groups admit no inbound traffic from `0.0.0.0/0` (C-5). (6) A request with another `Host` header is refused. |
| (D) The public hostname admits a `/mcp` call and a page search | R1 | E2E | - | 4 | Stories 5.2, 5.3 | Constraint: the page and `/mcp` answer over HTTPS on the fixed hostname (R1). Consequence: the epic's Outcome is false. This row is the user-visible check; it does not carry R-002 or R-005. Scenarios: (1) `GET /` serves the search page under the bootstrap certificate (chain and hostname verified, not `-k`). (2) A search returns ranked issues with outcomes. (3) An MCP client lists tools and calls `search_similar_issues` at `/mcp` over the hostname, so `allowed_hosts` and the route hostname admit it. (4) The MCP result equals a direct `POST /v1/search` through the same hostname for the same request, compared as parsed JSON. |
| (E) No credential, account id or alert email in any committed file | R6, R9, R10, R11 | Unit | - | 4 | Stories 5.1, 5.7, 5.8, 5.9 | Policy: AGENTS.md ("keep masking ... in every committed or published artifact"); story 5.1: "alert email and account details are Terraform variables that stay out of the repo". `.gitignore` has no Terraform entries today. Consequence: a published account id, key or personal email cannot be unpublished. No workaround. Scenarios: (1) `.gitignore` covers `*.tfstate*`, `*.tfvars`, `.terraform/` and plan files, and `git ls-files` lists none. (2) A scan of tracked files finds no 12-digit account id, no `AKIA`/`ASIA` key pattern and no email address in `infra/`, `docs/drills/` and the workflows. (3) Each drill record passes the same scan, and a planted account id in a temporary copy fails it. (4) Terraform variable declarations for the alert email and account details have no default. |

**Total P0**: 25 tests, ~15–30 hours

Row (B) item 5 and rows (C) and (D) read a live environment, so they run in the dispatches already counted in Resource Estimates.

### P1 (High)

**Criteria**: Core, frequent, or complex behavior with material user reach and a limited workaround.
Risk score is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| A recreated environment archives under its own `serverName` and restores from the previous one | R2, R11 | E2E | R-001 | 7 | Stories 5.6, 5.9 | Mechanism: an incarnation id reused, or one value out of three places that name the archive. Boundary: the Cluster, its plugin and the bootstrap bucket across two environment lifetimes, so E2E. Consequence: the second environment cannot archive, or overwrites the first's WAL. Workaround: reload the corpus from the pinned snapshot, which loses the drill evidence, so P1 and not P0. Scenarios: (1) *Unit, `ci.yml`:* an `env-up` input check refuses an incarnation id whose prefix exists, before `terraform apply`. (2) *Unit:* the Cluster, the `ObjectStore` and the recovery `externalClusters` render the same `serverName` from one value. (3) The agent dispatches `env-up`, `env-down` with `backup_first`, then `env-up` with `restore-from` set. (4) The second environment archives WAL under its own `serverName`, with no "Expected empty archive" and no `skipEmptyWalArchiveCheck` annotation. (5) Its `corpus_meta` and issue count equal the first's, against the manifest oracle. (6) The first incarnation's objects are unchanged: key list and sizes before and after. (7) Both environments served the same hostname under the same certificate ARN (R2). |
| The Gateway, certificate and DNS chain serves the fixed hostname | R1, R2 | E2E | R-002 | 6 | Story 5.2 | Mechanism: ALB, explicit certificate ARN, target type `ip`, and external-dns reading the Gateway's address. Boundary: AWS Load Balancer Controller, Route53 and the cluster, so E2E. Consequence: no live hostname, and a replan if neither address path works. Workaround: the `external-dns.kubernetes.io/target` annotation. Scenarios, by a person in the hand run: (1) the Gateway reports an address and the ALB is `internet-facing`. (2) The listener presents the bootstrap certificate by ARN, and the plan records which certificate mode the controller used. (3) The record in the bootstrap zone exists, shown by `dig` against the zone's name servers. (4) The plan records whether the target annotation was needed. (5) Targets register by pod IP and report healthy. (6) The `--policy=sync` dry-run lists only this environment's records. |
| `env-down` tears down in AD-24's order, and its leftover check can see what it checks for | R3 | E2E | R-003 | 7 | Stories 5.2, 5.4 | Mechanism: the controller is removed before the Gateway's ALB is confirmed gone. Boundary: workflow, Helm, the controller and AWS, so E2E. Consequence: orphaned ALB, ENIs, security group and volumes keep billing and can block `terraform destroy`. Workaround: delete them by hand in the console, which costs the money until noticed. Scenarios: (1) *Unit, `ci.yml`:* with stub `helm`, `kubectl` and `aws`, `env-down` calls the seven steps in AD-24's order, and a stub that never reports the ALB gone makes the job fail before `platform` is uninstalled. (2) *Positive control, live:* while the environment is up, the leftover check in read-only mode lists the ALB, at least one target group, the security group and the PVC volumes, and an oracle query by controller-owned tags agrees with it. (3) After `env-down`, the check reports nothing outside Terraform state. (4) A stuck Gateway is reported with its finalizer and the remedy, and the job fails without force-deleting. (5) The tracer's hand teardown (5.2) in the same order leaves no ALB, ENI, volume or security group by tag. (6) The ALB controller flag `manage-backend-security-group-rules` is left at its default (render test). (7) The wait's give-up time is stated and tested with a stub. |
| A forgotten environment destroys itself, and the cost guardrails exist | R4, R5 | E2E | R-004 | 6 | Stories 5.1, 5.3, 5.4, 5.11 | Mechanism: the expiry stamp, the hourly sweep and the budget alarm are the only cost controls. Boundary: scheduled workflow, the deployed environment and AWS Budgets, so E2E. Consequence: the month exceeds $10 (R5). Workaround: delete by hand when the alarm email arrives. Scenarios: (1) *Unit:* Terraform declares the $8 budget alarm, and `env-up`'s expiry input defaults to 4. (2) The environment carries an expiry tag set from the input. (3) An environment stamped with a 15-minute expiry is destroyed by the scheduled run with no dispatch, observed by the agent after merge (C-2), and the time past expiry is recorded against C-3's bound. (4) A failed smoke check leaves the environment up and the sweep later removes it. (5) The sweep skips an unexpired environment. (6) Cost Explorer's month-to-date figure matches the summed environment-hours within a stated tolerance (Independent Oracles). |
| `env-up` meets the 30-minute target and records its stages | R1 | E2E | R-005 | 6 | Stories 5.2, 5.3, 5.11 | Mechanism: the fixed stages (control plane, node join, image pulls, load, ALB health, DNS) add up to more than 30 minutes. Boundary: the workflow, Terraform, EKS, Helm and the public resolver, so a deadline across several deployables: E2E. Consequence: the epic's title is false. Workaround: the user moves the target, which the epic reserves to them. Scenarios: (1) the clock starts at `terraform apply` and stops when the smoke check passes. (2) A recorded run finishes in under 30 minutes. (3) The job summary lists each stage, and the stages sum to the total within a stated tolerance. (4) The recorded total agrees with GitHub's step timestamps from `gh run view`. (5) `dns_visible` is measured against the authoritative name servers first, then the public resolver. (6) A second dispatch for a SHA whose images exist skips the build job, and the skipped job is outside the timed window. |
| Failover with two instances keeps search answering | R10 | E2E | R-007 | 6 | Story 5.8 | Mechanism: the open plugin issue on two instances archiving to one archive. Boundary: two CNPG instances, the plugin, the ALB and a probe, so E2E. Consequence: R10 unmet. Workaround: none that satisfies R10, since a one-instance drill is not accepted. Scenarios, by a person: (1) the two instances run on different nodes before the failure. (2) A probe searches through the public hostname every second and runs from outside the cluster. (3) The node holding the primary is terminated. (4) A standby is promoted. (5) The probe succeeds again, and the recovery time and failed-request count are recorded. (6) After promotion, WAL archiving continues under one `serverName` with no archive error in the Cluster status, which is where #828 would show. |
| The backup role is least-privilege and every backup operation works under it | R6, R8 | E2E | R-008 | 7 | Story 5.6 | Mechanism: an inferred, untested minimum policy on a bucket that also holds Terraform state. Boundary: the IRSA role, the plugin sidecar and S3, so E2E. Consequence: archiving or retention fails, or the role reaches the state objects. Workaround: edit the policy. Scenarios: (1) with the candidate set, an on-demand backup completes with status completed and its objects sit under the incarnation's prefix. (2) WAL archiving runs under the role. (3) A restore read succeeds. (4) A retention delete succeeds. (5) IAM policy simulation denies reads and writes on the Terraform state prefix. (6) The pods hold no AWS key and the Cluster has no `skipEmptyWalArchiveCheck`. (7) The exact action set that was needed is recorded in the plan. |
| The account is active and the domain can be bought | R5 | E2E | R-009 | 3 | Story 5.1 | Mechanism: a new account's activation delay. Boundary: the account, Route53 Domains and billing, so E2E. Consequence: the lane cannot start. Workaround: none sourced (the research reports 5 to 9 days in some cases), which is why this row is P1 although its score is 4. Scenarios, as story 5.1's entry checks, by a person: (1) `sts get-caller-identity` answers under the admin identity. (2) A Route53 Domains availability check for the chosen name succeeds. (3) The plan records the plan type and the credit terms the console shows. |
| The leftover check names what it finds and nothing else | R3 | Unit | - | 6 | Story 5.4 | Logic of the control, on the recordings from Independent Oracles (1). Scenarios: (1) injecting a tagged ALB, target group, ENI, volume, security group, KMS key and log group each makes the check fail and name it. (2) Output with only tagged-and-in-state resources passes. (3) A resource carrying another environment's tag is ignored. (4) A bootstrap resource is ignored (shared with P0 (B)). (5) Dry-run mode injects a leftover and fails. (6) An `aws` error or empty listing from an unreachable API fails the check and never reads as clean. |
| Both charts render for both environments, and `values-eks.yaml` holds environment facts only | R7 | Unit | - | 10 | Stories 5.2, 5.5, 5.6, 5.8 | Boundary: `helm template` under the pinned Helm, offline. Scenarios: (1) `platform` and `ticketscope` render with `values-kind.yaml`, unchanged from today. (2) Both render with `values-eks.yaml`. (3) Every key in `values-eks.yaml` is on the allowlist (AD-25 plus the keys C-4 names). (4) A key present in both `values.yaml` and `values-eks.yaml` with a different value fails, shown by a planted override of `retrieval.defaultMode`, an `api` resource and the snapshot pin. (5) The Gateway listener and route hostnames are the live hostname, and no kind stand-in hostname appears on EKS. (6) `mcp`'s allowed hosts contain the live hostname and no wildcard. (7) EKS renders the AWS Load Balancer Controller, external-dns and the `LoadBalancerConfiguration` with an explicit certificate ARN, target type `ip` and `scheme: internet-facing`, and kind renders none of them. (8) EKS renders no SeaweedFS and kind still does. (9) The backup `ObjectStore` sets the role annotation and `serverName` on EKS and keeps static SeaweedFS credentials on kind (R6). (10) EKS requires the two instances on different nodes and kind does not (R10). |
| Terraform validates, and the plan holds to AD-23 and the leftover check's tags | R3, R7 | Unit | - | 9 | Stories 5.1, 5.2, 5.5 | Boundary: Terraform, no AWS. `terraform fmt -check` and `validate` run for both stacks in `ci.yml`. Plan-level scenarios use `terraform test` with a mocked provider, or validate only where the EKS module cannot be planned without credentials (Risks to Plan). Scenarios: (1) fmt and validate pass for `infra/bootstrap` and `infra/env`. (2) A deliberately broken module fails the check. (3) `infra/env` contains no `helm_release` or `kubernetes_*` resource (AD-23). (4) No NAT gateway, and subnets are public. (5) No customer-managed KMS key, and control-plane logging is off. (6) Cluster version is 1.36 and the node group is arm64. (7) Every taggable resource carries the environment and expiry tags. (8) Bootstrap: the bucket blocks public access, ECR keeps 10 images, and the lifecycle rule exists. (9) State for `env` is kept under its own key in the bootstrap bucket. |
| The env workflows have the triggers, inputs, guards and ordering the epic states | R1, R4, R6 | Unit | - | 9 | Stories 5.3, 5.4, 5.9, 5.11 | A parse test over the workflow files, as `tests/unit/test_mcp_workflow.py` does. Scenarios: (1) `env-up.yml` takes a SHA and an expiry in hours. (2) `env-down.yml` runs on dispatch and on an hourly schedule. (3) The timed jobs start at `terraform apply` and the build job precedes and is skipped when images exist. (4) All env workflows share one `concurrency` group with `cancel-in-progress: false`, so one environment exists at a time. (5) `env-check.yml` runs `env-down` and the leftover check with `if: always()` after a failed smoke check. (6) `env-up` takes `restore-from` and `env-down` takes `backup_first`. (7) Only the env workflows request `id-token: write`. (8) Nothing runs `terraform` or `helm` against the cluster on `pull_request`. (9) `env-check.yml` is dispatch only. |
| The smoke check proves a search and an MCP call, and can fail | R1 | Unit | - | 6 | Story 5.3 | Mechanism: a smoke check that cannot fail would let every live row pass vacuously. Boundary: test code against a fake server, no AWS. Scenarios: (1) a fake serving the page and `/mcp` passes. (2) No results, a 5xx, a wrong certificate name, a slow response beyond its timeout and an empty tool list each fail it. (3) It compares the issue count with the pinned manifest count (C-7). (4) It prints `corpus_meta` and the count into the summary. (5) It uses `tests/waiting.eventually` for every wait, never `time.sleep`. (6) It is selected by its own marker and excluded from default runs, as `-m kind` is. |
| Stories 5.1 and 5.3's identity checks hold on the real account | R2, R5, R6 | E2E | - | 7 | Story 5.1 | Boundary: the bootstrap layer against AWS, read by the agent under the read-only profile after a person's apply. Scenarios: (1) a second `terraform plan` of bootstrap shows no changes. (2) The certificate status is `ISSUED` for the fixed hostname. (3) The zone's name servers match the registered domain, by `dig`. (4) The $8 budget alarm exists. (5) The bucket's public access block and the ECR lifecycle (keep 10) read back from the CLI. (6) Under the read-only profile `sts get-caller-identity` works and creating a bucket is denied. (7) The profile's configuration is not in the repo. |
| `env-up` and `env-down` authenticate through OIDC, with no stored key | R6 | E2E | - | 3 | Stories 5.1, 5.3 | Boundary: GitHub Actions, the OIDC provider and the deploy role. Scenarios: (1) a dispatched run assumes the role and prints the caller identity. (2) `gh api` listing of the repo's secrets and variables shows no AWS credential. (3) A run from a ref the trust policy does not name is refused (C-2). |
| The hostname and certificate stay the same across environment lifetimes | R2 | E2E | - | 4 | Stories 5.3, 5.9 | Evidence comes from the two environments of the recreate sequence, not a separate run. Scenarios: (1) both `env-up` runs serve the same hostname. (2) Both present the same certificate ARN. (3) The record points at the new ALB after the second `env-up`. (4) The bootstrap certificate is unchanged between them. |
| A backup is restored into a new cluster and the counts match | R9 | E2E | - | 5 | Story 5.7 | Boundary: two clusters, the plugin and S3, run by a person. Scenarios: (1) a backup taken on EKS restores into a new Cluster under a new name from the source's `serverName`. (2) The restored `corpus_meta` equals the source's. (3) Its issue count equals the source's and the pinned manifest's. (4) The ordered digest of issue numbers matches. (5) A recovered cluster that must archive has its own plugin entry and `ObjectStore` path. |
| The restore drill's comparison fails when the counts differ | R9 | Unit | - | 3 | Story 5.7 | Mechanism: a comparison that cannot fail makes the drill vacuous. Scenarios: (1) equal `corpus_meta` and counts exit 0. (2) A different count exits non-zero. (3) A different `corpus_meta` exits non-zero. |
| kind and CI behaviour is unchanged and kind jobs run only when they should | R7 | Unit | - | 4 | Story 5.5 | Constraint: "Must not change: kind and CI behaviour". Boundary: `.github/kind-paths.yml` evaluated against changed-file lists. Scenarios: (1) a change to `infra/**` alone starts no kind deploy. (2) A change to `deploy/charts/**` still does. (3) `scripts/kind-up.sh`, `values-kind.yaml` and `_kind-deploy.yml` are byte-identical to `main` unless a story's plan names the change. (4) `ci.yml`'s `charts` job lists every new chart test file. |
| The refactor sweep changes no behaviour | R1, R3, R7 | E2E | - | 3 | Story 5.10 | On story 5.10's PR: (1) `ci.yml` and `mcp-e2e.yml` pass and both charts render with each environment file. (2) `terraform validate` passes for both stacks. (3) A dispatched `env-up` and `env-down` still finish clean, using the one environment run budgeted for it. |
| The integrated check on EKS runs the whole sequence once and the evidence is linked | R1, R3, R4, R5, R9, R10, R11 | E2E | - | 6 | Story 5.11 | Wiring only, because lower rows hold the logic. Scenarios: (1) the agent dispatches `env-check.yml` on a SHA and it finishes green. (2) `env-up` is under 30 minutes. (3) The leftover check is clean. (4) The epic's Notes cite the run URL as the CI evidence. (5) The Notes link the restore, failure and recreate records. (6) The Notes record the billing figure for the month, by the measure C-1 settles. |

**Total P1**: 123 tests, ~49–98 hours

### P2 (Medium)

**Criteria**: Secondary behavior with narrower user reach and an acceptable workaround. Risk score
is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| Two `t4g.medium` nodes hold the platform pods and both database instances | R1 | E2E | R-006 | 4 | Story 5.2 | Mechanism: an unmeasured fit. Boundary: nodes, scheduler and pods, so E2E. Consequence: pods Pending or OOMKilled and `env-up` never Ready. Workaround: `t4g.large`, one value, $9.52 a month, documented in the epic. Scenarios: (1) every pod is Ready with no restart after a full install. (2) The plan records requests, limits and free memory per node. (3) The two CNPG instances land on different nodes. (4) The node-size fallback is one value in `infra/env` and changes nothing else. |
| Story 5.2's shared script and values run unchanged in story 5.3's workflow | R1 | E2E | R-010 | 3 | Stories 5.2, 5.3 | Mechanism: an oversized tracer whose defects surface later. Boundary: a person's hand run, then a workflow. Scenarios: (1) the plan names the independent review, or records the split. (2) Story 5.3's workflow calls `scripts/eks-deploy.sh` with no fork or copy. (3) Re-running the script against a live environment is a no-op that leaves it Ready. |
| The `env-up` summary and artifact carry usable stage times | R1 | Unit | - | 3 | Story 5.3 | Scenarios: (1) every stage has a name and a duration in seconds. (2) The artifact parses as JSON. (3) A failed stage is recorded with its duration, not dropped. |
| The failure drill's probe and recorder count correctly | R10 | Unit | - | 3 | Story 5.8 | Scenarios on a fake target: (1) a gap of N failed responses is counted as N. (2) Recovery time runs from the termination to the next success. (3) Recorded output keeps no account id or address (shared with P0 (E)). |
| The new scripts pass static checks | R1, R3, R9, R10 | Unit | - | 2 | Stories 5.2, 5.4, 5.7, 5.8 | Neither `shellcheck` nor `actionlint` appears in `.github` or `scripts` today. Scenarios: (1) `shellcheck` passes for the new `scripts/*.sh`. (2) `actionlint` passes for the new workflows. Both are proposed additions to `ci.yml`. |

**Total P2**: 15 tests, ~6–12 hours

### P3 (Low)

**Criteria**: Rare, cosmetic, or experimental behavior with minimal impact and an easy workaround.
Risk score is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| The namespace holds only Secrets the chart owns | R8 | E2E | R-011 | 2 | Story 5.6 | Mechanism: the plugin's Role can read every Secret in the namespace (issue 892). Boundary: the plugin's Role and the namespace, so E2E. Consequence: a future Secret is readable. Workaround: accepted by the story. Scenarios: (1) the plan records the Role's rules and the namespace's Secret names. (2) A Secret the chart does not own fails the check. |
| Each drill record has the sections the epic asks for | R9, R10, R11 | Unit | - | 2 | Stories 5.7, 5.8, 5.9 | Scenarios: (1) each record in `docs/drills/` keeps the commands, their output, the timings and the result under named headings. (2) A record missing the result fails. Masking is P0 row (E). |

**Total P3**: 4 tests, ~1–2 hours

Why the bands look like this:

- **P0.** Four controls that stand as constraints: a deploy role that any repo could assume (A), a destroy that reaches bootstrap (B), an exposed internal service with no auth (C), and an unpublishable leak (E) are each a security or data-integrity failure with no safe workaround after the fact. Row (D) is the user-visible Outcome check and stays P0 with no scored risk because the epic has nothing to show if the hostname does not serve.
- **P1 for all six high risks.** Each has a stated workaround or a bounded consequence. The corpus reloads from the pinned snapshot (R-001). The target annotation or a replan answers R-002. A leaked ALB is found by the leftover check and deleted by hand (R-003). The user may move the 30-minute target (R-005). R-007's workaround does not satisfy R10, but the harm is a missing drill, not a critical business impact. R-008 is a policy edit. The P0 criterion needs both critical impact and no safe workaround.
- **P1 for R-009 although its score is 4.** The sources give no recovery path for a delayed account, so a lower priority is not justified.
- **P2 for node fit and the tracer's size.** Each has a source-backed fix: a documented node size, and an independent review.
- **P3 for the accepted Secret exposure and the record's structure.** One is accepted by the story, and the other is a one-place fix.

P0 rows per story: story 5.1 has (A), (B) and (E); story 5.2 has (B), (C) and (D); story 5.3 has (A), (C) and (D); story 5.4 has (B); stories 5.7, 5.8 and 5.9 have (E). Stories 5.5, 5.6, 5.10 and 5.11 carry no P0 row.

---

## Execution Strategy

**Philosophy:** Run every offline scenario in pull requests while the suite stays under 15 minutes. Dispatch only what spends environment-hours. P0 through P3 are priority and are not execution timing; this section decides when tests run and the coverage plan above decides what they are.

- **Pull request, `ci.yml`:**
  - `checks` runs ruff, pyright, import-linter, the offline Unit rows (workflow parse, script logic against stub CLIs and recorded AWS output, smoke-check logic, the secret scan) and `python3 scripts/render_readme_table.py --check`.
  - `charts` runs both charts with both environment files under the pinned Helm, the allowlist and override tests, and the Terraform steps: `fmt -check`, `validate` and `terraform test` for both stacks. New chart test files go in its explicit list.
  - `integrated-check`, `mcp-e2e.yml` and `eval.yml` keep running unchanged on kind-relevant paths. They are this epic's regression guard for the kind path and `eval/baseline.json`.
  - No pull-request job holds AWS credentials or runs `terraform apply`.
- **Dispatched, never on a PR:** `env-up.yml`, `env-down.yml` and, from story 5.11, `env-check.yml`. Before story 5.4 a person dispatches them. From story 5.4 the agent does, at most one environment at a time and with an expiry of at most 4 hours.
- **Scheduled:** the hourly `env-down` sweep is a product behaviour, observed once in story 5.4 after merge (C-2). It is not a test schedule.
- **Manual, hitl:** stories 5.1, 5.2, 5.3, 5.6, 5.7 and 5.8 are run by a person. Each records its commands, stage times and findings in its plan.
- **Nightly:** none planned. Each live run costs money, and a nightly environment would use the month's budget in two nights.
- **Weekly:** none planned, for the same reason.

Do not re-list the individual tests here. They are already in the coverage plan.

---

## Resource Estimates

### Test Development Effort

| Priority | Count | Hours/Test | Total Hours | Notes |
| -------- | ----- | ---------- | ----------- | ----- |
| P0 | 25 | 0.6–1.2 | ~15–30 | Trust and bootstrap-protection tests written before the build, and the public-edge probes |
| P1 | 123 | 0.4–0.8 | ~49–98 | Offline rows are cheap against stubs and recordings. The live rows share runs, and the cost is in setup and waiting |
| P2 | 15 | 0.4–0.8 | ~6–12 | |
| P3 | 4 | 0.25–0.5 | ~1–2 | |
| **Total** | **167** | **-** | **~71–142** | **~2–4 weeks, spread across eleven stories** |

### EKS environment-hours

These are estimates from the epic's per-run cost ($0.22 to $0.32 an environment-hour). They are not measured. A run counts from `terraform apply` to the end of teardown.

| Story | Live runs | Environment-hours | Notes |
| ----- | --------- | ----------------- | ----- |
| 5.2 | 1–2 | ~2–4 | The tracer is the likeliest to be repeated |
| 5.3 | 2 | ~2–3 | The second dispatch proves the skipped build |
| 5.4 | 2 | ~2–3 | One run to tear down, and one run with a 15-minute expiry waits for the hourly sweep |
| 5.6, 5.7, 5.8 | 1 shared (C-8) | ~2–3 | Three separate environments would cost ~3–5 |
| 5.9 | 2 environments | ~2–3 | |
| 5.10 | 1 | ~1 | |
| 5.11 | 1 | ~1–1.5 | |
| Reruns after failures | - | ~3–6 | |
| **Total** | **-** | **~15–25** | At $0.22 to $0.32 that is about $3.30 to $8.00, plus the fixed monthly cost |

The epic budgets about 25 environment-hours a month. If these runs fall in one calendar month, that month sits at or over the budget before the domain and zone are added. The plan therefore asks the PO to spread stories across at least two months, and to put story 5.11, whose month carries the R5 figure, in the lighter one (C-1).

### Prerequisites

**Test Data:**

- Recorded `aws` list output for an environment while up and after teardown, masked (story 5.2).
- A planted tagged resource for the leftover check, as injected recorded output and as the dry-run mode, never a real resource the agent creates.
- The pinned snapshot's manifest issue count, read from the version pin in `values.yaml`.
- A fake page and `/mcp` server for the smoke check's failure cases.

**Tooling:**

- pytest, ruff, pyright, import-linter and the pinned Helm 4.3.1.
- Terraform at the version the spine's stack table pins, with `terraform test` and mocked providers.
- `shellcheck` and `actionlint` (proposed additions to `ci.yml`).
- `gh`, `dig`, `jq` and the `aws` CLI under the read-only profile.
- The `mcp` SDK client already used by `tests/mcp`, and `tests/waiting.eventually`.

**Environment:**

- An AWS account on the Paid plan in `us-east-1`, with the bootstrap layer applied (story 5.1).
- A GitHub environment whose branch rule admits the dispatching ref (C-2).
- EKS 1.36 on two `t4g.medium` nodes, brought up per run.
- No new Postgres container: epic 5 adds no database code.

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions)
- **P1 pass rate**: ≥95% (waivers required for failures). A live run that fails for an AWS-side reason, such as a quota or an outage, is rerun once and counts once.
- **P2/P3 pass rate**: ≥90% (informational)
- **High-risk mitigations**: 100% complete or approved waivers

### Coverage Targets

- **Critical paths**: ≥80% (`env-up` → Terraform → Helm → the page and `/mcp` over the hostname; `env-down` → leftover check; backup → restore)
- **Security scenarios**: 100% (trust policy, no stored key, exposure, backup role scope, masking)
- **Cost-control scenarios**: 100% (alarm, expiry stamp, sweep, ordered teardown, leftover check with positive control)
- **Edge cases**: ≥50%

### Non-Negotiable Requirements

- [ ] All P0 tests pass
- [ ] No high-risk (≥6) items unmitigated
- [ ] Security tests (P0 rows (A), (C), (E) and the backup role's scope) pass 100%
- [ ] The 30-minute target is met by a recorded run, or the user has recorded a Decision to move it
- [ ] Planned NFR evidence exists or `nfr-assess` has documented CONCERNS/waivers

---

## Mitigation Plans

### R-001: Archive reuse across incarnations (Score: 6)

**Mitigation Strategy:**

1. `env-up` generates the incarnation id from the run id and attempt, never from the cluster name or SHA.
2. `env-up` refuses an id whose prefix already exists in the bucket, before `terraform apply`.
3. One value feeds the Cluster's plugin entry, the `ObjectStore` path and the recovery `externalClusters`.
4. `skipEmptyWalArchiveCheck` is never set, and a test fails if it appears.

**Owner:** Dillon (stories 5.6 and 5.9)
**Timeline:** wiring in story 5.6; recreate proof in story 5.9
**Status:** Planned
**Verification:** the R-001 row passes, including the first incarnation's objects unchanged.
**Residual risk:** story 5.9's note says the plugin issue behind the failure is unreproduced on current versions, so the plan cannot say whether the `serverName` change is what prevents it. If the first recreate passes, a run without the change on a spare incarnation would answer that, at the cost of an environment-hour.

### R-002: The Gateway, certificate and DNS chain is unproven (Score: 6)

**Mitigation Strategy:**

1. Story 5.2 runs the chain by hand first, so the unproven part fails in the tracer.
2. The explicit certificate ARN is in a `LoadBalancerConfiguration`, and the render test checks it.
3. If external-dns does not read the address, the target annotation is the fallback. If neither works, the story stops for a replan, with no second ALB and no Ingress (AD-14).

**Owner:** Dillon (story 5.2)
**Timeline:** first `env-up`
**Status:** Planned
**Verification:** the R-002 row passes and the plan records the certificate mode and whether the annotation was needed.
**Residual risk:** one environment shows one controller version's behaviour. A later chart or controller upgrade can change it, and only the next `env-up` would see it.

### R-003: Teardown leaves AWS resources behind (Score: 6)

**Mitigation Strategy:**

1. The Gateway is deleted and its ALB confirmed gone while the controller still runs, then `platform` is uninstalled (AD-24 as amended).
2. The leftover check includes a positive control, so a clean result means the resources were seen and are gone.
3. A stuck Gateway is reported with its finalizer and the remedy, and the job fails without force-deleting.
4. The controller's `manage-backend-security-group-rules` stays at its default.

**Owner:** Dillon (stories 5.2 and 5.4)
**Timeline:** hand teardown in 5.2; workflow in 5.4
**Status:** Planned
**Verification:** the R-003 row passes, including the positive control and the independent controller-tag oracle.
**Residual risk:** resources the controller creates but tags under a key the oracle does not know remain invisible to both checks. Cost Explorer's month-to-date figure is the last backstop (R-004).

### R-005: The 30-minute target is unmeasured (Score: 6)

**Mitigation Strategy:**

1. Story 5.2 times each stage by hand, so the budget is seen before any workflow exists.
2. Story 5.3 records stage times, including `dns_visible` against the zone's name servers.
3. A run at or over 30 minutes is recorded as a Decision with the stage times and a proposed fix before the target changes.
4. The pinned embeddings mean `env-up` never embeds, so the corpus load is the one data stage.

**Owner:** Dillon (stories 5.2 and 5.3)
**Timeline:** stage times in 5.2; recorded run in 5.3
**Status:** Planned
**Verification:** the R-005 row passes, with GitHub's step timestamps agreeing with the recorded total.
**Residual risk:** one recorded run is one sample. AWS provisioning times vary, so a later run can exceed 30 minutes. Story 5.11's run is a second sample.

### R-007: Failover with two instances hits the plugin's open bug (Score: 6)

**Mitigation Strategy:**

1. Story 5.8 runs the two-instance case and does not fall back to one instance.
2. The plugin is pinned to 0.16.0 or later.
3. If the bug bites, the record keeps exactly what failed, and the story proposes the fix or the limit for the user to decide.

**Owner:** Dillon (story 5.8)
**Timeline:** drill in 5.8, before 5.9
**Status:** Planned
**Verification:** the R-007 row passes, with archiving still healthy after promotion.
**Residual risk:** if #828 bites and no fix exists, R10 cannot be met as written. That is a replan, which the epic Notes already name as a finding to resolve.

### R-008: The backup role's policy is inferred and untested (Score: 6)

**Mitigation Strategy:**

1. Start from the candidate action set, with a prefix condition on the backup prefix and no access to the state prefix.
2. Exercise backup, WAL archive, restore read and retention delete under it, and tighten against failures.
3. Record the exact set that was needed.
4. Check the effective permissions with IAM policy simulation, not by reading the policy text.

**Owner:** Dillon (story 5.6)
**Timeline:** before stories 5.7 and 5.9 rely on it
**Status:** Planned
**Verification:** the R-008 row passes.
**Residual risk:** a future plugin version can need an action this version did not. The record names the version it was tested on.

---

## Assumptions and Dependencies

### Assumptions

1. The C-1 to C-8 decisions reach the stories before each one builds.
2. The AWS account runs on the Paid plan, with `us-east-1` as its region (epic Constraints).
3. EKS 1.36 is available on standard support in `us-east-1` for the build window. The spine pins it, and no source confirms the date (UNKNOWN).
4. GitHub-hosted runners can reach the cluster's API endpoint, and the read-only profile can read what these tests need, including Cost Explorer and IAM policy simulation (UNVERIFIED; story 5.1 checks them).
5. The expiry sweep's schedule runs from `main`, and the repository stays active enough that GitHub does not disable it (C-3).

### Dependencies

1. Branch `epic-5-refine` merges to `main`, so the epic and stories are there before story 5.1 starts.
2. A person creates the AWS account now, so activation does not gate story 5.1 (R-009).
3. A person buys the domain and applies `infra/bootstrap` once (story 5.1).
4. Stories 1.11, 3.8 and 4.7 are done before stories 5.2 and 5.3.
5. The PO writes the C-1 to C-8 decisions into the stories.
6. The red-mode sessions run before stories 5.1 and 5.4 build.

### Risks to Plan

- **Risk**: `terraform test` with a mocked provider cannot plan the EKS module, because the module reads many values that are unknown without credentials.
  - **Impact**: the plan-level scenarios in the Terraform row cannot run offline, leaving only `fmt` and `validate`.
  - **Contingency**: assert the tag, NAT, KMS and logging rules on the module inputs in `infra/env` instead of on a plan. Story 5.5's description allows "a mocked provider or a plan-only mode, whichever the plan finds works".
- **Risk**: the live runs exhaust the month's environment-hour budget (R-004).
  - **Impact**: R5's figure fails for the month, and the epic's recorded evidence is in a bad month.
  - **Contingency**: spread the stories over two months, share one environment across stories 5.6 to 5.8, and record the figure for the lighter month.
- **Risk**: the hourly sweep is delayed or disabled (C-3).
  - **Impact**: a forgotten environment lives past its expiry.
  - **Contingency**: the $8 alarm, and a rule that the agent checks the account for a running environment at the end of every session.

---

## Proposed Story Updates

These changes are for the PO to apply. This plan does not edit `tickets.toml` or the epic.

| Story | Proposed change | Why |
| ----- | --------------- | --- |
| 5.1 | Add to `verify`: "`.gitignore` covers Terraform state, plan files, `.terraform/` and `*.tfvars`, and a scan of tracked files finds no account id, key pattern or email (R6); the deploy role's trust and the backup prefix's scope are asserted by tests on the rendered policy, written before the build (R6); the read-only profile can run IAM policy simulation and read Cost Explorer (R5, R6)." Add to Description: the account is active before the story starts. | P0 (A), P0 (E), R-009, assumption 4 |
| 5.2 | Add to `verify`: "the controller's default-tag and the EBS CSI extra-volume-tag settings are set, and the leftover check's list finds the ALB, a target group, the security group and the volumes while the environment is up (R3); real `aws` list output for the environment, up and after teardown, is captured with ids masked and committed as fixtures for story 5.4 (R3); the plan records requests, limits and node memory headroom (R7)." | C-6, R-003, R-006 |
| 5.3 | Add to `verify`: "the smoke check compares the issue count with the pinned snapshot's manifest count (R1); `dns_visible` is measured against the zone's name servers before the public resolver (R1); the plan states whether the live run is from the branch, a named environment or after merge (R1, R6)." | C-7, R-005, C-2 |
| 5.4 | Add to `verify`: "the check, run while the environment is up, lists the Gateway's ALB, a target group, the security group and the PVC volumes (R3); IAM policy simulation of the deploy role against bootstrap ARNs is denied, and `terraform plan -lock=false` of bootstrap shows no change after `env-down` (R3); the scheduled expiry is observed after merge, with the time past expiry recorded against the bound C-3 settles (R4)." Add to Notes: the red-mode tests for the bootstrap protection exist before the build. | P0 (B), R-003, C-2, C-3 |
| 5.5 | Add to `verify`: "the allowlist names the keys C-4 lists, and an added key outside it fails (R7); the EKS render has no kind stand-in hostname and `mcp`'s allowed hosts hold the live hostname and no wildcard (R7)." | C-4 |
| 5.6 | Add to `verify`: "IAM policy simulation of the backup role is denied on the Terraform state prefix (R6); the namespace's Secret names and the plugin Role's rules are recorded (R8)." | R-008, R-011 |
| 5.7 | Add to `verify`: "the ordered digest of issue numbers matches between source and restored cluster, and the counts equal the pinned manifest's (R9)." | Independent Oracles |
| 5.8 | Add to `verify`: "after promotion the Cluster's archive status shows no error and archiving continues under one `serverName` (R10)." Add to Notes: run in the same environment window as stories 5.6 and 5.7, the node loss last. | R-007, C-8 |
| 5.9 | Add to `verify`: "the first incarnation's archive objects are unchanged by the second environment (R11)." | R-001 |
| 5.11 | Add to `verify`: "the Notes record the billing figure by the measure the PO chose in C-1, and the figure under the other measure." Add to Notes: schedule the story in the lighter of the epic's calendar months. | C-1, R-004 |

---

## Follow-on Workflows (Manual)

- Run `/bmad-tea-automate` in red mode to commit the trust-policy tests (P0 (A)) before story 5.1's build, and the bootstrap-protection and leftover-check tests (P0 (B)) before story 5.4's build. The build sessions do not author their own oracles (separate workflow; not auto-run).
- Run `/bmad-tea-automate` for broader coverage once implementation exists.
- Run `/bmad-tea-nfr` after story 5.3 (the 30-minute figure) and after story 5.11 (the cost figures).
- Run `/bmad-tea-trace` at epic closure, linking the `env-check.yml` run URL and the drill records. `ci.yml`'s `evidence` job reads only its own run's reports, so the live runs are cited by URL, as epic 4's plan did for `mcp-e2e.yml`.

---

## Approval

**Test Design Approved By:**

- [ ] Product Manager: Dillon Date: ____
- [ ] Tech Lead: Dillon Date: ____
- [ ] QA Lead: Dillon Date: ____

**Comments:**

---

## Interworking & Regression

| Service/Component | Impact | Regression Scope |
| ----------------- | ------ | ---------------- |
| **Epic 1 `platform` and `ticketscope` charts, `kind-up.sh`, `_kind-deploy.yml`** | Story 5.2 adds EKS-only dependencies and templates to `platform`, and `values-eks.yaml` to both charts | The kind render in both charts, `tests/smoke/test_gateway.py`, `ci.yml` `integrated-check`, and the byte-identical check on `kind-up.sh` and `values-kind.yaml` |
| **Epic 1 `.github/kind-paths.yml`** | Story 5.5 changes which paths start kind jobs | The path-filter row, and `mcp-e2e.yml` and `eval.yml` on a PR that touches `deploy/charts/**` |
| **Epic 3 chart defaults, `api` resources and embedding assets** | They size the nodes and the corpus load time | The allowlist test fails on any override of them, and R-005 and R-006's rows record the measured figures |
| **Epic 4 `mcp` Deployment, route and `allowed_hosts`** | The live hostname must be in `mcp`'s allowed hosts and route | P0 row (D) and the chart row's scenario (6); `tests/mcp` on kind |
| **Epic 6 OAuth** | Edits `values-eks.yaml` after this epic and runs on this hostname | The allowlist admits auth keys; P0 row (C)'s list of exposed paths |
| **Epic 7 dashboard and Prometheus** | Adds pods to the two nodes and to the `platform` release | R-006's recorded headroom; the chart render rows |
| **Epic 8 reviewer package** | Links the live URL and the three drill records | The drill record rows and the masking scan |
| **`README.md` results table and `eval/baseline.json`** | Untouched by this epic | `python3 scripts/render_readme_table.py --check` and `eval.yml` on every story's PR |

---

## Appendix

### Knowledge Base References

- `risk-governance.md` - Risk classification framework
- `probability-impact.md` - Risk scoring methodology
- `test-levels-framework.md` - Test level selection
- `test-priorities-matrix.md` - P0-P3 prioritization
- `nfr-criteria.md` - NFR categories and evidence

### Related Documents

- Initiative: `_bmad-output/initiative-ticketscope/initiative-ticketscope.md` (R3, R10, R11)
- Epic: `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/epic-eks-environment.md`
- Stories: `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/tickets.toml`
- Architecture: `_bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md`
- Prior test design: `_bmad-output/test-artifacts/test-design/test-design-epic-4.md`

---

**Generated by**: BMad TEA Agent - Test Architect Module
**Workflow**: `bmad-tea-test-design`
**Version**: 4.0 (BMad v6)
