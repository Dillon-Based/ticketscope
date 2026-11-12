# Digest q2-account-r1-1: "A brand-new AWS account can run EKS inside the monthly budget"

Accessed 2026-11-12 for all lines. Rounds 1+2 merged, by sub-question. Fields: claim | URL | publisher | pub_date | confidence | class.
pub_date "n/a" = page undated in fetch result (live docs).

## Q1 Plans (free vs paid)

- New accounts choose Free plan or Paid plan at sign-up; $100 credit on signup either way, up to $100 more via activities. | https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html | AWS Billing User Guide | n/a | high | plan
- Free plan ends at 6 months or when credits are used up, whichever first. After that the account is closed and access lost; AWS keeps content 90 days; upgrade to Paid within 90 days to recover. Remaining credits then apply to future bills. | same URL | AWS | n/a | high | plan
- Free plan excludes services that could deplete credits (Savings Plans, RIs, some Marketplace offers); not eligible for other promo credits. Auto-upgrades to Paid on joining AWS Organizations, Control Tower, etc. (so Organizations/Control Tower is not a free-plan option). | same URL; https://aws.amazon.com/free/terms/ | AWS | n/a | high | plan
- Services supported on the Free plan in the "new AWS experience" sign-up include Amazon EKS, EC2 (not Capacity Blocks), Elastic Load Balancing, Route 53, VPC, EBS, CloudWatch, Budgets, Service Quotas. Multi-region/cross-region features not supported. Unsupported: Organizations, Transit Gateway, Control Tower, Shield etc. (need "advanced" sign-up). | https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html | AWS Accounts reference | n/a | high | plan
- The Free-plan SCP allows eks:*, elasticloadbalancing:*, route53:*, route53domains:* and denies: Spot requests, EC2 Fleet, dedicated host tenancy, instance-store-root instances, RIs/capacity purchases, NAT-less items like TGW/VPN. No instance-type or size restriction seen in the grep I ran (I grepped for InstanceType; no hit). | https://docs.aws.amazon.com/accounts/latest/reference/scps-and-rcps-for-projects.html | AWS | n/a | med (grepped saved copy, did not read every line) | plan
- Paid plan: all services, standard pay-as-you-go beyond credits; account not closed when credits deplete. | free-tier-plans.html | AWS | n/a | high | plan
- Free plan resources unused for 3 months may be reclaimed after 30 days' notice; plan "not for sensitive data". | https://aws.amazon.com/free/terms/ | AWS | n/a | med | plan
- Builder Center article (AWS-hosted) says a sample guardrail policy (user-built, not default) blocks EKS/ELB/EIP/NAT launches; NOT a default plan restriction. | https://builder.aws.com/content/3Kkt4kNiDSUnO3n6db2weSNubzE/the-dollar0-aws-account-in-2026-free-plan-credits-guardrails | AWS Builder Center | 2026-10-18 (mod 2026-11-11) | med | plan
- Note: the "Free plan supported services" list is for "Sign up for AWS (new)". The classic/advanced sign-up path was not separately verified. | gap | - | - | - | plan

## Q2 Credits

- Credit size $100 + up to $100 via activities (total up to $200). | free-tier-plans.html; https://aws.amazon.com/about-aws/whats-new/2025/07/aws-free-tier-credits-month-free-plan | AWS | 2025-07 | high | credit
- Credits apply to participating services in all global regions, applied automatically monthly; not in China/GovCloud (mostly). | https://aws.amazon.com/free/faqs/ | AWS | n/a | high | credit
- Route 53 domain REGISTRATION: "You can't use AWS credits to pay the fee for registering a new domain." (primary doc). Hosted zone/query fees: credits can absorb (re:Post answer only, med). | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-register.html | AWS | n/a | high (registration) / low (hosted zone) | credit
- Domain registration non-refundable; hosted zone is auto-created and billed monthly (free if deleted within 12h of registering). | same | AWS | n/a | high | pricing
- EKS: control plane $0.10/cluster/hour standard support, $0.60 extended (after 14 months of version life). No EKS free tier mentioned. ~25h/month = ~$2.50 control plane. | https://aws.amazon.com/eks/pricing/ | AWS | n/a | high | pricing
- Public IPv4: $0.005/hr in-use and idle; no free-tier waiver stated on VPC pricing page. (ALB uses >=2 public IPv4 in 2 AZs; I did not verify ALB per-IP count this run.) | https://aws.amazon.com/vpc/pricing/ | AWS | n/a | med | pricing
- Credit-applicability to EKS, EC2, ELB, hosted zones, public IPv4: no AWS page fetched says they are excluded; no page lists eligible services explicitly. Repost answer (community) says EKS control plane/nodes/LBs/storage are covered. | https://repost.aws/questions/QUQ... (search snippet only; page 403) | re:Post | n/a | low | credit
- Marketplace: Free plan allows "Bedrock and Free only" Marketplace offers. | supported-services page | AWS | n/a | high | plan
- End of credits/period: Free plan -> account closed (see Q1). Paid plan -> pay standard rates.

