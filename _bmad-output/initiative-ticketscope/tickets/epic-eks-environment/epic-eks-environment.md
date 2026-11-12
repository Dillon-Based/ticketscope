---
type: epic
title: "terraform apply brings up the live URL on EKS in under 30 minutes"
parent: initiative-ticketscope
covers: [R3, R10, R11]
sources: []
companions: []
after: []
refined: true
risk: high
---

# terraform apply brings up the live URL on EKS in under 30 minutes

## Description

- **Bootstrap layer (persistent).** It holds the DNS zone and fixed hostname, the certificate, the OIDC deploy role, the state and backup bucket, ECR and a budget alarm.
- **Environment (ephemeral).** Terraform provisions short-lived EKS from the bootstrap layer, and GitHub Actions deploys epic 1's releases and images there through OIDC, with no stored keys.
- **Live in 30 minutes.** The page and epic 4's MCP endpoint are live in under 30 minutes, including loading the corpus.
- **Teardown and cost.** An ordered teardown leaves only the bootstrap layer billing. An expiry destroys forgotten environments, and hosting costs under $10/month.
- **Backups and drills.** CloudNativePG backups go to S3, and a restore drill and a failure drill are recorded.

Epic 6's OAuth flow and epic 8's live link run on this URL, and epic 7's dashboard runs in this environment.

## Outcome

ticketscope is rebuilt for each demo from a near-free bootstrap layer and torn down after, cheaply and with no stored keys (initiative R10, R11; brief Success Criteria 3).

## Requirements

- R1 (parent R10): From the bootstrap layer, `env-up` brings the search page and the MCP endpoint live on the fixed HTTPS hostname, with the corpus loaded, in under 30 minutes. The clock runs from the start of `terraform apply` until the page and `/mcp` answer over HTTPS, and `env-up` records the time of each stage. It is met when a recorded run finishes under 30 minutes and its smoke check gets a search result from the page and from an MCP client call, both over the public hostname.
- R2 (parent R10): The hostname and its certificate stay the same across environment lifetimes. It is met when two consecutive `env-up` runs, with an `env-down` between them, serve the same hostname under the same bootstrap certificate.
- R3 (parent R10): Destroying the environment leaves only the bootstrap layer. It is met when `env-down`'s tag-scoped check finds no load balancer, ENI, volume, KMS key or log group outside Terraform state after a recorded run, and the check fails the job when a tagged leftover is planted.
- R4 (parent R10): A forgotten environment destroys itself. It is met when an environment stamped with a short expiry is torn down by the scheduled `env-down` with no person dispatching it.
- R5 (parent R10): Hosting costs under $10 for a month, the bootstrap layer and the domain included, and an alarm warns before that. It is met when the billing figure for a month that holds recorded runs is under $10 and the $8 budget alarm exists in Terraform.
- R6 (parent R11): GitHub Actions deploys to EKS through OIDC, and no cloud key is stored in the repo or its secrets. CloudNativePG backups use an IRSA role. It is met when `env-up` and `env-down` run with no AWS credential among the repo's secrets and variables, and the deploy role trusts only this repo.
- R7 (parent R11): The same `platform` and `ticketscope` charts install on EKS and on kind, and `values-eks.yaml` holds environment facts only. It is met when a PR check renders both environments' values, and an environment file that overrides a product default fails the check.
- R8 (parent R3): CloudNativePG backs up through the Barman Cloud Plugin to the bootstrap S3 bucket. It is met when a backup completes on EKS and its objects are in that bucket.
- R9 (parent R3): A backup restore is recorded. It is met when a backup taken on EKS is restored into a new cluster and the restored `corpus_meta` and issue count match the source, with the commands and their output kept in the repo.
- R10 (parent R3): An instance failure is survived and recorded. It is met when the node holding the primary is lost, a standby is promoted, and search keeps answering through the public hostname, with the recovery time and the commands kept in the repo.
- R11 (parent R3): A recreated environment backs up to and restores from the same bucket. It is met when two consecutive environments with the same cluster name, the second created after the first is destroyed, each archive WAL to the bootstrap bucket under their own `serverName`, and the second restores from the first's backup with no "Expected empty archive" failure.

