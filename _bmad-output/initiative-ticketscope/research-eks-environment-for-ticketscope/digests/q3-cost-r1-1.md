# Q3 cost model, round 1 (us-east-1, 2026-11-12)

Verdict: FITS under $10/month at 25 env-hours for t4g.medium (~$7.8) and t4g.large (~$9.5, thin margin) with a .com; m7g.large (~$10.2) does NOT fit on-demand. One forgotten day (+24h) breaks the budget for every size. Spot is unverified.

## Sources (all accessed 2026-11-12)
- AWS Pricing API bulk JSON (primary, downloaded to scratch, parsed with python -I): AmazonEKS (publicationDate 2026-11-11), AmazonEC2 us-east-1 regional file (2026-11-10), AmazonVPC (2026-11-05), AWSELB (2026-11-11), AmazonS3 (2026-11-09), AmazonECR (2026-11-11), AmazonRoute53 (2026-11-04). URL pattern https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/<Service>/current/index.json (EC2: .../AmazonEC2/current/us-east-1/index.json).
- EKS versions doc: https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html
- https://aws.amazon.com/vpc/pricing/ , https://aws.amazon.com/route53/pricing/
- Domain: AWS per-TLD pages (no prices on them), AWS PDF (unreadable to my tools), secondary: https://dev.classmethod.jp/en/articles/route53-tld-pricing-change-2026/ and https://costgoat.com/pricing/route-53-domains (updated 2026-10-20).

## Version
Kubernetes 1.36: EKS release June 2, 2026; end of standard support Aug 2, 2027; end of extended Aug 2, 2028. Standard-support list on 2026-11-12: 1.37, 1.36, 1.35, 1.34. So 1.36 is on standard support (control plane $0.10/h). 1.37 (released on EKS Oct 1, 2026) is also available.

## Unit prices (us-east-1)
| Item | Price | Unit | Source |
|---|---|---|---|
| EKS cluster, standard support | $0.10 | per cluster-hour | EKS price list (USE1-AmazonEKS-Hours:perCluster) |
| EKS extended support | $0.50 | per cluster-hour | EKS price list (USE1-AmazonEKS-Hours:extendedSupport) |
| t4g.medium Linux on-demand | $0.0336 | per instance-hour | EC2 price list |
| t4g.large | $0.0672 | per hour | EC2 price list |
| m7g.large | $0.0816 | per hour | EC2 price list |
| gp3 | $0.08 | per GB-month (prorated per second; baseline 3000 IOPS/125 MB/s included, belief) | EC2 price list |
| ALB hourly | $0.0225 | per ALB-hour | ELB price list |
| ALB LCU | $0.008 | per LCU-hour | ELB price list |
| Public IPv4 (in-use or idle) | $0.005 | per address-hour | VPC price list + vpc/pricing page |
| ECR storage | $0.10 | per GB-month | ECR price list |
| S3 Standard | $0.023 | per GB-month first 50 TB | S3 price list |
| S3 PUT/COPY/POST/LIST | $0.005 per 1,000; GET $0.004 per 10,000 | | S3 price list |
| Route 53 hosted zone | $0.50 | per zone-month, not prorated | aws.amazon.com/route53/pricing |
| Route 53 standard queries | $0.40 | per million | same |
| Domain .com | $16 reg, $16 renew (was $15 before 2026-07-01) | per year | classmethod + costgoat (secondary only) |
| .click / .link / .net / .dev | $3 / $5 / $17 / $17 (reg = renew) | per year | costgoat only (single secondary source) |

Spot (NOT from a primary source; aggregators via web search, dates mixed): t4g.medium avg ~$0.0164 (max ~$0.0190 stated, zone table up to $0.0263); t4g.large avg ~$0.0565 (range 0.0237-0.0864, page dated 2026-01-16); m7g.large ~$0.0265-0.0605 across pages (I used 0.04). Low confidence, use as order of magnitude only.

