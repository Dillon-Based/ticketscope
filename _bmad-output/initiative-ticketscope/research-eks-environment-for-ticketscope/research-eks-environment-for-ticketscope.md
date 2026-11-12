---
title: 'technical research: EKS environment feasibility for ticketscope'
type: 'technical'
topic: 'EKS environment feasibility for ticketscope'
decision: 'Build epic 5 (EKS demo environment) as designed, or cut it'
source: 'native run from brief.md; digests/ hold the evidence'
status: complete
preset: 'standard (4 subagents, 2 rounds), validation high'
validation: 'high'
claims_verified: 13
claims_unverified: 15
claims_disputed: 3
created: '2026-11-12'
updated: '2026-11-12'
---

# Technical research: EKS environment feasibility for ticketscope

**Decision this research serves:** build epic 5 (the EKS demo environment) as designed, or cut it.

All claims were retrieved 2026-11-12 and trace to a digest file in `digests/`. Nothing here was tested live on AWS: controller behaviour comes from reading docs and source, and several fetches were summarised by a small model (flagged where it matters). Project context shaped the questions only; it is not evidence.

## Executive summary

**Build it, with five design changes. No assumption is overturned outright, and none holds as written.**

| Assumption | Verdict | Single most important reason |
| --- | --- | --- |
| Gateway API on the AWS LB Controller gives the routing and TLS needed | **Holds with changes** | GA, one Gateway gives one ALB with path routing [27][21]; but external-dns writing the alias record from an ALB-backed Gateway is not proven end to end [24][25], and the Helm chart does not install the Gateway API CRDs [21]. |
| A brand-new AWS account can run EKS | **Holds with changes** | AWS docs list EKS, EC2, ELB, Route 53 as usable on the Free plan [12], but the Free plan closes the account after 6 months or when credits run out [10][13], and credits cannot pay for domain registration [15]. Treat the account as Paid (or upgrade early). |
| Cost fits $10 a month at about 25 env-hours | **Holds with changes** | 2x t4g.medium totals about $7.84 a month including persistent costs; 2x t4g.large about $9.52; m7g.large does not fit (about $10.24) [1][3][4][5][6]. One forgotten day breaks the budget at every size. |
| A recreated environment can back up to and restore from the same bucket through IRSA | **Holds with changes** | A same-name cluster on the same bucket path fails with "Expected empty archive" unless each incarnation archives under a new `serverName` [30][31]. Pod Identity fits a recreate-every-time cluster better than IRSA [35]. |

The five changes, in order of cost-if-found-late:
1. **Give every environment incarnation its own `serverName`** (or prefix) for WAL archiving, and restore from the previous incarnation's `serverName` [30][31]. Otherwise the second create likely fails: the docs describe the check [30], but the same-name case rests on one open issue reported on CNPG 1.26 and plugin 0.11.0, not reproduced on current versions [31] (medium-high).
2. **Run the AWS account on the Paid plan** (upgrade is immediate once a payment method is added, credits carry over, but it cannot be reversed) [13]. A Free-plan bootstrap layer disappears at 6 months [10].
3. **Test the Gateway, ACM and external-dns chain early.** Use an explicit ACM ARN in `LoadBalancerConfiguration` [22][23]; set `scheme: internet-facing` and target type `ip`; install the CRDs yourself [21]; keep `external-dns.kubernetes.io/target` as the fallback [25].
4. **Use Pod Identity, not IRSA,** for the database service account: the role trust policy is static, so the persistent bootstrap layer can own the role [35].
5. **Budget for teardown discipline, not for node size.** Each environment-hour costs $0.22 to $0.32 [1]; the budget is gone at about 34.6 hours with t4g.medium.

Biggest caveat: external-dns plus an ALB-backed Gateway has no end-to-end source in any primary document I found, and the minimum S3 IAM policy is my own inference from AWS and Barman documentation, not a published set.

## Q1: Gateway API on the AWS Load Balancer Controller

**Versions.** Controller v3.6.2 (25 Oct 2026) and external-dns v0.24.0 (23 Oct 2026) match the author's table [19][20]. EKS 1.36 is not named in the controller's own matrix, which says only "Kubernetes 1.22 or newer" [21]; the only recent-EKS evidence is an issue reporter on 1.33 [26]. Treat 1.36 compatibility as expected but unstated (medium).

**GA and install.** AWS announced GA of Gateway API support (L4 to NLB, L7 to ALB) on 2026-03-06 [27]. The L7 docs add that the ALB implementation does not fully implement the Gateway API core, and ListenerSets are experimental [21]. Needs standard-channel Gateway API CRDs v1.6.0 plus the controller's own CRDs (`TargetGroupConfiguration`, `LoadBalancerConfiguration`, `ListenerRuleConfiguration`); the Helm chart does not install them (request #4651 open) [21]. The controller enables itself when the CRDs are present, and `--feature-gates=ALBGatewayAPI=false` disables it [21]. Mixing L4 and L7 routes on one Gateway is unsupported [21].