## Constraints

- **Split:** `bootstrap` is persistent and applied once by the author locally. `env` is ephemeral. Terraform owns only AWS resources, and every Helm release is installed by the workflow, never by `helm_release` (spine AD-15, AD-23).
- **`env` stack:** a VPC with public subnets and no NAT, EKS and its node group, vpc-cni and ebs-csi, and IRSA roles for the LB controller, external-dns and CNPG backup. No customer-managed KMS key, and EKS control-plane logging off (AD-23).
- **Kubernetes:** EKS and the kind node image are both 1.36, on standard support. No Auto Mode and no Fargate (AD-16).
- **Images:** multi-arch, SHA-tagged, pulled from bootstrap ECR, which keeps the last 10. Nodes are Graviton, so the arm64 image has to run (AD-16).
- **Exposure:** the one `Gateway` on the AWS Load Balancer Controller, the bootstrap ACM certificate, and external-dns writing the record into the bootstrap zone. Grafana, Tempo and SeaweedFS are never public (AD-13, AD-14).
- **Gateway chain (research, 2026-11-12):** the workflow installs the standard-channel Gateway API CRDs and the controller's own CRDs itself, because the controller's Helm chart does not. The certificate is an explicit ARN in a `LoadBalancerConfiguration`, since listener `certificateRefs` are unsupported. The Gateway sets `scheme: internet-facing`, and target type is `ip` through `TargetGroupConfiguration`. L4 and L7 routes are never mixed on the Gateway. `external-dns.kubernetes.io/target` on the Gateway is the fallback if the ALB's address is not read from its status, and `--policy=sync` is dry-run first on external-dns 0.24.
- **Install order:** `platform`, then the `ticketscope` release, `migrate`, `load`, then `api` and `mcp` Ready. `load` is idempotent against `corpus_meta`. `env-up` never computes embeddings and takes the pinned asset (AD-21, AD-22).
- **Values:** environment facts only in `values-eks.yaml`: hostname, gateway class, storage class, backup endpoint, auth on or off and issuer, and replica counts. Product defaults and the snapshot pin stay in `values.yaml` (AD-25).
- **Teardown:** the ordered steps of AD-24, with the Gateway deleted and its ALB confirmed gone before the controller is uninstalled, because a controller removed first leaves the Gateway stuck and its AWS resources behind. Expiry is stamped by `env-up` (4 hours by default) and a scheduled `env-down` sweeps expired environments. About 25 env-hours a month is the budget, and one forgotten day breaks it at every node size.
- **Backups:** `instances: 2` in every environment, backing up through the Barman Cloud Plugin (v0.16.0 or later) to the bootstrap bucket, with an IRSA role created in the `env` stack (AD-18). Each incarnation archives under its own `serverName`, set as a plugin parameter on the Cluster, and restores from the previous incarnation's `serverName`. `spec.serviceAccountName` is left unset.
- **Account:** the AWS account is on the Paid plan, because the Free plan closes the account after 6 months or when credits run out and would take the bootstrap layer with it. Sign-up uses the advanced path, so the account's region is not pinned to the contact country's.
- **Region and domain:** `us-east-1`. The domain is bought and registered in Route53 in the same account, so the zone needs no outside delegation.
- **No stored keys:** deploys use GitHub Actions OIDC and backups use IRSA. The author's own admin identity runs the one-time `bootstrap` apply and is not stored in the repo or its secrets (initiative Constraints).
- **Wording:** "a personal project, deployed and operated on Kubernetes", never "production" (initiative Constraints).

## Done when

