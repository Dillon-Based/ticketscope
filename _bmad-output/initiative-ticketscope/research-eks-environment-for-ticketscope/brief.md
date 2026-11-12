# Research prompt: can a short-lived EKS demo environment meet these assumptions?

Paste everything below the line into a deep-research tool. Tool-neutral. It names no project, person or account.

---

## Your task

You are researching four technical questions for a solo engineer who plans to build a short-lived Kubernetes demo environment on Amazon EKS. Today is 2026-11-12. Answer from sources you retrieve now, not from memory: your training data is probably out of date on every one of these topics. If you cannot find evidence for something, say so plainly instead of filling the gap.

## The decision this serves

Whether to build the environment as designed or to cut it. Four assumptions underpin the design, and two of them could cut it outright:

- Gateway API on the AWS Load Balancer Controller can do the routing and TLS the design needs.
- A brand-new AWS account can run EKS inside the monthly budget.
- A recreated environment can back up to and restore from the same S3 bucket through IRSA.

Report anything that contradicts an assumption as prominently as anything that confirms one.

## The design, so you know what to check

- One EKS cluster, Kubernetes 1.36 on standard support. No EKS Auto Mode, no Fargate. A VPC with public subnets only and no NAT gateway. A managed node group of 2 Graviton (arm64) nodes. Managed add-ons: vpc-cni and ebs-csi.
- The environment is created and destroyed on demand, about 25 hours a month in total, so every resource is created and deleted repeatedly. Anything that survives a destroy, or breaks a recreate, matters.
- A persistent "bootstrap" layer outside the cluster holds a Route53 hosted zone for a registered domain, an ACM certificate for one fixed hostname, a GitHub OIDC provider and deploy role, one S3 bucket for Terraform state and database backups, and ECR repositories.
- In-cluster components, installed with Helm, never by Terraform: the AWS Load Balancer Controller, external-dns, CloudNativePG, and the Barman Cloud Plugin. The versions the author wrote down are listed below. Treat them as claims to check, and report the actual current versions.

| Component | Version the author wrote down |
| --- | --- |
| Kubernetes (EKS) | 1.36 |
| AWS Load Balancer Controller | 3.6 |
| external-dns | 0.24 |
| CloudNativePG | 1.30 |
| Barman Cloud Plugin | 0.15 |
| Terraform / terraform-aws-modules/eks | 1.17 / 21 |

## Question 1: Gateway API on the AWS Load Balancer Controller

Establish what works today, on EKS 1.36 with the controller version you find current.

1. Is the controller's Gateway API support generally available or still beta or experimental? Which controller version introduced it, which Gateway API version and CRD channel does it need, and what feature flags or installation steps are required?
2. One `Gateway` plus `HTTPRoute`s: can a single Gateway produce **one** ALB that routes by path to two different Services (`/` and `/v1` to one, `/mcp` and `/.well-known/oauth-protected-resource` to another)? Are `PathPrefix` and `Exact` matches both supported? Which `HTTPRoute` fields are ignored or unsupported?
3. TLS: how is an existing ACM certificate attached to the HTTPS listener, and does it select the certificate by the listener's hostname? Is that done through listener `certificateRefs`, a `LoadBalancerConfiguration` resource, annotations, or certificate auto-discovery? Does a listener `hostname` filter which routes attach, and what happens when a route's hostnames do not match?
4. external-dns: does the `gateway-httproute` source (or other Gateway sources) work with an ALB-backed Gateway, and does it write the Route53 alias record for the hostname? Which external-dns version is needed, and what is the record ownership and cleanup behaviour (TXT registry, `--policy`) when the Gateway is deleted?
5. Teardown: after the `Gateway` is deleted and the controller uninstalled, what AWS resources can be left behind (ALB, target groups, security groups, ENIs, listener rules), and what ordering avoids it? Report finalizer and stuck-deletion problems and the issues that describe them.
6. Pod targets: target type `ip` versus `instance`, health-check configuration, and readiness gates in this setup.
7. Known bugs and open issues in the controller's repository that affect this exact setup, with their status and whether each is fixed in the current release.

## Question 2: a brand-new AWS account

1. What plans does a newly created AWS account start on today (free plan versus paid plan)? State what each allows, including whether Amazon EKS, EC2 instances, Application Load Balancers and Route53 domain registration are usable on the starting plan, and what is blocked until the account is upgraded.
2. What credits does a new account get, how large, how long do they last, and what do they apply to and exclude? Check EKS, EC2, ELB, Route53 hosted zones and domain registration, public IPv4 charges, and Marketplace. What happens when credits or the free period end?
3. Do AWS Budgets and budget alerts work on every plan? Are there limits on actions?
4. Default service quotas on a new account that could block this design: running on-demand vCPUs for the instance family chosen (Graviton), Elastic IPs and the number of load balancers. How long does a quota increase take?
5. Any account-verification or fraud-review delay that commonly holds up new accounts, as reported by AWS docs or credible user accounts.

