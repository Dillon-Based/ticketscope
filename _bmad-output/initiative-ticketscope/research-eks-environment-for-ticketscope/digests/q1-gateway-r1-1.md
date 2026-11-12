# Digest q1: Gateway API on AWS Load Balancer Controller (rounds 1+2)
Format: {claim | source | publisher | pub_date | accessed=2026-11-12 | confidence | class}
Note: tool-summarized fetches (small model); release page dates have no year (inferred 2026 from sequence).

## Versions (actual current)
- LBC latest is v3.6.2 (25 Oct), v3.6.1 (21 Oct), v3.6.0 (05 Oct). Author's "3.6" is fine. | https://github.com/kubernetes-sigs/aws-load-balancer-controller/releases | kubernetes-sigs | 2026-10 | high | version
- external-dns latest is v0.24.0 (23 Oct). Matches author's 0.24. | https://github.com/kubernetes-sigs/external-dns/releases | kubernetes-sigs | 2026-10 | high | version
- EKS/K8s 1.36 not verified this run. | - | - | - | - | - | version

## Q1 GA, CRDs, install
- AWS announced GA of Gateway API support (post dated 2026-03-06); article gives no version; a search snippet says GA since v3.0.0 (single secondary source, low). | https://aws.amazon.com/blogs/networking-and-content-delivery/aws-load-balancer-controller-adds-general-availability-support-for-kubernetes-gateway-api | AWS | 2026-03-06 | med | version
- Docs: needs LBC >= v2.13.0 for NLB; ALB HTTPRoute/GRPCRoute from v2.14.0. Docs page itself states no GA/beta label. | https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/gateway/gateway/ | kubernetes-sigs | current | med | version
- CRDs: standard-channel Gateway API v1.6.0 (v3.5.0-v3.6.2 need 1.6.0; v3.3.0 needed 1.5.0) PLUS LBC's own CRDs (gateway-crds.yaml: TargetGroupConfiguration, LoadBalancerConfiguration, ListenerRuleConfiguration). ALB needs only standard channel (Gateway, GatewayClass, HTTPRoute, GRPCRoute). | docs page above + releases page | kubernetes-sigs | 2026 | high | version
- Install steps: server-side apply standard v1.6.0 CRDs, apply gateway-crds.yaml, then install controller. Controllers auto-enable when CRDs detected; disable via --feature-gates=ALBGatewayAPI=false,NLBGatewayAPI=false. Helm chart does not install Gateway API CRDs (open request #4651). | docs page; https://github.com/kubernetes-sigs/aws-load-balancer-controller/issues?q=is%3Aissue%20is%3Aopen%20gateway | kubernetes-sigs | 2026 | med | behavior
- Mixing L4 and L7 routes on one Gateway unsupported. | docs page | kubernetes-sigs | current | high | behavior
- Controller upgraded before CRDs: NLB route kinds auto-disabled (v3.5.0 note). | releases | kubernetes-sigs | 2026-08 | med | behavior

## Q2 Single Gateway -> one ALB, routing
- Each Gateway using the ALB GatewayClass provisions one ALB. HTTPRoute supports path, header, query, method matches; hostnames, parentRefs, backendRefs; filters RequestRedirect (ReplacePrefixMatch redirect loops, use ReplaceFullPath), UrlRewrite, ExtensionRef; partial RequestHeaderModifier. | https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/gateway/l7gateway/ | kubernetes-sigs | current | med | behavior
- Unsupported: ResponseHeaderModifier, RequestMirror, CORS, ExternalAuth (use ListenerRuleConfiguration), timeouts, retries, session persistence (via LRC), backend TLS, UseDefaultGateways. | same | kubernetes-sigs | current | med | behavior
- If one rule in an HTTPRoute fails (e.g. invalid redirect), controller stops creating later rules for that route. | same | kubernetes-sigs | current | med | behavior
- Missing backend Service yields a 500 fixed-response rule. | gateway docs page | kubernetes-sigs | current | med | behavior
- Docs summary did not explicitly confirm PathPrefix vs Exact per-type support; "HTTPPathMatch supported" only. Two HTTPRoutes to two Services on one Gateway is the standard pattern but not explicitly evidenced beyond cross-namespace routes in AWS blog. | - | - | - | low | behavior
- Open: #4884 (combine HTTP methods into one rule), #4938 (share target group per Service/port across routes), #4688 (ReplaceFullPath w/ regex), #4668 (CORS). None block the two-service path split. | issues list | kubernetes-sigs | 2026 | med | bug

## Q3 TLS
- ACM cert is attached via LoadBalancerConfiguration (defaultCertificate ARN, or certificates list). Listener certificateRefs / TLS options are NOT supported ("Use LB Config"). | https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/gateway/loadbalancerconfig/ and l7gateway page | kubernetes-sigs | current | med-high | behavior
- Hostname-based ACM discovery: AWS blog says controller queries ACM when hostname is set on Gateway listener or Route and attaches the matching cert; gateway docs page also says discovery works via hostname on listeners/routes. But l7gateway and loadbalancerconfig pages show only explicit ARN, and the Ingress cert_discovery page does not mention Gateway. Issue #4774 reporter says only ARN attach works, auto-create not supported; discovery for Gateway unconfirmed there. Treat discovery as claimed-but-not-demonstrated; explicit ARN in LoadBalancerConfiguration is the safe path. | https://aws.amazon.com/blogs/networking-and-content-delivery/aws-load-balancer-controller-adds-general-availability-support-for-kubernetes-gateway-api ; https://github.com/kubernetes-sigs/aws-load-balancer-controller/issues/4774 | AWS / kubernetes-sigs | 2026 | med | behavior
- create-acm-cert for Gateway not supported yet (#4774 open, PR #4949); secrets-to-ACM sync not supported (#4494). | issues | kubernetes-sigs | 2026 | med | other
- LoadBalancerConfiguration scheme DEFAULT IS internal; set internet-facing explicitly. Default sslPolicy ELBSecurityPolicy-2016-08 (open #4931 to modernize). ipAddressType default ipv4. | loadbalancerconfig page | kubernetes-sigs | current | med | behavior
- Listener-hostname-vs-route-hostname attachment/mismatch behavior: not documented in what was fetched (Gateway API spec says hostnames must intersect; not evidenced here). | - | - | - | - | behavior

## Q4 external-dns
- external-dns gateway-httproute source: targets come from parent Gateway status.addresses (IP or Hostname types only), overridden by external-dns.kubernetes.io/target annotation on the Gateway (annotation ignored on Routes). Hostnames from HTTPRoute spec.hostnames and listener hostnames. | https://raw.githubusercontent.com/kubernetes-sigs/external-dns/master/source/gateway.go ; https://kubernetes-sigs.github.io/external-dns/latest/docs/sources/gateway-api/ | kubernetes-sigs | current | high | behavior
- AWS blog says Gateway/Route status shows the provisioned ALB DNS name. Not confirmed that it lands in Gateway status.addresses as Hostname type; no source shows external-dns + LBC ALB Gateway end to end. Safe fallback: set external-dns.kubernetes.io/target annotation on Gateway to ALB hostname (but ALB name is not known until created). UNVERIFIED end-to-end. | blog above | AWS | 2026-03-06 | low | behavior
- external-dns >= 0.24.0 changes: annotation/FQDN-template hostname suppresses listener hostname fallback (#6746); with --policy=sync, previously fallback-created records get deleted (use --dry-run). Gateway/HTTPRoute at v1 since 0.21; need Gateway API CRDs >=1.0 for httproute. | https://github.com/kubernetes-sigs/external-dns/releases | kubernetes-sigs | 2026-10 | med | version
- Ownership/cleanup (TXT registry, policy upsert-only vs sync on Gateway deletion): not researched this run.

## Q5 Teardown
- No Gateway-API-specific teardown leak bug found for LBC. #3592 (NLB/SG left behind after Gateway deletion) was blamed on Envoy Gateway (not LBC), closed 2024-06-25, recurrence reported 2025-01; Cilium similar. Not applicable to LBC ALB gateway. | https://github.com/kubernetes-sigs/aws-load-balancer-controller/issues/3592 | kubernetes-sigs | 2024-02 / 2025-01 | med | bug
- Open #4652: security group leakage when manage-backend-security-group-rules=false (opened 2026-03-30; relation to Gateway not shown). Relevant only if that flag is set. | issues list | kubernetes-sigs | 2026-03 | low | bug
- General pattern (forum/issues, not Gateway-specific): delete Gateway/Ingress first while controller still running; controller removes finalizers only after AWS cleanup; uninstalling controller first leaves stuck finalizers and orphan ALB/SG/ENIs. PR #4217 adds finalizers to LoadBalancerConfiguration (merge status not checked). Ordering: delete routes+Gateway, wait ALB gone, then uninstall controller, then cluster. | search results (various) | mixed | various | low-med | behavior

## Q6 Targets
- TargetGroupConfiguration: targetType default "auto-inferred as instance" (controller flag --default-target-type; Gateway-level default TGC can override); ip type registers pods, requires VPC CNI. Health check via healthCheckConfig (path, port, protocol, matcher, thresholds); Service-level TGC healthCheckConfig replaces default block wholesale. Docs: with instance, target group holds nodes at NodePort (Services need NodePort/LB-able type). | https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/gateway/targetgroupconfig/ | kubernetes-sigs | current | med | behavior
- Readiness gates for Gateway: not found in docs fetched.

## Q7 Bugs
- #4855 open: ALBGatewayAPI crash-loop on huge clusters (12k Services), v3.4.2; irrelevant for a 2-node demo. | https://github.com/kubernetes-sigs/aws-load-balancer-controller/issues/4855 | kubernetes-sigs | 2026-07 | high | bug
- v3.4.1 known vulnerability; v3.4.2 security fix on cross-kind route precedence; current 3.6.2 is past both. | releases | kubernetes-sigs | 2026-07 | med | bug
- #4740 open: target groups recreated when TGC defaultConfiguration changes. #4699: failed upgrade 3.0 to 3.2. #4753: LoadBalancerConfiguration lacks spec.vpcId. | issues list | kubernetes-sigs | 2026 | low-med | bug

## Contradictions
- Cert-by-hostname: AWS blog and gateway docs page say ACM discovery via listener/route hostname; l7gateway/loadbalancerconfig docs show only explicit ARN, listener certificateRefs unsupported. Resolve in design by using explicit ARN in LoadBalancerConfiguration.
- Older kgateway/Solo.io docs (1.18+) say LBC creates ALBs only via Ingress; superseded by GA (those are third-party and outdated).
- Default scheme is internal: Gateway without internet-facing config yields an unreachable ALB (public-subnet-only design needs explicit scheme and subnet config).
- Assumption partially contradicted: no Gateway-level auto-cert creation, no CORS/timeouts/retries/response header filters.

## Leads not chased
- Whether Gateway status.addresses is populated with ALB hostname type (read LBC gateway status code).
- external-dns TXT registry / --policy behavior on Gateway deletion; Route53 alias vs CNAME for hostname targets (external-dns auto-aliases ELB hostnames).
- PathPrefix vs Exact exact support; matching with listener hostname mismatch.
- Readiness gate / ip-mode deregistration delay with Gateway; PR #4217 merge state; #4652 detail; issues page 2 (30 results).
- EKS 1.36 compatibility of LBC 3.6.2 / IAM policy updates.

## Looked for but could not find
- Any open or closed LBC issue about Gateway deletion leaving ALB/target groups/SG/ENIs.
- Any end-to-end doc of external-dns + LBC ALB Gateway.
- Docs on readiness gates and deletion/finalizer behavior for Gateway.
- Explicit GA version statement (blog gives date only).

# Round 2 (accessed=2026-11-12; sources are controller repo docs/source and issues, via summarizing fetches)

## R2-1 ACM cert by listener hostname (RESOLVES the contradiction)
- Source pkg/gateway/model/model_build_listener.go: certs only for HTTPS/TLS listeners. Explicit ARNs (LoadBalancerConfiguration defaultCertificate, then certificates[]) collected first; hostname discovery runs ONLY if no explicit cert exists; explicit and discovered are never merged. Discovery uses certDiscovery.Discover on the listener hostname plus attached-route compatible hostnames (falls back to route hostnames). No hostnames at all -> listener build error "No hostnames found for TLS cert discovery". Empty discovery result = empty cert list with no error (HTTPS listener with no cert). | https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/pkg/gateway/model/model_build_listener.go | kubernetes-sigs | main as of 2026-11 | high-med | behavior
- Docs gateway.md quote: "Both L4 and L7 Gateway implementations support static certificate configuration and certificate discovery ... using the hostname field on the Gateway listener and attached routes"; certificateRefs cannot be used. | https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/guide/gateway/gateway.md | kubernetes-sigs | 2026 | high | behavior
- Reconciled: both AWS blog and docs are right; discovery works for Gateway (code), explicit ARN is the alternative. The LB-config/l7 pages simply do not document discovery. #4774 reporter only said auto-CREATE of certs is unsupported. Design implication: set a hostname on the HTTPS listener (an existing ACM cert matching it, wildcard OK per Ingress discovery doc) or give an explicit ARN. Caveat: no-match yields silent cert-less listener (code reading, not tested).

## R2-2 status.addresses and external-dns
- gateway_controller.go updateGatewayStatusSuccess writes the ALB DNS name (lowercased) into Gateway status.addresses (a single address). So the controller DOES populate it. | https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/controllers/gateway/gateway_controller.go | kubernetes-sigs | main | high | behavior
- Not shown: the address type field (Hostname vs unset). external-dns skips types other than IP/Hostname and treats unset as IPAddress (round 1 gateway.go); if LBC leaves type unset, external-dns would treat an ALB hostname as an IP. UNVERIFIED; fallback is external-dns.kubernetes.io/target annotation on the Gateway. | - | - | - | low | behavior
- Issue LBC #4245 (closed 2025-06-26): external-dns made no records for HTTPRoutes on LBC v2.13.2/EKS 1.33 because Gateway/HTTPRoute status was not published (Accepted Unknown) and helm RBAC bug blocked patching LoadBalancerConfiguration; fixed in v2.13.3 + RBAC PR #4248; DNS records then created. Gateway status.addresses was already populated in the broken state, so external-dns evidently needs Accepted/parent status. Old version; fixed. | https://github.com/kubernetes-sigs/aws-load-balancer-controller/issues/4245 | kubernetes-sigs | 2025-06 | med | bug
- external-dns #4768 (Gateway API sources timing out / no records) is mostly RBAC/source-config; fix: list gateway-httproute in sources so the chart builds ClusterRole; Gateway CRDs installed but RBAC missing causes informer sync timeouts. LBC mentioned only in passing. | https://github.com/kubernetes-sigs/external-dns/issues/4768 | kubernetes-sigs | 2024-2026 | med | bug
- No external-dns doc found covering ALB-backed Gateway with LBC end to end.

## R2-3 Teardown
- Source: reconcileDelete runs deployModel with empty stack (deletes LB, TGs, SG via stack deployer), then releases backend SG, updates service refcounts, then removes the Gateway finalizer. Failure at any step keeps finalizer and retries. So controller must be running during Gateway deletion; if controller is uninstalled first the Gateway stays stuck and AWS ALB/TG/SG remain. (Order inside deployer not seen.) | controllers/gateway/gateway_controller.go URL above | kubernetes-sigs | main | med-high | behavior
- No issue found (query: gateway/httproute stuck/finalizer/leftover/not deleted; 14 results) about LBC Gateway deletion leaving AWS resources. #4024 is "Gateway pending" from v2.10.1 pre-Gateway support (closed not planned) - irrelevant. #3592 was Envoy Gateway. #4245 maintainer said a finalizer problem fixed in v2.13.3. | https://github.com/kubernetes-sigs/aws-load-balancer-controller/issues?q=is%3Aissue%20(gateway%20OR%20httproute)%20(stuck%20OR%20finalizer) | kubernetes-sigs | 2026 | med | bug
- Open #4652 (backend SG leakage when manage-backend-security-group-rules=false): leave that flag at default. | round 1 | low | bug

## R2-4 HTTPRoute fields (docs l7gateway.md table, verbatim statuses)
- Supported: ParentRefs, Hostnames, rule SectionName, PathMatch/HeaderMatch/QueryParamMatch/Method, RequestRedirect (ReplacePrefixMatch limitation), UrlRewrite, ExtensionRef, BackendRef. Unsupported: UseDefaultGateways, ResponseHeaderModifier, RequestMirror, CORS, ExternalAuth (use ListenerRuleConfiguration), Timeouts, Retry, SessionPersistence (use LRC). RequestHeaderModifier limited. | https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/guide/gateway/l7gateway.md | kubernetes-sigs | 2026 | high | behavior
- Docs do not name Exact vs PathPrefix; only examples with PathPrefix. Exact vs PathPrefix translation not confirmed (source file path guessed returned 404). Unverified. Docs say wildcard/regex path (#4688 regex open). | - | low | behavior

## R2-5 K8s/EKS 1.36
- installation.md matrix lists only "v2.5.0 and later: Kubernetes 1.22 or newer"; no 1.36 mention, no upper bound, not updated for 3.x. Docs confer neither support nor incompatibility. Evidence of recent EKS use: #4245 reporter on EKS 1.33. | https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/deploy/installation.md | kubernetes-sigs | 2026 | med | version

## Still unresolved
- Gateway status.addresses type field; Exact/PathPrefix semantics; listener-hostname vs route-hostname mismatch behavior (compat hostnames; routes with no intersecting hostname are not attached per Gateway API spec, not evidenced here); external-dns TXT/policy cleanup; readiness gates.