## Q3 Budgets

- AWS Budgets is in the Free plan supported list; also Billing/Cost Explorer. | supported-services-sign-up-new.html | AWS | n/a | high | plan
- Budget monitoring/notifications free; first 2 action-enabled budgets/month free, then $0.10/day each. | https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/ | AWS | n/a | high | pricing
- Budgets data refresh up to 3x/day (8-12h apart); spend can exceed threshold before alert/action. Budget actions can apply IAM deny policy; running resources keep billing. | https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html | AWS | n/a | high | other
- Budgets treats credits as negative cost by default (a zero-spend budget can stay quiet while credits pay) unless credits excluded. | Builder Center article above | AWS | 2026-10-18 | med | other
- Spend limits (min $20/month, optional SCP) apply only after upgrade to Paid; not available to all accounts yet. | https://aws.amazon.com/free/faqs/ ; Builder article | AWS | n/a | med | plan
- Not verified: whether budget actions work identically on Free plan (the 'projects' SCPs are AWS-managed and might block IAM role policy attach on "managed/" roles). Unconfirmed.

## Q4 Quotas

- Default Running On-Demand Standard (A,C,D,H,I,M,R,T,Z) instances = 5 vCPUs (quota L-1216C47A), adjustable. EC2 auto-raises quotas based on usage. Pending/stopped instances don't count. | https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html ; https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-on-demand-instances.html | AWS | n/a | high | quota
- Implication: 2 x t4g.medium (2 vCPU) or 2 x m7g.large (2 vCPU) = 4 vCPU fits; 2 x m7g.xlarge (4 vCPU) = 8 does NOT; a third 2-vCPU node or surge during rolling node upgrade (6 vCPU) would fail. Graviton uses the Standard quota (no separate Graviton quota). Derived by me. | derived | - | - | med | quota
- Elastic IPs per region default 5; VPCs 5; NAT gateways 5/AZ. | https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html | AWS | n/a | high | quota
- Application Load Balancers per region default 50. | https://docs.aws.amazon.com/general/latest/gr/elb.html | AWS | n/a | high | quota
- Increase: Service Quotas console; small increases usually auto-approved, larger go to Support; no priority support; can be denied. No stated SLA. | https://docs.aws.amazon.com/servicequotas/latest/userguide/request-quota-increase.html | AWS | n/a | high | quota
- Service Quotas is available on Free plan. Whether Free-plan accounts get lower quotas than Paid: NOT documented; community report of 5 vCPU and one India account with 1 vCPU unable to launch t3.micro. | https://repost.aws/questions/QUtZw68fatTCeMgiPqYfGzgw/ (search snippet; page 403) | re:Post | undated | low | anecdote

## Q5 Verification delays (anecdotal, supporting only)

- AWS says new-account activation can take up to 24h (some messages say up to 2 days); check email/spam for info requests; escalate via Support case "Account Activation". | search results incl. https://repost.aws/knowledge-center/create-and-activate-aws-account | AWS re:Post | n/a | med | other
- Users report 5-9+ day stalls: verification stuck 5 days blocking CloudShell and Route 53 domain purchase; Bedrock "not authorized" 9 days; accounts "incomplete" 48h-5 days. Pages 403 on fetch, so content seen only via search snippets. | https://www.repost.aws/questions/QU9D6D6-1WRxG6YvJdpI2YXQ/... ; https://repost.aws/questions/QU_BWOWZGWSmi3ms_UqD1PKQ/... | re:Post | 2026 (per search tool) | low | anecdote
- Responder note: new accounts can have service-specific restrictions lifted after the account is active for some period. | re:Post (snippet) | - | - | low | anecdote
- Route 53 registrant email verification required or domain suspended (ICANN). Do not use a Route 53 domain as root email for the same account. | domain-register.html | AWS | n/a | high | other

## Contradictions

