# Digest q4-irsa-r1-1: recreated EKS env backing up to one S3 bucket via IRSA (CNPG + Barman Cloud Plugin)

Accessed 2026-11-12. Rounds 1 and 2 merged by sub-question. Claim format: {claim | source | publisher | pub_date | confidence | class}. Fetch tool summarizes pages through a small model, so verbatim quotes are second-hand.

## Verdict
The assumption mostly holds, with caveats. IRSA and Pod Identity both work via `s3Credentials.inheritFromIAMRole: true`. Pod Identity fits a destroy/recreate cluster better than IRSA. WAL archive reuse under the same serverName is the real risk, and I found no primary doc stating the empty-archive rule. The IAM minimum policy is NOT evidenced from primary docs.

## Versions (class: version)
- Plugin latest is v0.16.0 (2026-11-09); v0.15.1 (2026-09-30); v0.15.0 (2026-09-03). Brief's "0.15" is one minor behind. | https://github.com/cloudnative-pg/plugin-barman-cloud/releases | GitHub | 2026-11-09 | high | version
- Plugin install page (v0.16.0): CNPG "must be 1.30 or newer"; cert-manager required (`cmctl check api`); plugin must be in same namespace as operator (cnpg-system). | https://cloudnative-pg.io/plugin-barman-cloud/docs/installation/ | CNPG project | current | high | version
- CNPG latest is v1.30.1 (2026-09-23); v1.30.0 (2026-06-29) adds Kubernetes 1.36 support (also 1.29.2). 1.29 and 1.28 no longer supported. | https://github.com/cloudnative-pg/cloudnative-pg/releases | GitHub | 2026-09-23 | high | version
- Terraform v1.17.2 (2026-11-11) exists; 1.17.0 released 2026-10-21. | https://github.com/hashicorp/terraform/releases | GitHub | 2026-11-11 | high | version
- terraform-aws-eks latest v21.29.0 (2026-10-07). v21 requires Terraform >=1.5.7, AWS provider >=6.0.0, TLS >=4.0.0. | https://github.com/terraform-aws-modules/terraform-aws-eks/releases ; .../docs/UPGRADE-21.0.md | GitHub | 2026-10-07 | high | version
- Plugin release notes show no CNPG/Kubernetes compat matrix; v0.8.0 renamed RBAC resources (barman-plugin- prefix), a breaking change. | releases page above | GitHub | 2025-10-27 | medium | version
- Kubernetes 1.36 on EKS itself: NOT verified (not searched).