- From the bootstrap layer, env-up brings up the page and MCP endpoint on the fixed HTTPS hostname in under 30 minutes, with the corpus loaded. env-up runs Terraform apply plus the Helm deploy and records its wall-clock time and the time of each stage (R1, R2).
- env-down runs the spine's ordered teardown. A tag-scoped check then finds nothing but the bootstrap layer: no load balancers, ENIs, volumes, KMS keys or log groups left outside Terraform state. A forgotten environment expires on its own (R3, R4).
- The deploy authenticates through GitHub OIDC, with no cloud keys stored in the repo or in secrets. Backups use an IRSA role. The same charts install on kind and EKS (R6, R7).
- CloudNativePG backs up to S3, a restore drill and an instance-failure drill are each recorded, and a recreated environment backs up to and restores from the same bucket (R8, R9, R10, R11).
- A budget alarm and an environment expiry are in place, and the month's hosting cost, bootstrap layer and domain included, is under $10 (R4, R5).
- Delivered on the cluster, with an integrated check passing in CI: a cheap check on every PR (the charts render with `values-eks.yaml`, Terraform validates), and a dispatched `env-up`, smoke check, `env-down` and leftover check that ends clean.

## Boundaries

- Out: always-on hosting, autoscaling experiments, EKS Auto Mode and Fargate (initiative Boundaries; spine AD-16).
- Terraform owns only AWS resources; every in-cluster release is installed by the workflow with Helm.
- In the chart, this epic owns `values-eks.yaml`. Retrieval defaults and `api` resources belong to epic-hybrid-retrieval, the `mcp` keys to epic-mcp-server, and auth keys to epic-mcp-oauth, which edits `values-eks.yaml` after this epic.
- Prometheus and the dashboard are epic-grafana-dashboard's. This epic provides the live environment and its values file.
- Out: recording the demo and the README's live link (epic-reviewer-package).
- Out: a second environment, or a staging copy of the live one.
- Touch point: AWS account, S3, ECR and DNS — consumed and configured by Terraform; owner: epic-eks-environment
- Touch point: a registered domain, bought in Route53 — the fixed hostname's zone; owner: epic-eks-environment
- Touch point: the GitHub repo's Actions settings — the deploy role's trust and the dispatch and schedule triggers; owner: epic-eks-environment
- Must not change: kind and CI behaviour. `scripts/kind-up.sh`, `values-kind.yaml` and the `_kind-deploy.yml` workflow keep working as they do.

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R3, R10, R11)
- architecture spine — _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md, AD-1–AD-3, AD-6, AD-7, AD-9, AD-13–AD-18, AD-21–AD-25, and Open questions (AWS account plan and credits)

## Notes