## Question 3: monthly cost against a $10 limit

Build a cost model for **us-east-1**, with every price traceable to an AWS pricing page or the AWS Pricing API as of this month. Budget: **about 25 environment-hours per month**, plus whatever is billed even when the environment is down.

Line items to price, with the price per unit and the unit:

- EKS control plane on standard support (and the extended-support rate, in case 1.36 is not on standard support).
- Two Graviton nodes, on-demand and spot, for each of `t4g.medium`, `t4g.large` and `m7g.large`. Include the node EBS volume (gp3, 30 GB).
- Two persistent database volumes of about 20 GB each, only while the environment exists.
- One Application Load Balancer: hourly charge plus the LCU charge at demo traffic.
- Public IPv4: the hourly charge per address, for the nodes and for the load balancer's subnets. Report how many addresses the design uses.
- Data transfer, ECR storage, S3 storage and requests at this scale (a database of about 1 GB, with weekly backups).
- Persistent costs: the Route53 hosted zone, a domain registration for a common TLD such as `.com` and for the cheapest reputable TLDs (state the actual annual price and the renewal price, which can differ), and any CloudWatch, KMS or Secrets Manager charges if applicable.

Deliver a table with a low, likely and high monthly figure for each line and a total. State clearly which total applies if the environment is torn down correctly and which if it is left running for 24 hours by mistake. Say whether the total fits under $10 a month, and which two levers move it most. Show your arithmetic.

## Question 4: IRSA for CloudNativePG backups through the Barman Cloud Plugin

1. How does the Barman Cloud Plugin authenticate to S3 on EKS today? Does it support IRSA (`inheritFromIAMRole` or a service-account annotation), EKS Pod Identity, or both? Which is better supported, and which would you recommend in a setup that creates a fresh cluster each time?
2. Exact configuration: the `ObjectStore` resource fields, the service account the plugin sidecar and the database pods use, and the annotation that links it to an IAM role.
3. The minimum IAM policy for backup, WAL archiving, restore and retention cleanup on one bucket prefix.
4. Because the cluster, and so its OIDC issuer, is **recreated every time**, how should the role's trust policy be built so it follows each new cluster's OIDC provider? Report any caveat about creating the OIDC provider per cluster.
5. **Recreate and restore.** When an environment is destroyed and a new cluster with the same name is created against the same bucket and prefix, what happens to WAL archiving? Report the documented failure modes (such as a non-empty archive, or a server-name collision) and how the `serverName` or path settings avoid them. How does restoring a backup into a brand-new cluster work with the plugin's recovery configuration, and what must exist (role, object store, credentials) before it can start?
6. Compatibility of CloudNativePG 1.30, the Barman Cloud Plugin 0.15 and Kubernetes 1.36, and any breaking changes, including the removal of in-tree Barman object store support.

## Source policy

- Prefer: AWS documentation, the AWS pricing pages and Pricing API, AWS blog and What's New posts, the GitHub repositories, release notes and issue trackers of `kubernetes-sigs/aws-load-balancer-controller`, `kubernetes-sigs/external-dns`, `cloudnative-pg/cloudnative-pg`, `cloudnative-pg/plugin-barman-cloud` and `terraform-aws-modules/terraform-aws-eks`, and the CloudNativePG and Gateway API documentation.
- Read issue threads and release notes, not launch announcements. An old complaint against a current version is a false claim, so check whether each reported problem has been fixed.
- Blog posts and forum answers are allowed as supporting evidence only, never as the sole source for a version, price or limit.
- No sources are banned.

## Freshness and evidence

- Version and compatibility claims: from the last month. Prices: from the last month. Ecosystem and issue claims: from the last six months.
- A claim about a version, a price, or "this fails" needs two independent sources, or must come from the primary AWS or project documentation.
- A claim is a sentence with a source URL, the publication date, and the date you accessed it. No naked numbers.
- Report contrary evidence. Admit gaps. Do not pad a thin answer. "I could not find this" is a finding.

## Required output

Write for an engineer who will act on it. Use this structure so it can be extracted cleanly:

1. **Verdict per assumption**: one line each for the Gateway/ALB/ACM/external-dns assumption, the new-account assumption, the cost assumption and the IRSA-recreate assumption: Holds, Holds with changes, or Does not hold, with the single most important reason.
2. **Findings per question** (1–4): the answers to the numbered sub-questions, each claim with its URL and dates.
3. **Cost table** for Question 3, with arithmetic.
4. **Contradictions and gotchas**: anything that would change the design, ranked by how much it would cost to discover late.
5. **Version table**: the actual current version of each component, with source and date, against the table above.
6. **Source list**: every URL cited, with publisher, publication date and access date.