## Q1 Authentication
- Pod Identity works with the plugin via `s3Credentials.inheritFromIAMRole: true`; reporter confirmed it already worked, issue #772 closed 2026-03-03. Role trust: `pods.eks.amazonaws.com` with `sts:AssumeRole` and `sts:TagSession`; plus a PodIdentityAssociation to the Postgres service account. | https://github.com/cloudnative-pg/plugin-barman-cloud/issues/772 | GitHub issue (reporter, not maintainer-documented) | 2026-03-03 | medium | config
- Docs gap: official plugin docs do not document Pod Identity (issue #876 open since 2026-04-27 asking for it). Official object_stores page only shows IRSA annotation. | https://github.com/cloudnative-pg/plugin-barman-cloud/issues/876 ; https://cloudnative-pg.io/plugin-barman-cloud/docs/object_stores/ | GitHub / CNPG | 2026-04-27 | high | other
- Plugin passes auth through to barman-cloud (boto3); user must verify their method is supported. | object_stores page (via search snippet) | CNPG | current | medium | behavior
- AWS: Pod Identity does not use OIDC providers; "If you have the same application in multiple clusters, you can make identical associations in each cluster without modifying the trust policy of the role." Needs the eks-pod-identity-agent add-on (DaemonSet); eventually consistent (seconds); Linux EC2 nodes only (no Fargate). | https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html | AWS | current | high | behavior
- Recommendation (my inference from the above, not stated by any source): Pod Identity for a recreated-cluster env, since trust policy and role stay constant. IRSA is the officially documented path in plugin docs.

## Q2 Exact config
Plugin docs (usage) cluster-side:
```yaml
# source: https://cloudnative-pg.io/plugin-barman-cloud/docs/usage/
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata: {name: cluster-example}
spec:
  instances: 3
  plugins:
  - name: barman-cloud.cloudnative-pg.io
    isWALArchiver: true
    parameters:
      barmanObjectName: s3-store
```
IRSA ObjectStore + SA annotation (third-party blog, OneUptime 2026-09-18, https://oneuptime.com/blog/post/2026-09-18-cloudnativepg-minio-s3-iam-ca-path-style/view; annotation form also in official docs):
```yaml
kind: ObjectStore   # apiVersion barmancloud.cnpg.io/v1
spec:
  configuration:
    destinationPath: s3://aws-postgres-backups/production
    s3Credentials:
      inheritFromIAMRole: true
---
kind: Cluster
spec:
  serviceAccountTemplate:
    metadata:
      annotations:
        eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/orders-backup
```
- `ObjectStore.spec.configuration.serverName` must stay empty; use plugin parameter `serverName` in Cluster. | usage docs | CNPG | current | high | config
- ObjectStore spec: `configuration`, `retentionPolicy` (`^[1-9][0-9]*[dwm]$`), `instanceSidecarConfiguration` (env, retentionPolicyIntervalSeconds default 1800, resources, additionalContainerArgs, logLevel). | https://cloudnative-pg.io/plugin-barman-cloud/docs/plugin-barman-cloud.v1/ | CNPG | current | high | config
- Service account: plugin binds Role `<cluster>-barman-cloud` to SA named after the Cluster, ignoring `spec.serviceAccountName`; bug open (#1117, 2026-09-28), would break IRSA/Pod Identity setups using a custom SA. Default SA = cluster name, so annotate via `serviceAccountTemplate` and don't set `serviceAccountName`. | https://github.com/cloudnative-pg/plugin-barman-cloud/issues/1117 | GitHub | 2026-09-28 | medium | bug
- Bug: with `inheritFromIAMRole: true` the generated Role grants `secrets` access with empty resourceNames (all Secrets in namespace). Open, fix PR #893 open; seen in v0.14.0. Not shown fixed in 0.15/0.16 notes. | https://github.com/cloudnative-pg/plugin-barman-cloud/issues/892 | GitHub | 2026-05-07 | medium | bug
- Caveat: changing SA annotation does not affect existing pods (blog). | OneUptime | 2026-09-18 | low | behavior

## Q3 Minimum IAM policy
- NOT found in any primary doc. Pod Identity issue #772 reporter used `s3:Get*`, `s3:List*` (read, for restore) plus `kms:Decrypt`/`kms:DescribeKey` if KMS. Blog lists operations only (upload, read/list, multipart cleanup, delete, KMS). Docs recommend bucket versioning + lifecycle expiry instead of broad delete permissions.
- Unverified belief (from training, not evidenced this run): backup/WAL needs `s3:PutObject`, `s3:GetObject`, `s3:ListBucket` (bucket ARN, prefix condition), `s3:AbortMultipartUpload`, `s3:ListMultipartUploadParts`; retention cleanup needs `s3:DeleteObject`. Check Barman docs in a follow-up.

## Q4 Trust policy / OIDC per cluster
- terraform-aws-eks: `enable_irsa` default true (creates OIDC provider); `include_oidc_root_ca_thumbprint` default true; `custom_oidc_thumbprints` default []; output `oidc_provider` = issuer without https://. | https://raw.githubusercontent.com/terraform-aws-modules/terraform-aws-eks/master/README.md | GitHub | current | high | config
- Issuer URL is cluster-unique (per-cluster ID), so IRSA trust must reference each new `oidc_provider` and a SA subject `system:serviceaccount:<ns>:<sa>`. Role must be built from module output each run or its trust updated. (Inference; not read directly from a source.)
- v21 UPGRADE doc: issuer URL changed to dual-stack `oidc-eks` endpoint; thumbprint behavior beyond README not verified.
- Pod Identity avoids this: single principal `pods.eks.amazonaws.com`; module `addons` accepts `pod_identity_association` list (role_arn, service_account). | README, AWS doc | high | config
- Issue #1117 states IRSA ties credentials to SA name so recreated/renamed clusters need new cloud-side credentials (reporter's claim).

## Q5 Recreate and restore
- Restore stanza from official usage docs:
```yaml
# source: https://cloudnative-pg.io/plugin-barman-cloud/docs/usage/
spec:
  bootstrap:
    recovery:
      source: source
  externalClusters:
  - name: source
    plugin:
      name: barman-cloud.cloudnative-pg.io
      parameters:
        barmanObjectName: s3-store
        serverName: cluster-example
```
  Recovered cluster does not archive WAL unless `.spec.plugins` with `isWALArchiver: true` and a separate ObjectStore (docs example: `s3-store-bis`) is added. | high | config
- Docs "strongly recommend one object store per PostgreSQL cluster." Docs do not discuss serverName collisions or "Expected empty archive" (string not found anywhere). | usage/concepts docs | high | behavior
- Barman `barman-cloud-check-wal-archive` fails when archive path has WAL, unless all WAL is from earlier timelines; path keyed by serverName/cluster name, so a same-name new cluster hits the same path. | https://docs.pgbarman.org/release/3.8.0/barman-cloud-check-wal-archive.1.html ; barman issue #432 | Barman | medium | behavior
- Plugin v0.14.0 "honors the operator's check_empty_wal_archive decision". Mechanism not read; suggests the operator decides whether to check. | releases | medium | behavior
- Mitigation consistent with sources: restored cluster archives to a new serverName/prefix, or use unique cluster name per incarnation (e.g., suffix) while restoring from old serverName. Blog warns changing recovery serverName to the new name breaks restore. | https://oneuptime.com/blog/post/2026-09-18-cloudnativepg-green-backup-failed-restore/view | OneUptime | 2026-09-18 | low | other
- Prerequisites at restore time (inference): cert-manager, CNPG 1.30+, plugin in cnpg-system, ObjectStore + SA/role/association before the Cluster.
- With Pod Identity: association must exist in the new cluster before pods start (credentials injected at pod creation).

## Q6 Compatibility
- Plugin 0.16.0 needs CNPG >= 1.30; 0.15 requirement not checked. CNPG 1.30 supports K8s 1.36. cert-manager required.
- barmanObjectStore removal: DEPENDS ON SOURCE, see Contradictions.

## Contradictions
1. Removal version of in-tree Barman: CNPG release notes (v1.30.0/1.29.2/1.28.4) say removal in 1.31.0 "rather than 1.30.0"; the CNPG devel backup docs say "1.31 is last minor with native support, removed from 1.32.0"; the 1.30 backup docs name no version. Needs a primary re-check (release notes may have been revised). Note v1.30.1 still adds in-tree features.
2. Brief says plugin 0.15; actual latest is 0.16.0 (0.15.1 latest patch of 0.15).
3. Pod Identity "supported" per issue #772 yet absent from official docs (#876 open).
4. Plugin-generated Role issues (#892, #1117) are open and could hit an IAM-role-based setup.

## Leads not chased
- Fix status of #892 (PR #893) and #1117 in 0.16.0 notes.
- Plugin docs troubleshooting / "check_empty_wal_archive" annotation mechanism; CNPG `cnpg.io/skipEmptyWalArchiveCheck`.
- Barman docs for exact S3 permissions; AWS IRSA doc on thumbprints (AWS now verifies EKS OIDC via trusted CAs, unverified).
- EKS support of Kubernetes 1.36 and Pod Identity Agent add-on compatibility.
- Plugin 0.15 compat requirement; Helm chart for plugin versions.

## Looked for but could not find
- Any primary doc for minimum S3 IAM actions.
- "Expected empty archive" exact string.
- Official documentation of Pod Identity with the plugin.
- Documented serverName collision guidance for the plugin.

---

# Round 2 (accessed 2026-11-12)

## R2-1 Minimum S3 IAM actions
- No plugin/CNPG/Barman doc gives a complete S3 policy. Barman user guide names only `s3:GetObjectRetention` and `s3:GetObjectLegalHold` (needed for `barman-cloud-backup-delete --check-object-lock`). | https://docs.pgbarman.org/release/3.18.0/user_guide/barman_cloud.html | Barman | current | medium | config
- `barman-cloud-check-wal-archive` first calls `HeadBucket` and, if the bucket is missing, tries to create it (so `s3:ListBucket` for HeadBucket; bucket pre-exists so creation need not be granted). Same source. | medium | behavior
- AWS S3 multipart doc maps actions: `s3:PutObject` (create/upload/complete), `s3:AbortMultipartUpload`, `s3:ListMultipartUploadParts`, `s3:ListBucketMultipartUploads`; KMS needs `kms:GenerateDataKey` + `kms:Decrypt`. | https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html | AWS | current | high | config
- Issue #772 reporter's restore-role: `s3:Get*`, `s3:List*` (+ `kms:Decrypt`, `kms:DescribeKey`). Plugin docs recommend bucket versioning/lifecycle instead of broad delete rights.
- Assembled candidate (INFERENCE, not stated as a set by any source; test it): Object actions on `arn:aws:s3:::BUCKET/PREFIX/*`: `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject` (retention cleanup only), `s3:AbortMultipartUpload`, `s3:ListMultipartUploadParts`; bucket actions on `arn:aws:s3:::BUCKET` with `s3:prefix` condition: `s3:ListBucket`, `s3:ListBucketMultipartUploads`; optionally `s3:GetBucketLocation`; KMS if SSE-KMS. Add `s3:GetObjectRetention`/`s3:GetObjectLegalHold` only with object lock. If lifecycle rules do deletion, omit `s3:DeleteObject` (but plugin retentionPolicy then fails).

## R2-2 Same-name cluster on same bucket/prefix
- Official CNPG recovery docs (1.30): safety check failure leaves the cluster in "Setting up primary", pod log "ERROR: WAL archive check failed for server recoveredCluster: Expected empty archive". Advice: "Avoid reusing the same ObjectStore configuration for both backup and recovery in the same cluster"; if so "each cluster uses a unique serverName". Annotation `cnpg.io/skipEmptyWalArchiveCheck: enabled` bypasses, "strongly discouraged". Same-name recovery not addressed. | https://cloudnative-pg.io/docs/1.30/recovery/ | CNPG | current | high | behavior
- Plugin issue #767 (open; closed then reopened 2026-05-20): restoring under the same name as the deleted source fails; serverName defaults to cluster name, so the new cluster's archive path (same name) still holds old WAL, so the check fails. Bot-suggested workarounds (not maintainer-confirmed): different cluster name; keep name but set the recovery `externalClusters` serverName to the old value while new cluster's archiving uses a new serverName (e.g. `-v2`, bump each restore); empty the path; or skip annotation. Labeled bug, bot calls it design constraint. | https://github.com/cloudnative-pg/plugin-barman-cloud/issues/767 | GitHub | 2026-02-14 | medium | bug
- Implication for this design: recreating the cluster with the SAME name against the SAME prefix will hit this unless the new incarnation archives to a different serverName (plugin parameter `serverName` on the `.spec.plugins` entry) or prefix. This directly contradicts the "same cluster name, one bucket" assumption unless serverName is varied per incarnation.
- #350 (closed 2025-08-21 via PR #457): error occurred even with plugin disabled in restore; a later commenter reports still reproducing on CNPG v1.30.0, and that adding the plugin to a cluster created without it skips the check (marker file already deleted). https://github.com/cloudnative-pg/plugin-barman-cloud/issues/350 | medium | bug
- #828 (open, 2026-04-08): former primary after failover hits "Expected empty archive" because check ran without `--timeline`. PR #843 (timeline detection, `--timeline`) reportedly merged 2026-04-15, but reports persist on plugin v0.14.0 + operator v1.30.0 (2026-09-09). Not confirmed fixed in a release. https://github.com/cloudnative-pg/plugin-barman-cloud/issues/828 | medium | bug. Relevant to HA (instances>1) only; a single-instance demo likely avoids it (inference).
- Plugin v0.14.0 note: "honors the operator's check_empty_wal_archive decision" (release page).

## R2-3 terraform-aws-eks v21 with per-cluster recreation
- IRSA: `enable_irsa` default true creates OIDC provider per cluster; output `oidc_provider_arn` / `oidc_provider` feed trust policy, so with Terraform in one root module the role trust follows each new cluster automatically (inference). If the role is in a persistent stack separate from the cluster, trust must be updated per cluster. README.
- Pod Identity: `addons.<name>.pod_identity_association = [{role_arn, service_account}]` input exists; `eks-pod-identity-agent` addon (use `before_compute = true`). Association is created per cluster in EKS; role trust is the static `pods.eks.amazonaws.com` with `sts:AssumeRole`+`sts:TagSession`; namespace/SA need not exist at creation, and no SA annotation is used. AWS doc: https://docs.aws.amazon.com/eks/latest/userguide/pod-id-association.html (high). Role can therefore live in a persistent stack with the bucket. Note: `pod_identity_association` is documented on addons (for the addon's own SA); for the CNPG SA use a separate `aws_eks_pod_identity_association` resource (inference; not verified in module docs).
- Pod Identity creds are injected at pod creation: association must exist before CNPG pods start (AWS: eventually consistent, seconds).
- v21 cluster-level thumbprint inputs (`include_oidc_root_ca_thumbprint`, `custom_oidc_thumbprints`) exist; nothing found on destroy/recreate issues.

## R2-4 EKS Kubernetes 1.36
- Yes. EKS release of 1.36: June 2, 2026 (upstream April 22, 2026); end of standard support August 2, 2027. 1.37 also available (EKS Oct 1, 2026). Standard support list: 1.37, 1.36, 1.35, 1.34. | https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html | AWS | current | high | version
- CNPG 1.30 supports K8s 1.36 (round 1); CNPG 1.30 support for 1.37 not checked.

## R2-5 #1117 and #892 in plugin v0.16.0
- #1117 (open, bind Role to custom serviceAccountName): the underlying defect was fixed by merged PR #869 ("rbac: Bind the Role to the cluster's custom serviceAccountName", merged 2026-11-03 into main; part of release PR #1139 "release 0.16.0", also listed in the v0.16.0 changelog). The #1117 issue itself is still open (a manual workaround thread), and a commenter on v0.15.1 reported the bug there. So: fixed in 0.16.0, not in 0.15.x. Existing RoleBinding subject update on reconcile is the commenter's code-reading, unconfirmed. Sources: https://github.com/cloudnative-pg/plugin-barman-cloud/pull/869 ; https://github.com/cloudnative-pg/plugin-barman-cloud/releases/tag/v0.16.0 | medium-high | bug
- #892 (wildcard Secret RBAC with inheritFromIAMRole): PR #893 still OPEN, unmerged, no milestone (fetched 2026-11-12); v0.16.0 notes don't mention it. NOT fixed in 0.16.0. Risk: the DB service account (the one with the IAM role) can read all Secrets in its namespace; acceptable for a single-purpose demo namespace, worth noting. | https://github.com/cloudnative-pg/plugin-barman-cloud/pull/893 | high | bug

## Round 2 corrections / contradictions
- Round 1 said #1117 not confirmed fixed: now: fixed in v0.16.0 via #869 (so use 0.16.0, not 0.15, if a custom serviceAccountName is wanted).
- Same-name recreate: docs silent; issue #767 says it fails by design unless serverName differs. This is the main threat to the brief's assumption.
- Fetch-tool summaries are second-hand; the claim that PR #869's change landed in the v0.16.0 tag rests on a changelog line plus the cross-referenced release PR.

## Leads not chased
- Actual S3 policy tested end to end (no source); Barman `--check-object-lock` side effects.
- Whether CNPG supports setting plugin-parameter `serverName` on `.spec.plugins` for archiving (usage docs example shows it on externalClusters; the digest's claim that plugins accepts serverName rests on #767's bot YAML and the docs line "use the serverName plugin parameter in the Cluster configuration").
- Whether PR #843 shipped in 0.15/0.16.