## Counts and assumptions
- ALB in 2 AZ subnets: 2 public IPv4 (one per AZ; belief from AWS docs behaviour, not re-fetched this run). Nodes in public subnets: 2. Total 4 addresses x $0.005 = $0.02/h. VPC pricing page lists Amazon EKS among services creating VPC resources with public IPv4, but gives no EKS-specific charge; I found no evidence that control-plane ENIs add billed public IPs in the customer account (cross-account ENIs are private IPs; unverified belief).
- Env EBS: 2x30 GB node + 2x20 GB DB = 100 GB, billed only while volumes exist (assumes DB volumes deleted at teardown with data restored from S3 backup). If DB volumes persist all month: +$3.20/mo (40 GB x 0.08), which is a persistent cost not in the env line.
- LCU: 0.5 LCU avg at demo traffic (assumption).
- Data transfer: ~1 GB out at $0.09/GB is the high case ($0.09); ECR pulls in-region assumed free; internet-egress free allowance not verified this run. Not priced from a source, so treated as <= $0.10.
- ECR 3 GB stored = $0.30 (assumption). S3: 1 GB DB x 4 weekly backups retained = 4 GB x 0.023 = $0.09; requests negligible (<$0.01).
- CloudWatch/KMS/Secrets Manager: zero if EKS control-plane logging is off and default AWS-managed keys are used; prices not retrieved (CloudWatch log ingestion unpriced here: leads not chased).
- ACM public certificate: free (belief, not re-verified). GitHub OIDC provider/role: no charge (belief).

## Arithmetic (python3 -I /tmp/calc.py output, abridged)
Per env-hour fixed (excl. nodes) = 0.10 + 0.0225 + 0.004 (LCU 0.5) + 4x0.005 + 100GBx0.08/730 = $0.1575/h.
Env cost = H x (0.1575 + 2 x node rate):
```
t4g.medium H=25 : cp 2.50 nodes 1.68 ebs 0.27 alb 0.56 lcu 0.10 ip 0.50 = 5.62 ; H=24: 5.39 ; H=730: 164.00
t4g.large  H=25 : cp 2.50 nodes 3.36 ebs 0.27 alb 0.56 lcu 0.10 ip 0.50 = 7.30 ; H=24: 7.00 ; H=730: 213.06
m7g.large  H=25 : cp 2.50 nodes 4.08 ebs 0.27 alb 0.56 lcu 0.10 ip 0.50 = 8.02 ; H=24: 7.70 ; H=730: 234.08
spot (H=25): t4g.medium 4.76 ; t4g.large 6.76 ; m7g.large 5.94
persistent: zone 0.50 + S3 0.09 + ECR 0.30 + domain/12 -> .com 1.33 => 2.23 ; .click 0.25 => 1.14 ; .link 0.42 ; .net 1.42
likely totals 25h + persistent(.com): t4g.medium 7.84 ; t4g.large 9.52 ; m7g.large 10.24   (.click: 6.76 / 8.44 / 9.16)
```

## Monthly table (25 h, node = 2x t4g.medium unless stated)
| Line | Low | Likely | High |
|---|---|---|---|
| EKS control plane (25h x 0.10) | 2.50 | 2.50 | 2.50 (12.50 if extended support; not applicable to 1.36) |
| 2 nodes (spot / t4g.medium OD / m7g.large OD) | 0.82 | 1.68 | 4.08 |
| EBS 100 GB, 25h | 0.27 | 0.27 | 0.27 (3.20 + 0.27 if DB vols kept all month) |
| ALB hours | 0.56 | 0.56 | 0.56 |
| ALB LCU | 0.05 | 0.10 | 0.20 |
| Public IPv4 x4 | 0.50 | 0.50 | 0.50 |
| Data transfer | 0 | 0.05 | 0.10 |
| ECR | 0.10 | 0.30 | 0.50 |
| S3 | 0.05 | 0.09 | 0.15 |
| Route 53 zone | 0.50 | 0.50 | 0.50 |
| Domain amortised (.click / .com / .net) | 0.25 | 1.33 | 1.42 |
| Total | ~5.5 | ~7.9 | ~11.9 |

By node choice (likely, .com): t4g.medium $7.84, t4g.large $9.52, m7g.large $10.24.

Persistent only (zone + S3 + ECR + .com): ~$2.23/mo; per-env-hour (t4g.medium): $0.1575 + 0.0672 = $0.2247/h; (t4g.large) $0.2919/h; (m7g.large) $0.3207/h.

## Mistake scenarios (t4g.medium / t4g.large / m7g.large, incl. persistent $2.23, +24 forgotten hours on top of 25)
- Left running one extra 24h: env 11.01 / 14.30 / 15.72 -> total ~13.2 / 16.5 / 18.0. Over budget.
- One full day alone (24h env): 5.39 / 7.00 / 7.70.
- Full month 730h: env 164.00 / 213.06 / 234.08 (EKS cluster alone $73).
Break-even: t4g.medium budget exhausted at (10 - 2.23)/0.2247 = ~34.6 env-hours; t4g.large ~26.6 h; m7g.large ~24.2 h.