- Waits on epic-search-baseline because: it needs the Helm releases and images that CI already deploys to kind.
- Waits on epic-hybrid-retrieval because: the embedding model's resource needs and precomputed embeddings size the nodes and the corpus load time.
- Waits on epic-mcp-server because: the live URL must serve the MCP server.
- Decision: Adopted the architecture spine. A persistent bootstrap layer and an ephemeral environment replace "from nothing", and the title now says what is timed (user, 2026-11-05).
- Decision: Refined with Sofia's picks (user, "take your picks", 2026-11-12). The 30-minute clock runs from the start of `terraform apply` to the page and `/mcp` answering over HTTPS, and CI pushes the SHA-tagged images beforehand, so building multi-arch images is outside the timed window. `env-up` records the time of each stage, so the tracer shows early whether the target is reachable.
- Decision: The integrated check is a cheap check on every PR (charts rendered with `values-eks.yaml`, Terraform validation) plus a dispatched `env-up`, smoke check, `env-down` and leftover check, because CI cannot afford an EKS environment per PR (user, 2026-11-12).
- Decision: Region is `us-east-1`. Node sizing is left to the stories: the smallest Graviton on-demand type that fits `api` at 512Mi, two CNPG instances on separate nodes so the failure drill is a real node loss, and the `platform` pods, from epic 3's measured chart defaults (user, 2026-11-12).
- Decision: The author owns no domain, so this epic buys one and registers it in Route53 in the same account. A zone delegated from a domain held elsewhere was declined, because the domain would then be a second place to configure (user, 2026-11-12).
- Assumption: There is no AWS account yet (user, 2026-11-12). Creating it, locking down the root user with MFA, and making an admin identity for the one-time `bootstrap` apply are hitl setup on the first story. The account should be created now, in parallel with epic 4, so its verification and any quota requests never gate this epic. The deadline is 2026-12-31.
- Decision: Applied the feasibility research (user, "go ahead", 2026-11-12; research-eks-environment-for-ticketscope). Verdict was build it with changes: no assumption was overturned and none held as written. Nothing in it was tested live on AWS, and 15 of its 31 claims are unverified, so each change below is a thing the tracer or a story proves.
- Decision: Pod Identity was considered for backups and declined for now. The spine already creates the backup role in the `env` stack, so each cluster's own OIDC trust is rebuilt with it and the research's reason for Pod Identity does not apply. IRSA is the officially documented path, while Pod Identity is confirmed only by a closed plugin issue. It stays the fallback if IRSA fails on the first recreate.
- Decision: The AWS account runs on the Paid plan from the start, and the domain is paid by card, since credits cannot pay a registration fee (research, 2026-11-12).
- Decision: Nodes start at 2x `t4g.medium` ($7.84 a month with a `.com`, 25 env-hours). `t4g.large` ($9.52) is the fallback if the `platform` pods and two database instances do not fit in 8 GiB. `m7g.large` ($10.24) does not fit the budget. A `.click` suffix ($3 a year) is the cost lever if a `.com` ($16) is too much (research, 2026-11-12).
- Source conflict: spine AD-24 step 3 uninstalls the `platform` release, which holds both the Gateway and the AWS Load Balancer Controller (AD-13), before the wait for the ALB to disappear. The research reads the controller as removing the Gateway's finalizer only after it deletes the ALB, target groups and security group, so a controller removed first leaves the Gateway stuck and the AWS resources behind (source reading, not tested). The Gateway has to be deleted, and its ALB confirmed gone, before `platform` is uninstalled. AD-24 is amended to say so.
- Source conflict: spine AD-14 says the ALB picks up the ACM certificate by hostname. The controller does that only as discovery, when no explicit certificate exists, and listener `certificateRefs` are unsupported. This epic uses an explicit ARN in a `LoadBalancerConfiguration`. AD-14 is amended.
- Source conflict: spine AD-13 lists the Gateway API CRDs under `platform`. The controller's Helm chart does not install its own CRDs or the Gateway API ones, so the workflow installs both before `platform`.
- Source conflict: spine Stack table says Barman Cloud Plugin 0.15 and Terraform 1.17. The research finds v0.16.0 (2026-11-09) current, and its fix for the plugin binding its Role to the Cluster's service account name is in 0.16.0.
- Unknown: whether failover with two instances archiving to one archive hits the plugin's open bug #828, which the research reads as likely avoided only by a one-instance demo. R10's failure drill runs the two-instance case, so the drill story finds out. A one-instance drill would not satisfy R10 (initiative R3 asks for a survived instance failure).
- Unknown: the exact minimum S3 IAM policy for backup, WAL archive, restore and retention. No document publishes one, and the candidate set in the research is inferred and untested. The backup story tests backup, restore and retention against it before it is trusted.
- Assumption: The month's cost is tight, not comfortable: $7.84 with 2x `t4g.medium` torn down correctly, about $13.20 after one forgotten day. Teardown discipline matters more than node size, so the expiry and the scheduled sweep carry the budget. Data transfer is assumed at a few cents and unpriced from a source, and orphaned volumes or ALBs from a bad teardown are not in the estimate.
- Open question: Do the $100 sign-up credits cover EKS, EC2 and ELB? No AWS page excludes them and none lists eligible services, and domain registration is explicitly excluded. Owner: this epic. They cushion the first months and are not part of the plan, so the answer does not gate the build.
- Open question: Does external-dns write the Route53 alias from an ALB-backed Gateway end to end? No primary source shows it working or failing, and it is unknown whether the controller sets the address type external-dns expects. The tracer runs it, with the target annotation as the fallback. If neither works, that is a replan.
- Open question: Does a new account's activation delay land inside the schedule? AWS says up to 24 hours, with community reports of 5 to 9 days that blocked domain purchase. Create the account now (deadline 2026-12-31).
