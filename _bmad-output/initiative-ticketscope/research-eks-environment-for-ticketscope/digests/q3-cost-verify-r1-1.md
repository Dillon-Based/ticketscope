# q3 cost verify r1-1 (accessed=2026-11-12)
Format: claim | source | publisher | pub_date | status

1. EKS std $0.10/cluster-h; extended $0.50 | https://aws.amazon.com/eks/pricing/ | AWS | undated (c) 2026 | confirmed. Page: "$0.10 per cluster per hour"; extended "$0.60 ... (Standard + $0.50)" i.e. $0.50 is the surcharge, total $0.60.
2. t4g.medium $0.0336, t4g.large $0.0672, m7g.large $0.0816 | https://instances.vantage.sh/aws/ec2/{type}?region=us-east-1 | Vantage (third party; AWS on-demand page was dynamic, no rates) | live 2026-11-12 | confirmed (third party, region label not explicit on fetch)
3. gp3 $0.08/GB-mo | https://aws.amazon.com/ebs/pricing/ | AWS | undated | unverified (page only shows $0.08 as hypothetical example)
4. ALB $0.0225/h + $0.008/LCU-h | https://aws.amazon.com/elasticloadbalancing/pricing/ | AWS | undated | confirmed (us-east-1 examples)
5. Public IPv4 $0.005/h in-use (idle also $0.005) | https://aws.amazon.com/vpc/pricing/ | AWS | undated | confirmed. ALB: ELB page says standard IPv4 charges apply to all addresses consumed by load balancers; VPC page example "one load balancer with two in-use public IPv4 addresses" (per-AZ implied, not stated).
6. Route 53 hosted zone $0.50/mo | https://aws.amazon.com/route53/pricing/ | AWS | undated | confirmed ($0.50 first 25 zones, $0.10 after)
7a. .com $16 reg/renew from 2026-07-01 (was $15) | https://dev.classmethod.jp/en/articles/route53-tld-pricing-change-2026/ | Classmethod DevelopersIO, citing AWS TLD pricing PDF | 2026-06-09 | confirmed $16 (secondary); AWS PDF text not extractable (obfuscated fonts, no pdftotext) -> primary unverified
7b. .org $15->$16; .net $17; .dev $17 (unchanged) | same | same | 2026-06-09 | confirmed (secondary)
7c. .click, .link | web search snippet only: .click ~$3, .link ~$5 (pre-July, stale 2024 sources); not covered by Classmethod | unverified post-July 2026. Cheapest in Classmethod list: .work $12->$14; the $13 group jumps to $36-$60 from July 2026. Renewal assumed = registration (not shown separately).
8. Spot us-east-1 | instances.vantage.sh pages, 2026-11-12 | Vantage | live | t4g.medium ~$0.017, t4g.large ~$0.027, m7g.large ~$0.053 per h (approx, region label unconfirmed; not from AWS Spot Advisor)
9. Other EKS charges | https://aws.amazon.com/eks/pricing/ | AWS | undated | none beyond: IPv4 via VPC page; no ENI charge listed; Hybrid Nodes $0.020/vCPU-h (tiered); Provisioned Control Plane XL $1.65/h, 2XL $3.40, 4XL $6.90, 8XL $13.90 (add-on to $0.10; optional). None apply to a basic cluster.