## Claim lines
{EKS standard-support cluster price $0.10/h us-east-1, https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEKS/current/index.json, AWS, 2026-11-11, accessed=2026-11-12, high, pricing}
{EKS extended support $0.50/h, same, AWS, 2026-11-11, accessed=2026-11-12, high, pricing}
{K8s 1.36 on EKS standard support; released 2026-06-02; standard ends 2027-08-02, https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html, AWS, undated (accessed page lists 1.37 as newest), accessed=2026-11-12, high, version}
{t4g.medium $0.0336/h, t4g.large $0.0672/h, m7g.large $0.0816/h Linux on-demand, https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/us-east-1/index.json, AWS, 2026-11-10, accessed=2026-11-12, high, pricing}
{gp3 $0.08/GB-month, same EC2 file, AWS, 2026-11-10, accessed=2026-11-12, high, pricing}
{ALB $0.0225/h, LCU $0.008/LCU-h, https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSELB/current/index.json, AWS, 2026-11-11, accessed=2026-11-12, high, pricing}
{Public IPv4 $0.005/h in-use and idle; no free tier on page; LB with 2 in-use IPs charged as 2, https://aws.amazon.com/vpc/pricing/ and AmazonVPC price list, AWS, 2026-11-05, accessed=2026-11-12, high, pricing}
{ECR $0.10/GB-month, AmazonECR price list, AWS, 2026-11-11, accessed=2026-11-12, high, pricing}
{S3 Standard $0.023/GB-month; PUT $0.005/1k; GET $0.004/10k, AmazonS3 price list, AWS, 2026-11-09, accessed=2026-11-12, high, pricing}
{Route 53 hosted zone $0.50/month, not prorated, https://aws.amazon.com/route53/pricing/, AWS, undated, accessed=2026-11-12, high, pricing}
{.com $16 reg and renew from 2026-07-01 (was $15), https://dev.classmethod.jp/en/articles/route53-tld-pricing-change-2026/, Classmethod (quotes AWS PDF), 2026, accessed=2026-11-12, medium, pricing}
{.click $3, .link $5, .net $17, .dev $17, .xyz $19, .cloud $26, reg = renew, https://costgoat.com/pricing/route-53-domains, CostGoat, 2026-10-20, accessed=2026-11-12, medium-low (single secondary source), pricing}
{Spot t4g.medium ~$0.016/h, t4g.large ~$0.057/h, m7g.large ~$0.03-0.06/h, aggregator pages (doit.com, holori) via web search, mixed dates, accessed=2026-11-12, low, pricing}

## Contradictions
- Domain prices: one search summary said .com $15, others $16 after 2026-07-01; resolved to $16 (two secondary sources agree on the change). The AWS price list PDF itself could not be parsed (compressed, no text tools), so no primary confirmation. Renewal = registration for all TLDs seen (no divergence found, but only secondary sources).
- Spot aggregators contradict each other (t4g.medium avg 0.0164 vs zone up to 0.0263; m7g.large 0.0265-0.0397 vs 0.0402-0.0605). Spot is therefore a range, not a fact.
- Contradicts a "cheap" assumption: m7g.large on-demand does not fit; any 24h mistake breaks the budget for all sizes.

## Leads not chased
- DescribeSpotPriceHistory via AWS CLI (needs credentials) for real spot prices; EC2 spot advisor JSON.
- Route 53 GetDomainPrices API for primary domain prices.
- CloudWatch Logs ingestion, KMS ($1/key-month for customer keys), Secrets Manager ($0.40/secret-month) prices from price lists; EKS control-plane logging cost.
- Internet egress free allowance (100 GB/month) and cross-AZ transfer charges (2-AZ ALB to nodes); NAT-less design means no NAT cost.
- EBS volumes orphaned by PVCs on teardown; ALB created by LB controller orphaned on destroy; ACM/OIDC being free; GitHub Actions minutes.
- Whether EKS control-plane ENIs create billable public IPv4 in the customer account.
- Savings from 1.37 vs 1.36 (none expected).

## Looked for but could not find
- Machine-readable Route 53 TLD price list from AWS (PDF text not extractable with available tools; the per-TLD docs pages carry no prices).
- Current primary spot prices.
- EKS-specific public IPv4 charge statement.
- A free-tier statement for EKS control plane (none seen; $0.10/h billed from the first hour).
- Note: Auto Mode price list entries ($/h management fee per instance) exist but Auto Mode is out of scope.
