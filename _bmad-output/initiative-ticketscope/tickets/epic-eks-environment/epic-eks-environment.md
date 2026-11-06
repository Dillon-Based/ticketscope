---
type: epic
title: "terraform apply brings up the live URL on EKS in under 30 minutes"
parent: initiative-ticketscope
covers: [R3, R10, R11]
sources: []
companions: []
after: []
refined: false
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

## Done when

- From the bootstrap layer, env-up brings up the page and MCP endpoint on the fixed HTTPS hostname in under 30 minutes, with the corpus loaded. env-up runs Terraform apply plus the Helm deploy and records its wall-clock time (R10).
- env-down runs the spine's ordered teardown. A tag-scoped check then finds nothing but the bootstrap layer: no load balancers, ENIs, volumes, KMS keys or log groups left outside Terraform state (R10; addendum EKS gotchas).
- The deploy authenticates through GitHub OIDC, with no cloud keys stored in the repo or in secrets. Backups use an IRSA role (R11).
- CloudNativePG backs up to S3, and a restore drill and an instance-failure drill are each recorded (R3).
- A budget alarm and an environment expiry are in place, and the month's hosting cost, bootstrap layer included, is under $10 (initiative Constraints).
- Delivered on the cluster, with an integrated check passing in CI.

## Boundaries

- Out: always-on hosting, autoscaling experiments, EKS Auto Mode and Fargate (initiative Boundaries; spine AD-16).
- Terraform owns only AWS resources; every in-cluster release is installed by the workflow with Helm.
- Touch point: AWS account, S3, ECR and DNS — consumed and configured by Terraform; owner: epic-eks-environment

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R3, R10, R11)
- architecture spine — _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md, AD-1–AD-3, AD-6, AD-7, AD-9, AD-13–AD-18, AD-21–AD-25

## Notes

- Waits on epic-search-baseline because: it needs the Helm releases and images that CI already deploys to kind.
- Waits on epic-hybrid-retrieval because: the embedding model's resource needs and precomputed embeddings size the nodes and the corpus load time.
- Waits on epic-mcp-server because: the live URL must serve the MCP server.
- Decision: Adopted the architecture spine. A persistent bootstrap layer and an ephemeral environment replace "from nothing", and the title now says what is timed (user, 2026-11-05).