1. Credit expiry: Free Tier FAQ says signup credits expire 6 months after account creation (and 12 months after upgrade/for activity credits); Terms and a different FAQ answer say 12 months; Builder Center article explicitly notes AWS pages disagree. Plan for 6.
2. "No charges incur on Free plan" vs "credits can't pay domain registration": registration fee (~$ per year, TLD-dependent, not fetched) must be paid by card. Whether the Free plan permits a card-paid registration without upgrade is not documented; the SCP allows route53domains:* so probably yes, unverified.
3. Search summary claimed "AWS guardrail policies may block EKS launches on new accounts"; the primary docs show eks:* ALLOWED on Free plan. The block was a user-added sample policy. Primary docs win.
4. Old sources cite 1,152 vCPU default; current AWS docs say 5.
5. Free plan "account closes at end of plan" conflicts with a demo meant to persist: a Free-plan account vanishes after 6 months unless upgraded (within 90 days).

## Leads not chased

- Classic ("advanced") sign-up: whether it also yields Free/Paid plan and different service access.
- Whether Free plan can create EKS clusters in practice (docs say yes; no hands-on report found). Also AL2023 Graviton AMI/EKS add-ons costs, NAT gateway need (EKS nodes in public subnets avoid NAT; ~$0.045/hr otherwise).
- ALB hourly/LCU price and public IPv4 count; Route 53 hosted zone price ($0.50/mo, unverified this run); domain price per TLD.
- Whether Budgets actions are blocked by managed SCP on Free plan; Free-plan sensitive "3 months unused reclaim".
- Auto quota increase timing (typical hours-days; no AWS SLA found).
- Support plan availability on Free plan (AWS Support is listed; Basic only presumably).

## Looked for but could not find

- Official statement on quota defaults differing between Free and Paid plans.
- Explicit AWS list of services/line items credits do NOT cover (beyond domain registration, Marketplace non-free, RIs/Savings Plans).
- Any AWS-published quota-increase turnaround time.
- Any dated (<=12 months) credible report of verification delays that I could read in full (re:Post returned 403; only snippets).
- Any first-hand report of running EKS on a Free-plan account.

---
# Round 2 (account-plan question; accessed 2026-11-12; none of the fetched AWS pages show a last-updated date, only live-doc state)

## R2-1 Plan lifetime and closure (two independent AWS pages agree)
- "After your free account plan expires, your account closes automatically, and you lose access to your resources and data. AWS retains your content for 90 days before permanently deleting your account and all associated resources. To maintain your account access, you can upgrade to a **Paid account plan** ... within 90 days. Any remaining credits from your free account plan are automatically applied to future AWS bills." | https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html | AWS Billing User Guide | undated | high | plan
- "If you don't upgrade your account within 90 days, AWS will permanently erase your AWS account and all its content." and "AWS will retain your data for 90 days after your Free plan expires." (FAQ also says AWS "suspends" the account and projects.) | https://aws.amazon.com/free/faqs/ | AWS Free Tier FAQ | undated (c) 2026 | high | plan
- Third page: "When you either run out of credits or have an account that is over 6 months, you must upgrade to a Paid Plan." | https://docs.aws.amazon.com/accounts/latest/reference/upgrade-account.html | AWS Accounts Reference | undated | high | plan
- Verdict: closure/suspension, NOT auto-conversion. Upgrade is manual and must happen within 90 days. Wording differs: billing guide says "closes... lose access"; FAQ says "suspends". Data is retained 90 days then permanently erased.
- Free-plan comparison table: "Account closes when credits are depleted or when the plan duration ends" vs Paid "Account doesn't close when credits are depleted". (free-tier-plans.html)

## R2-2 Credit expiry 6 vs 12 months (unresolved by AWS; quoted per page)
- aws.amazon.com/free/faqs (General FAQ): "Free Tier credits expire 6 months from the date you create your AWS account."
- Same page (Paid Plan FAQ): "Free Tier credits expire 12 months after you create your account." and activity credits expire 12 months after account creation.
- https://aws.amazon.com/free/terms/ : "Free Tier Credits expire twelve months after you open the account." (round 1) while also "A Free Plan account expires six months after opening or when Free Tier Credits are exhausted".
- Reconciliation that fits all pages (my inference, med): on the Free plan the account itself ends at 6 months regardless, so Free-plan credits are effectively usable only for 6 months; after upgrading to Paid, unspent credits live to the 12-month mark. The FAQ line "Free Tier credits expire 6 months" is the conservative reading. Quoted line from FAQ: "your remaining Free Tier credits will automatically apply to future AWS bills until they expire."
- Dates: no last-updated date on any of these pages; confidence that 12 months is a Paid-plan outcome: med.