**One Gateway, one ALB, path routing.** Each Gateway of the ALB class provisions one ALB; HTTPRoute path, header, query and method matches, hostnames, parentRefs and backendRefs are supported [21]. Two HTTPRoutes to two Services on one Gateway is the standard pattern but is not explicitly evidenced beyond cross-namespace routes in the AWS blog [27] (medium). The docs never name `Exact` versus `PathPrefix`; they show only `PathPrefix` examples, and I could not confirm `Exact` from source (unverified). Unsupported: `ResponseHeaderModifier`, `RequestMirror`, CORS, timeouts, retries, session persistence; `RequestHeaderModifier` is partial [21]. If one rule in an HTTPRoute is invalid, later rules for that route are not created [21].

**TLS.** Listener `certificateRefs` are not supported; use `LoadBalancerConfiguration` (`defaultCertificate` or `certificates`) [21][22]. The source shows explicit ARNs are used first; hostname-based ACM discovery (listener hostname plus attached-route hostnames) runs only if no explicit certificate exists, and the two are never merged [23]. An HTTPS listener with no hostname at all is a build error; discovery that finds nothing leaves an HTTPS listener with no certificate and no error [23] (code reading, not tested; medium). This resolves an apparent conflict between the AWS blog and the docs pages: both are right [27][21][23]. A red-team pass found the conflict still visible on the docs pages [21][22]; the source reading is the stronger evidence. The default `scheme` is `internal`, so set `internet-facing` explicitly [22]. The listener-hostname versus route-hostname mismatch behaviour was not evidenced.

**external-dns.** The `gateway-httproute` source takes targets from the parent Gateway's `status.addresses` (types IP, Hostname or unset), overridden by an `external-dns.kubernetes.io/target` annotation on the Gateway; the route must be Accepted [25]. The controller writes the lowercased ALB DNS name into `status.addresses` [24], but the address `type` it sets was not seen. If unset, external-dns treats it as an IP address [25] (unverified risk). An old issue (#4245) shows external-dns needed Accepted status and a fixed RBAC; fixed in v2.13.3 [26]. external-dns 0.24 changes hostname-fallback behaviour; with `--policy=sync` previously created fallback records can be deleted, so dry-run first [20]. TXT-registry and `--policy` cleanup on Gateway deletion were not researched (open question). No primary source shows this combination working end to end, and none shows it failing (red-team, searched).

**Teardown.** The controller removes the Gateway finalizer only after deleting the load balancer, target groups and security group and releasing the backend security group [24]. If the controller is uninstalled first, the Gateway stays stuck and AWS resources remain [24] (source reading, medium-high). Order: delete routes and Gateway, wait until the ALB is gone, then uninstall the controller, then destroy the cluster. No Gateway-specific leak issue was found; #3592 was an Envoy Gateway problem [digest q1]. #4652 (backend security group leak when `manage-backend-security-group-rules=false`) is open: leave that flag at its default.

**Pod targets.** Target type defaults to instance-inferred; set `ip` explicitly via `TargetGroupConfiguration` (needs VPC CNI, which the design has) [21]. Health checks are set through `healthCheckConfig`, and a Service-level config replaces the default block wholesale [21]. Gateway readiness gates: not found in the docs.

**Open bugs.** None found that blocks a 2-node, 2-Service demo. #4855 (crash-loop at 12,000 Services) is irrelevant; #4740, #4699, #4753 are open or old and minor [digest q1].

## Q2: a brand-new AWS account

**Plans.** A new account chooses Free or Paid at sign-up and gets $100 in credits, plus up to $100 more from activities [10][11]. The Free plan's supported list includes EKS, EC2 (not Capacity Blocks), Elastic Load Balancing, Route 53, VPC, EBS, CloudWatch, Budgets and Service Quotas [12]; the AWS-managed Free-plan policy allows `eks:*`, `elasticloadbalancing:*`, `route53:*`, `route53domains:*` and denies Spot requests, EC2 Fleet and capacity purchases [41] (medium: grepped, not read line by line). Spot instances are therefore blocked on Free. Organizations and Control Tower auto-upgrade the account to Paid [10]. I found no first-hand report of running EKS on a Free-plan account, and a community thread reports a free-tier user blocked from creating a load balancer (page unreadable; cause unknown) [red-team digest].

