---
type: epic
title: "terraform apply brings up the live URL on EKS from nothing"
parent: initiative-ticketscope
covers: [R3, R10, R11]
sources: []
companions: []
after: []
refined: false
risk: high
---

# terraform apply brings up the live URL on EKS from nothing

## Description

Terraform provisions short-lived EKS with a public HTTPS URL (DNS name and certificate). GitHub Actions deploys epic 1's chart and images there through OIDC, with no stored keys. The page and epic 4's MCP endpoint are live in under 30 minutes, including loading the corpus. Destroy leaves nothing billing, and hosting costs under $10/month. CloudNativePG backups go to S3, and a restore drill and a failure drill are recorded. Epics 6, 7 and 8 run on this URL.

## Outcome

ticketscope is rebuilt from zero for each demo and torn down after, cheaply and with no stored keys (initiative R10, R11; brief Success Criteria 3).

## Done when

- terraform apply plus the Actions deploy brings up the page and MCP endpoint on a public HTTPS URL, with the corpus loaded, in under 30 minutes (R10).
- terraform destroy leaves no billing resources, including load balancers, volumes, KMS keys and log groups created outside Terraform state (R10; addendum EKS gotchas).
- The deploy authenticates through GitHub OIDC, with no cloud keys stored in the repo or in secrets (R11).
- CloudNativePG backs up to S3, and a restore drill and an instance-failure drill are each recorded (R3).
- The month's hosting cost is under $10 (initiative Constraints).
- Delivered on the cluster, with an integrated check passing in CI.

## Boundaries

- Out: always-on hosting and autoscaling experiments (initiative Boundaries).
- Touch point: AWS account, S3, ECR and DNS — consumed and configured by Terraform; owner: epic-eks-environment

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R3, R10, R11)

## Notes

- Waits on epic-search-baseline because: it needs the Helm chart and images that CI already deploys to kind.
- Waits on epic-hybrid-retrieval because: the embedding model's resource needs size the nodes and the corpus load time.
- Waits on epic-mcp-server because: the live URL must serve the MCP server.