## R2-3 Route 53 domain on a Free-plan account
- Free-plan supported list includes "Amazon Route 53"; Free-plan SCP allows route53domains:*. (supported-services-sign-up-new.html; scps-and-rcps-for-projects.html) | high that it is not blocked by plan
- "You can't use AWS credits to pay the fee for registering a new domain with Route 53." | domain-register.html | high
- Free-plan page: "The Free account plan ensures you won't incur any charges..." -> unreconciled with a card-paid registration fee. No AWS page says how a Free-plan account pays for registration. Search summary: Route 53 domain agreement says a registration "will not be effective unless and until payment to AWS is final" (https://aws.amazon.com/route53/domain-registration-agreement/, snippet only, med-low); community re:Post says card on file required (low). Upgrade flow page says "Add your payment method" is part of upgrading (upgrade-account.html), implying a Free-plan account may not have a payment method until upgrade (inference, low). Practical implication: domain registration probably needs a payment method; may force upgrade to Paid. UNVERIFIED.
- NEW: In the "new experience" sign-up, there is no root user (Builder ID owns projects) and "Use AWS Marketplace: No" (Compare table) vs supported-services "Marketplace: Bedrock and Free only" - minor inconsistency. | https://docs.aws.amazon.com/accounts/latest/reference/sign-up-for-aws.html
- Domain registrant email verification required or domain suspended; do not use a Route 53 domain as root email of same account. (domain-register.html)

## R2-4 Quotas on Free/new accounts; increase turnaround
- No AWS doc found stating lower quotas for Free-plan vs Paid. Documented default Standard on-demand = 5 vCPU for all accounts (round 1). "Amazon EC2 automatically increases your On-Demand Instance quotas based on your usage."
- Turnaround: "Smaller increases are usually automatically approved while larger requests are submitted to Support. Larger increase requests take time to review, process, approve, and deploy... Quota increase requests don't receive priority support. Support can approve, deny, or partially approve your requests." (https://docs.aws.amazon.com/servicequotas/latest/userguide/request-quota-increase.html). No numeric SLA anywhere. | high | quota
- Note: Free-plan "projects" are AWS-managed organizations; Service Quotas is on the supported list. Region is NOT selectable (see below).
- BIG NEW FINDING (Region lock): for "Sign up for AWS (new)", "AWS assigns it to a Region - US East (Ohio) (us-east-2), Europe (Stockholm) (eu-north-1), or Asia Pacific (Sydney) (ap-southeast-2) - based on the country in your contact address". Changing contact info doesn't change it; "If you need to access a specific Region, use Sign up for AWS (advanced)" or activate advanced features. | https://docs.aws.amazon.com/accounts/latest/reference/project-regions.html | high | plan. Also "Multi-Region or cross-Region features are not supported". Effect: EKS/Graviton must run in the assigned Region (not verified that EKS/t4g/m7g exist there; those Regions are large, so likely fine). Route 53 is global so unaffected.

## R2-5 Upgrade to Paid
- "You can also upgrade to a Paid Plan at any time." Procedure: Settings > Billing > Upgrade > Get started > "Add your payment method" > "Upgrade account" ... "Your upgrade is complete." | upgrade-account.html | high | plan
- "Paid account plan to access all AWS services and features immediately." | free-tier-plans.html | high
- Effects: remaining credits stay ("Any remaining credits from your free account plan are automatically applied to future AWS bills" / "until they expire"); eligible for other promotional credits; must pay charges beyond credits; account doesn't close when credits deplete; spend limits (min $20) become available; "You cannot reverse the upgrade process."; all projects upgrade together; does not convert to "advanced" sign-up. | upgrade-account.html; free-tier-plans.html | high
- Not stated: whether upgrade changes credit expiry date (FAQ implies 12 months post-upgrade).

## Round 2 contradictions / open
- 6 vs 12 month credit expiry: unresolved on AWS pages (see R2-2).
- "closes" vs "suspends" wording at Free plan end.
- Marketplace: "No" (compare table) vs "Bedrock and Free only" (supported list).
- Free plan "no charges" vs card-paid domain fee: no AWS statement.
## Round 2 not found
- Any AWS page stating how a Free-plan account pays Route 53 registration; any last-updated date on these pages; any documented Free-vs-Paid quota difference; numeric quota-increase SLA.