**Free-plan end (contradicts a persistent bootstrap layer).** "After your free account plan expires, your account closes automatically", AWS retains content 90 days and then permanently deletes it; the plan ends at 6 months or when credits are used, whichever comes first [10]. Two more AWS pages agree [11][13]. The wording differs ("closes" versus "suspends"), but none says it converts to Paid. Upgrade is manual, immediate once a payment method is added, and cannot be reversed; remaining credits carry over [13]. Confidence high; none of the pages is dated.

**Credits.** Credit applicability to EKS, EC2, ELB, hosted zones and public IPv4: no AWS page excludes them and no page lists eligible services; only a community answer says they are covered (low) [11]. Domain registration is explicitly excluded: "You can't use AWS credits to pay the fee for registering a new domain" [15]. Expiry is documented inconsistently: 6 months in one FAQ answer, 12 months in another and in the terms [11]. Plan for 6.

**Domain on the Free plan.** Route 53 is allowed [12][41], but no AWS page says how a Free-plan account pays the registration fee, and upgrading is the step that adds a payment method [13]. A domain purchase probably forces the upgrade (unverified inference).

**Budgets.** Budgets is on the Free plan list [12]. Notifications are free and the first two action budgets a month are free; data refreshes about three times a day, so spend can exceed a threshold before an alert fires [18]. Credits net against budget cost by default (single AWS-hosted article, medium). Whether budget actions work on the Free plan is unconfirmed.

**Quotas.** Default Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) instances: 5 vCPUs, shared by Graviton [16]. Two 2-vCPU nodes (t4g.medium, t4g.large, m7g.large) fit at 4 vCPU; two xlarge nodes (8 vCPU) do not, and a rolling node upgrade that surges a third node (6 vCPU) would fail (derived). Elastic IPs default 5 and ALBs 50 [digest q2]. Increases: small ones usually auto-approve, large ones go to Support, no SLA and no priority [17]. I found no documented lower quota for Free-plan accounts; one community report of a 1 vCPU account is low confidence.

**Region pin (weakened by red-team).** On the new streamlined sign-up path, AWS assigns the account's Region from the contact-address country (US to us-east-2, EU to eu-north-1, Australia and Asia to ap-southeast-2) and regional resources are created there [14]. The advanced sign-up path is not restricted [14]. So a us-east-1 cost model needs the advanced sign-up; cost differences in us-east-2 were not priced.

**Verification delay.** AWS says activation takes up to 24 hours (sometimes 2 days) [digest q2]; community re:Post accounts describe stalls of 5 to 9 days that blocked Route 53 domain purchase (snippets only, pages returned 403; low).

## Q3: monthly cost against $10 (us-east-1)

Prices come from the AWS bulk price list published 2026-11-04 to 2026-11-11 [1] and, independently, from AWS pricing pages [3][4][5][6]. EC2 on-demand rates were confirmed against Vantage only, because the AWS EC2 page renders dynamically [9]. gp3 $0.08 per GB-month is from the price list only [1]. Domain prices are secondary-sourced [7][8].

**Version.** Kubernetes 1.36 reached EKS on 2026-06-02, standard support runs to 2027-08-02, and 1.37 is also available [2]. Control plane on standard support: $0.10 per cluster-hour [1][3]. Extended support adds $0.50, for $0.60 in total [3]; it does not apply to 1.36.

**Unit prices.**

| Item | Price | Unit |
| --- | --- | --- |
| EKS control plane (standard) | $0.10 | per cluster-hour [1][3] |
| t4g.medium / t4g.large / m7g.large, Linux on-demand | $0.0336 / $0.0672 / $0.0816 | per instance-hour [1][9] |
| gp3 | $0.08 | per GB-month [1] |
| ALB | $0.0225 + $0.008 | per hour + per LCU-hour [1][5] |
| Public IPv4 | $0.005 | per address-hour, in use or idle [1][4] |
| S3 Standard / ECR | $0.023 / $0.10 | per GB-month [1] |
| Route 53 hosted zone | $0.50 | per month, not prorated [6] |
| .com | $16 registration and renewal (was $15 before 2026-07-01) | per year [7] (secondary) |
| .click / .link / .net / .dev | $3 / $5 / $17 / $17 | per year [8] (single secondary source; pre-July prices unverified) |
| Spot t4g.medium / t4g.large / m7g.large | about $0.016-0.017 / $0.027-0.057 / $0.03-0.06 | per hour, approximate, aggregators disagree, low confidence [9] |

Public IPv4 count: 4 addresses (2 nodes plus 2 ALB subnets), $0.02 per hour. An ALB charges one per address, and the VPC pricing example shows a load balancer with two in-use addresses [4]; one per AZ is implied, not stated. The pricing pages list no ENI or EKS-specific public IPv4 charge for a basic cluster [3][4] (absence on the page, medium). Hybrid Nodes and Provisioned Control Plane are optional add-ons and do not apply [3].

