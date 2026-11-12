# Citation check r1-1 (2026-11-12)

Scope: verdict table, five design changes, Q1-Q4 findings, cost arithmetic, recommendations, checked against digests. Report not edited.

## Mismatches

1. **Cost table, "High" column total (Q3, table "Monthly line, 25 h").** Report says "about 11.9". Summing the High column lines (2.50+4.08+0.27+0.56+0.20+0.50+0.10+0.50+0.15+0.50+1.42) gives 10.78. The q3 digest repeats ~11.9, so the error originates there. Low column sums to 5.60 (report "about 5.5"); Likely sums to 7.88 (ok). Effect: the High case is overstated by about $1.1. Cited [1][3] etc. unaffected. Fix the number or drop the claim.
2. **Pod targets paragraph, TLS/CRD sentences cite [21] (Q1).** [21] is the l7gateway page. Spot-fetch of that page: it has no mention of the Helm chart not installing CRDs, no v1.6.0, no default target type or `ip` / VPC CNI, no Kubernetes version. Digest q1 sourced those from gateway.md, targetgroupconfig, releases and the issues list (#4651). Also "one Gateway, one ALB" is stated only as "for every gateway ... the LBC provisions an ALB". Wrong-appendix: [21] is a bundle of several pages. Confidence: keep medium; add sources.
3. **EKS 1.36 not named in controller matrix, cited [21] (Q1 Versions).** Digest source is installation.md, not the l7gateway page. Wrong appendix entry.
4. **Public IPv4 / ENI sentence (Q3).** "No ENI or EKS-specific public IPv4 charge applies to a basic cluster [3][4]". Digests say only that none is listed on the EKS page (verify #9); q3 main digest calls the control-plane ENI point "unverified belief". Stated more strongly than evidence. Downgrade to "none listed" (medium).
5. **Spot "low" node cost 0.82 (Q3 table).** Corresponds to $0.0164/h (q3 main digest), but the unit table and verify digest give $0.017/h (=0.85). Minor inconsistency; spot is low confidence anyway.
6. **".click $3 / .link $5" attributed to CostGoat [8].** q3 main digest says CostGoat; verify digest says these came from stale 2024 search snippets and are unverified post-July 2026. Report already says "pre-July prices unverified"; consider low confidence rather than a table figure.
7. **"A 730-hour month costs 20x the budget" (Q3 levers).** From the table: 164 / 213 / 234 = 16x / 21x / 23x. "20x" fits t4g.large only; t4g.medium default is 16x.
8. **Same-name recreate "fails" / "Otherwise the second create fails" (change 1, Q4, verdict row 4).** Evidence: CNPG 1.30 recovery docs [30] confirmed by spot fetch (error text, unique serverName advice, skip annotation "strongly discouraged"). But the docs do not address same-name recreate; the failure claim rests on issue #767 [31], medium, reported on CNPG 1.26 / plugin 0.11.0 and not shown to reproduce on 1.30 / 0.16.0. Digest q4 itself says "I found no primary doc stating the empty-archive rule" for same-name. Suggest "likely fails" (medium-high) instead of fact. The workaround is bot-suggested in the thread, report calls it "community"; fine.
9. **[29] covers install page claim.** "Plugin install page requires CNPG 1.30+ and cert-manager" is from /docs/installation/, but appendix [29] lists only /docs/usage/. Minor wrong-appendix.
10. **Pod Identity recommendation and per-cluster `aws_eks_pod_identity_association` resource.** Report marks recommendation as inference (ok). The statement that the association is "an aws_eks_pod_identity_association" resource is the digest's own inference, not module-doc verified; the report's "Confidence high on AWS mechanism [35]" is fine.
11. **Rounding (Q3 node table).** Recomputed totals: 7.85 / 9.53 / 10.25 (report 7.84 / 9.52 / 10.24); +24 h: 13.24 / 16.53 / 17.94 (report 13.2 / 16.5 / 18.0). Immaterial.

## Verified without mismatch

- Arithmetic: fixed per env-hour 0.15746 (report 0.1575); persistent 2.23; 24 h 5.39 / 7.00 / 7.70; 730 h 164.0 / 213.1 / 234.1; break-even 34.6 and 26.6 h; $0.22 to $0.32 per hour.
- Free-plan closure (spot-fetched [10]): "account closes automatically", 90-day retention, 6 months or credits, remaining credits carry over, comparison table "Account closes when ..." all match. Upgrade "cannot be reversed" and "immediate once payment method added" are from [13] per digest (not refetched).
- Region pin (spot-fetched [14]): us-east-2 / eu-north-1 / ap-southeast-2 by contact country, advanced sign-up escape, "as of August 18, 2026" all match; Europe group includes Africa and Middle East, Asia Pacific group includes India, Japan, China.
- CNPG 1.30 recovery (spot-fetched [30]): matches report, except note in item 8.
- l7gateway [21] (spot-fetched): "does not fully implement all Core functionality" and certificateRefs unsupported confirmed. "ListenerSets experimental" is only implied (table marks AllowedListeners Experimental, see ListenerSets).
- Q2 claims on [10][11][12][13][15][16][17][18][41] and Q4 claims on [28][32][33][34][35][37] match digests. The red-team digest states the EKS-on-Free-plan list evidence was not fetched by that agent, while q2 digest does cite the supported-services page; the report relies on q2 and flags the residual correctly.
- Unverified items (status.addresses type, Exact vs PathPrefix, S3 policy, domain on Free plan) are correctly labelled unverified or inference.