**Arithmetic.** Fixed per environment-hour excluding nodes: 0.10 (control plane) + 0.0225 (ALB) + 0.004 (0.5 LCU) + 4 x 0.005 (IPv4) + 100 GB x 0.08 / 730 (EBS: 2 x 30 GB nodes + 2 x 20 GB DB volumes) = **$0.1575**. Environment cost = H x (0.1575 + 2 x node rate). Persistent: zone 0.50 + S3 0.09 (4 GB) + ECR 0.30 (3 GB, assumed) + domain amortised $16/12 = 1.33, for **$2.23 a month** ($1.14 with a $3 `.click`).

| Monthly line, 25 h, 2x t4g.medium | Low | Likely | High |
| --- | --- | --- | --- |
| EKS control plane (25 x 0.10) | 2.50 | 2.50 | 2.50 |
| 2 nodes (spot / t4g.medium OD / m7g.large OD) | 0.82 | 1.68 | 4.08 |
| EBS, 100 GB for 25 h | 0.27 | 0.27 | 0.27 |
| ALB hours | 0.56 | 0.56 | 0.56 |
| ALB LCU | 0.05 | 0.10 | 0.20 |
| Public IPv4 x 4 | 0.50 | 0.50 | 0.50 |
| Data transfer (assumed, not priced from a source) | 0 | 0.05 | 0.10 |
| ECR | 0.10 | 0.30 | 0.50 |
| S3 | 0.05 | 0.09 | 0.15 |
| Route 53 zone | 0.50 | 0.50 | 0.50 |
| Domain amortised (.click / .com / .net) | 0.25 | 1.33 | 1.42 |
| **Total** (sum of the lines above) | **5.60** | **7.88** | **10.78** |

| Node type, with .com | Torn down correctly (25 h) | Left running 24 h extra | One full day alone | Full month (730 h) |
| --- | --- | --- | --- | --- |
| t4g.medium | **$7.84** | about $13.2 | $5.39 | about $164 (env only) |
| t4g.large | **$9.52** | about $16.5 | $7.00 | about $213 |
| m7g.large | **$10.24** | about $18.0 | $7.70 | about $234 |

**Fits under $10?** Yes at t4g.medium ($7.84) and thinly at t4g.large ($9.52); no at m7g.large on-demand ($10.24). A forgotten day breaks the budget at every size. The budget is exhausted at about 34.6 environment-hours (t4g.medium) or 26.6 (t4g.large) [arithmetic, digest q3]. If the two database volumes persist all month rather than being deleted at teardown, add $3.20 a month.

**The two levers that move it most.** (1) Environment-hours and teardown discipline: each hour costs $0.22 to $0.32, and a 730-hour month costs roughly 16x to 23x the budget depending on node size. (2) Node size or spot: nodes are the largest variable line after the control plane's fixed $2.50. Spot is unverified on price, and the Free-plan policy denies Spot requests [41].

**Not priced.** CloudWatch Logs and KMS and Secrets Manager (assumed zero with control-plane logging off and AWS-managed keys), internet egress allowance and cross-AZ transfer, and orphaned EBS volumes or ALBs left by a bad teardown. The $100 sign-up credit, if it covers EKS, EC2 and ELB (unconfirmed, low), would cushion the first months but is not a plan.

## Q4: backups with CloudNativePG and the Barman Cloud Plugin

**Versions.** The plugin is at **v0.16.0** (2026-11-09), not 0.15 [28]. CloudNativePG is v1.30.1 (2026-09-23); v1.30.0 added Kubernetes 1.36 support [37]. The plugin's install page requires CNPG 1.30 or newer and cert-manager, with the plugin in the operator's namespace [29]. Terraform is 1.17.2 and terraform-aws-eks 21.29.0, both newer than your table [36][40]. The in-tree `barmanObjectStore` removal version is disputed: the CNPG 1.30 release notes say 1.31.0, the devel backup docs say 1.32.0 [37][39]. Either way, the plugin is the supported route.

**Authentication.** `s3Credentials.inheritFromIAMRole: true` works with both IRSA (annotation on the service account via `serviceAccountTemplate`) and Pod Identity [29][32]. IRSA is the officially documented path; Pod Identity is confirmed only by a closed issue [32], and a docs request (#876) is open [33]. Pod Identity does not use OIDC providers, and AWS states identical associations can be made in each cluster without changing the role's trust policy [35]. Recommendation (my inference from those sources): Pod Identity for a recreate-every-time cluster. The role lives in the persistent bootstrap layer; the `eks-pod-identity-agent` add-on and an `aws_eks_pod_identity_association` are created per cluster, and the association must exist before the database pods start because credentials are injected at pod creation [35].

**IRSA trust, if chosen.** The issuer URL is unique per cluster, so the trust policy must reference each new cluster's OIDC provider; terraform-aws-eks v21 creates it by default (`enable_irsa`) and exposes `oidc_provider_arn` [36]. That works within one Terraform root, but a role in a persistent stack needs its trust updated per cluster (inference).

**Exact configuration** (from the plugin docs [29], with the annotation form from a third-party post):

```yaml
apiVersion: barmancloud.cnpg.io/v1
kind: ObjectStore
spec:
  configuration:
    destinationPath: s3://BUCKET/PREFIX
    s3Credentials: {inheritFromIAMRole: true}
---
kind: Cluster
spec:
  plugins:
  - name: barman-cloud.cloudnative-pg.io
    isWALArchiver: true
    parameters: {barmanObjectName: s3-store}   # add serverName here per incarnation
  serviceAccountTemplate:                       # IRSA only; omit with Pod Identity
    metadata: {annotations: {eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT:role/ROLE}}
```

`ObjectStore.spec.configuration.serverName` must stay empty; set `serverName` as a plugin parameter on the Cluster [29]. Whether the `plugins` entry accepts `serverName` for archiving rests on the docs line and an issue thread [29][31], not on a worked example (medium). Do not set `spec.serviceAccountName`: before v0.16.0 the plugin bound its Role to a service account named after the Cluster and ignored a custom name (#1117); the fix (PR #869) is in v0.16.0 [34] (medium-high).

**Minimum IAM policy: not published.** No plugin, CNPG or Barman document gives a full S3 policy [42]. Candidate set, assembled from the AWS multipart-upload documentation [38] and Barman, **inferred and untested**: on `arn:aws:s3:::BUCKET/PREFIX/*`: `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject` (retention cleanup only), `s3:AbortMultipartUpload`, `s3:ListMultipartUploadParts`; on `arn:aws:s3:::BUCKET` with an `s3:prefix` condition: `s3:ListBucket`, `s3:ListBucketMultipartUploads`; plus `kms:GenerateDataKey` and `kms:Decrypt` if SSE-KMS [38][42]. Test backup, restore and retention before relying on it.

**Recreate and restore: the main threat.** CNPG's recovery docs describe the failure: the new primary stays in "Setting up primary" and logs "WAL archive check failed ... Expected empty archive", and advise unique `serverName`s per cluster; an annotation `cnpg.io/skipEmptyWalArchiveCheck: enabled` bypasses it but is "strongly discouraged" [30]. Plugin issue #767 (open, reopened 2026-05-20, no fix) reports the same-name restore failure because `serverName` defaults to the cluster name and the old WAL is still at that path [31]. v0.16.0's notes do not mention a fix [28]. Workarounds in the thread (community, not maintainer-confirmed): a new `serverName` per incarnation (for example a numeric suffix) with the recovery `externalClusters` entry pointing at the previous incarnation's `serverName` [31]. Restore stanza: `bootstrap.recovery.source` plus `externalClusters[].plugin` with `barmanObjectName` and `serverName`; a recovered cluster archives only if given its own `plugins` entry and, per the docs example, a separate ObjectStore [29]. Prerequisites before the Cluster is created: cert-manager, CNPG 1.30+, the plugin in the operator namespace, the ObjectStore, and the role and its credential path (annotation or Pod Identity association) [29][35]. HA failover in a single archive hits a related bug (#828, open) but a one-instance demo likely avoids it (inference) [digest q4].

**Open plugin bugs.** #892: with `inheritFromIAMRole: true` the generated Role grants read access to all Secrets in the namespace; fix PR #893 is open and v0.16.0 does not mention it [34]. Acceptable in a single-purpose namespace; note it.

## Cross-dimension insights

- **The account plan and the bootstrap layer are one decision.** A persistent Route 53 zone, bucket and ECR only make sense on an account that survives; the Free plan does not [10]. Upgrading also adds the payment method that domain registration needs [13][15]. Both findings point the same way.
- **Per-incarnation naming is a design rule that spans three layers.** Same cluster name, same bucket prefix and a static IAM role are all individually fine; together they trigger #767. The `serverName` (and therefore the bucket path) must change on each create, and the restore must read the previous one [31]. Pod Identity then removes the second per-cluster change (the role trust) [35].
- **Teardown order is a cost control and a correctness control.** Delete the Gateway first, wait for the ALB to vanish, then uninstall the controller [24]; a stuck ALB would also keep billing $0.0225 an hour plus its public IPs [1].
- **Cheap does not mean tolerant.** At 25 hours the design costs about $8, but 5 vCPU of default quota and a Budgets refresh of about three times a day [16][18] mean a forgotten environment can run most of a day before any alert fires.

## Contrary evidence

The red-team pass searched for disconfirming evidence on four conclusions [digests/redteam-r1-1.md].
- **Free-plan closure:** survives; the primary doc is explicit [10]. Residual: EKS eligibility on the Free plan rests on the supported list [12] and the policy [41], with no first-hand report and one unreadable thread about a blocked load balancer.
- **Region pin:** weakened to the new streamlined sign-up only; the advanced sign-up is unrestricted [14].
- **Same-name recreate:** survives. No fix PR exists, and the per-incarnation `serverName` is a community pattern, not documented guidance [31].
- **Gateway chain:** weakened. The AWS blog's hostname discovery versus the docs' explicit ARN was reconciled by source [23]; the external-dns hand-off and deletion ordering remain unproven end to end.

## Recommendations

| # | Recommendation | Feeds | Confidence basis |
| --- | --- | --- | --- |
| 1 | Build epic 5; do not cut it. | Epic decision | Cost fits [1][3]; no blocker found |
| 2 | Archive each environment incarnation under its own `serverName` or prefix and restore from the prior one; add a CI check that rejects a reused name. | Epic 5 requirements, architecture constraint | Docs [30] plus open issue [31]; the pattern itself is community |
| 3 | Use the Paid plan, or upgrade before the 6-month mark and before buying the domain. | Epic 5 constraints | High [10][13]; domain-fee payment path unverified |
| 4 | Use Pod Identity for the database role; own the role in the bootstrap layer. | Architecture (IAM) | High on the AWS mechanism [35]; medium on plugin support [32] |
| 5 | Write an early smoke test: ALB, ACM by explicit ARN, external-dns alias record, teardown order. | Epic 5 first story | The chain is unproven [24][25] |
| 6 | Default to 2x t4g.medium; set a budget alert and a hard TTL on environments. | Epic 5 operations | High on prices [1]; Budgets lag [18] |
| 7 | Pin the plugin to v0.16.0 and CNPG to 1.30.x; install the Gateway API v1.6.0 CRDs from the manifest. | Epic 5 deployment | High [28][37][21] |
| 8 | Test the S3 policy in a scratch bucket before depending on it. | Epic 5 backup story | Inference only [38] |

## Open questions

1. Does the controller set `status.addresses[].type` to Hostname so external-dns picks it up without the annotation? Test on a real ALB, or read `gateway_controller.go` for the type field.
2. Does a Free-plan account complete a Route 53 registration without upgrading? Ask AWS Support or try it.
3. Does `plugins[].parameters.serverName` work for archiving, and does a numeric suffix per incarnation restore cleanly? Prove with one destroy and recreate cycle.
4. Which S3 actions does each backup stage need? Test with a deny-by-default policy.
5. Do `Exact` and `PathPrefix` both translate correctly on the ALB, and what does a listener-hostname mismatch do? Test the `/`, `/v1`, `/mcp`, `/.well-known/oauth-protected-resource` rules.
6. Primary domain prices (the AWS TLD PDF was unreadable to the tools used), primary spot prices, and an AWS page confirming gp3 pricing.
7. Do credits cover EKS, EC2 and ELB? No AWS page lists excluded services.
8. What does the account do on the advanced sign-up path (plan, Region choice)? Not verified.
9. external-dns TXT registry and `--policy` behaviour on Gateway deletion; Gateway readiness gates.

## Source appendix

All accessed 2026-11-12. "undated" means the live page showed no date.

| [n] | Supports | Publisher | Pub date | Accessed | Confidence |
| --- | --- | --- | --- | --- | --- |
| [1] | EKS, EC2, VPC, ELB, S3, ECR unit prices | [AWS Pricing API bulk files](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/index.json) | 2026-11-04 to 2026-11-11 | 2026-11-12 | high |
| [2] | EKS 1.36 release and support dates | [AWS EKS Kubernetes versions](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html) | undated | 2026-11-12 | high |
| [3] | EKS standard and extended rates, no ENI charge | [AWS EKS pricing](https://aws.amazon.com/eks/pricing/) | undated | 2026-11-12 | high |
| [4] | Public IPv4 $0.005 per hour, LB addresses | [AWS VPC pricing](https://aws.amazon.com/vpc/pricing/) | undated | 2026-11-12 | high |
| [5] | ALB hourly and LCU | [AWS ELB pricing](https://aws.amazon.com/elasticloadbalancing/pricing/) | undated | 2026-11-12 | high |
| [6] | Route 53 zone $0.50 | [AWS Route 53 pricing](https://aws.amazon.com/route53/pricing/) | undated | 2026-11-12 | high |
| [7] | .com and other TLD prices | [Classmethod](https://dev.classmethod.jp/en/articles/route53-tld-pricing-change-2026/) | 2026-06-09 | 2026-11-12 | medium |
| [8] | .click, .link, .net, .dev prices | [CostGoat](https://costgoat.com/pricing/route-53-domains) | 2026-10-20 | 2026-11-12 | low |
| [9] | EC2 on-demand and spot confirmation | [Vantage instances](https://instances.vantage.sh/) | 2026-11-12 | 2026-11-12 | medium (on-demand), low (spot) |
| [10] | Free plan lifetime, closure, credits, upgrade | [AWS Billing User Guide](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html) | undated | 2026-11-12 | high |
| [11] | Free Tier FAQ, credit expiry, retention | [AWS Free Tier FAQ](https://aws.amazon.com/free/faqs/) | undated | 2026-11-12 | high (closure), low (expiry) |
| [12] | Free-plan supported services | [AWS Accounts Reference](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html) | undated | 2026-11-12 | high |
| [13] | Upgrade to Paid | [AWS Accounts Reference](https://docs.aws.amazon.com/accounts/latest/reference/upgrade-account.html) | undated | 2026-11-12 | high |
| [14] | Region assigned by contact country | [AWS Accounts Reference](https://docs.aws.amazon.com/accounts/latest/reference/project-regions.html) | references 2026-08-18 | 2026-11-12 | high |
| [15] | Credits cannot pay domain fees | [AWS Route 53 Developer Guide](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-register.html) | undated | 2026-11-12 | high |
| [16] | 5 vCPU default quota | [AWS EC2 instance quotas](https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html) | undated | 2026-11-12 | high |
| [17] | Quota increase process | [AWS Service Quotas guide](https://docs.aws.amazon.com/servicequotas/latest/userguide/request-quota-increase.html) | undated | 2026-11-12 | high |
| [18] | Budgets refresh and actions | [AWS Cost Management guide](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html) | undated | 2026-11-12 | high |
| [19] | LBC v3.6.2 | [kubernetes-sigs releases](https://github.com/kubernetes-sigs/aws-load-balancer-controller/releases) | 2026-10-25 | 2026-11-12 | high |
| [20] | external-dns v0.24.0 | [kubernetes-sigs releases](https://github.com/kubernetes-sigs/external-dns/releases) | 2026-10-23 | 2026-11-12 | high |
| [21] | Gateway docs set: l7gateway (routes, fields), gateway.md and targetgroupconfig (CRD versions, install, target type), installation.md (version matrix), open-issues list (Helm CRDs, #4651); the l7gateway page alone does not carry the CRD, Helm or 1.36 points | [LBC docs](https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/gateway/l7gateway/) | undated | 2026-11-12 | medium |
| [22] | LoadBalancerConfiguration, scheme default | [LBC docs](https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/gateway/loadbalancerconfig/) | undated | 2026-11-12 | medium |
| [23] | Certificate selection order | [LBC source](https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/pkg/gateway/model/model_build_listener.go) | main, 2026-11 | 2026-11-12 | medium (summarised fetch) |
| [24] | status.addresses, finalizer and delete order | [LBC source](https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/controllers/gateway/gateway_controller.go) | main, 2026-11 | 2026-11-12 | medium (summarised fetch) |
| [25] | external-dns Gateway source behaviour | [external-dns source](https://raw.githubusercontent.com/kubernetes-sigs/external-dns/master/source/gateway.go) and [docs](https://kubernetes-sigs.github.io/external-dns/latest/docs/sources/gateway-api/) | master, 2026-11 | 2026-11-12 | high-medium |
| [26] | Old Gateway status bug, EKS 1.33 report | [LBC issue 4245](https://github.com/kubernetes-sigs/aws-load-balancer-controller/issues/4245) | 2025-06-26 | 2026-11-12 | medium |
| [27] | Gateway API GA announcement | [AWS Networking blog](https://aws.amazon.com/blogs/networking-and-content-delivery/aws-load-balancer-controller-adds-general-availability-support-for-kubernetes-gateway-api) | 2026-03-06 | 2026-11-12 | high (GA), medium (detail) |
| [28] | Plugin v0.16.0 and release notes | [plugin-barman-cloud releases](https://github.com/cloudnative-pg/plugin-barman-cloud/releases) | 2026-11-09 | 2026-11-12 | high |
| [29] | Plugin usage, install, object stores | [CNPG plugin docs](https://cloudnative-pg.io/plugin-barman-cloud/docs/usage/) | undated | 2026-11-12 | high |
| [30] | Recovery docs, empty-archive check | [CNPG 1.30 docs](https://cloudnative-pg.io/docs/1.30/recovery/) | undated | 2026-11-12 | high |
| [31] | Same-name recreate failure | [plugin issue 767](https://github.com/cloudnative-pg/plugin-barman-cloud/issues/767) | 2026-02-14 | 2026-11-12 | medium |
| [32] | Pod Identity works with the plugin | [plugin issue 772](https://github.com/cloudnative-pg/plugin-barman-cloud/issues/772) | 2026-03-03 | 2026-11-12 | medium |
| [33] | Docs gap for Pod Identity | [plugin issue 876](https://github.com/cloudnative-pg/plugin-barman-cloud/issues/876) | 2026-04-27 | 2026-11-12 | high |
| [34] | Plugin RBAC bugs 1117, 892, PRs 869, 893 | [plugin PR 869](https://github.com/cloudnative-pg/plugin-barman-cloud/pull/869) and [PR 893](https://github.com/cloudnative-pg/plugin-barman-cloud/pull/893) | 2026-11-03 | 2026-11-12 | medium-high |
| [35] | Pod Identity mechanics, per-cluster associations | [AWS EKS Pod Identity docs](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html) | undated | 2026-11-12 | high |
| [36] | terraform-aws-eks v21 inputs | [terraform-aws-eks](https://github.com/terraform-aws-modules/terraform-aws-eks/releases) | 2026-10-07 | 2026-11-12 | high |
| [37] | CNPG 1.30.1, K8s 1.36, barman removal notes | [CNPG releases](https://github.com/cloudnative-pg/cloudnative-pg/releases) | 2026-09-23 | 2026-11-12 | high |
| [38] | S3 multipart action mapping | [AWS S3 User Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html) | undated | 2026-11-12 | high |
| [39] | In-tree Barman removal in 1.32 | [CNPG devel docs](https://cloudnative-pg.io/docs/devel/appendixes/backup_barmanobjectstore/) | undated | 2026-11-12 | medium |
| [40] | Terraform 1.17.2 | [HashiCorp releases](https://github.com/hashicorp/terraform/releases) | 2026-11-11 | 2026-11-12 | high |
| [41] | Free-plan service control policy | [AWS Accounts Reference](https://docs.aws.amazon.com/accounts/latest/reference/scps-and-rcps-for-projects.html) | undated | 2026-11-12 | medium |
| [42] | Barman S3 operations | [Barman user guide](https://docs.pgbarman.org/release/3.18.0/user_guide/barman_cloud.html) | undated | 2026-11-12 | medium |

Version table (actual versus the author's):

| Component | Author | Actual current | Source, date |
| --- | --- | --- | --- |
| Kubernetes (EKS) | 1.36 | 1.36 on standard support; 1.37 also available | [2] 2026-11-12 |
| AWS Load Balancer Controller | 3.6 | 3.6.2 | [19] 2026-10-25 |
| external-dns | 0.24 | 0.24.0 | [20] 2026-10-23 |
| CloudNativePG | 1.30 | 1.30.1 | [37] 2026-09-23 |
| Barman Cloud Plugin | 0.15 | **0.16.0** | [28] 2026-11-09 |
| Terraform | 1.17 | 1.17.2 | [40] 2026-11-11 |
| terraform-aws-modules/eks | 21 | 21.29.0 | [36] 2026-10-07 |
| Gateway API CRDs (needed) | n/a | standard channel v1.6.0 | [21] |

## Staleness map

Computed with `recon_kit.py staleness` from the claims ledger, using the technical pack's windows (versions and prices one month, behaviour, plan, quota and bug claims six months). The tool measures from each source's publication month, so it flags 8 of 18 claims as stale (earliest re-check date 2026-07-01); that reflects release and publication dates, not retrieval. Every claim here was retrieved on 2026-11-12, so the practical schedule is:

| Re-check by | Claims | Why |
| --- | --- | --- |
| 2026-12-12 | Controller, external-dns, CNPG, plugin, Terraform and module versions; EKS, EC2, ALB, IPv4 and Route 53 prices; Kubernetes 1.36 support dates | One-month window for versions and prices; the plugin and controller release often |
| 2026-12-12 | `.com` and other domain prices; spot prices | Secondary and aggregator sources only; confirm from AWS's own price list before buying |
| Before building | Same-name recreate issue #767 and plugin issues #892, #1117; external-dns plus ALB Gateway behaviour | Open issues can close in any release |
| 2027-05-12 | Free-plan closure and credit terms; Region pin; default quotas; Pod Identity mechanics | Six-month window, but AWS rewrote the free plan in 2025, so check before upgrading the account |

The earliest re-check is 2026-12-12. A Refresh run on this folder starts from that table.
