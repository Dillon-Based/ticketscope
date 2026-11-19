"""EKS values and the gateway chain on offline renders (story 5.2, AD-13, AD-14, AD-25): the
EKS files hold environment facts only, the platform chart renders the HTTPS listener, the
certificate by explicit ARN, an internet-facing scheme and target type ip, and the kind
release renders as before."""

import re
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.unit.test_chart_backup import (
    _IMAGE_TAGS,
    PLATFORM,
    TICKETSCOPE,
    _docs,
    _render,
    needs_platform_deps,
)

pytestmark = pytest.mark.skipif(shutil.which("helm") is None, reason="needs helm")

CERT = "arn:aws:acm:us-east-1:000000000000:certificate/00000000-0000-0000-0000-000000000000"
HOST = "ticketscope.example.test"

# The AD-25 environment keys an EKS file may set. A key under a prefix in ENV_PREFIXES is the
# environment's own configuration of an EKS-only controller; every other key must be listed.
PLATFORM_ENV_KEYS = {
    "gateway.className",
    "gateway.controllerName",
    "gateway.tls.enabled",
    "gateway.aws.enabled",
    "envoy-gateway.enabled",
    "storageClass.create",
}
PLATFORM_ENV_PREFIXES = ("aws-load-balancer-controller.", "external-dns.")
# AD-25 names the IRSA role annotation and the instance placement rule as environment facts. No
# committed value sets them yet (the backup and placement stories do), so the names are reserved.
RESERVED_ENV_KEYS = {"database.serviceAccount.annotations", "database.instancePlacement"}
TICKETSCOPE_ENV_KEYS = {
    "api.replicas",
    "mcp.replicas",
    "database.storage.storageClass",
    "backup.enabled",
} | RESERVED_ENV_KEYS


def _load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _leaves(node: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        for key, value in node.items():
            out.update(_leaves(value, f"{prefix}{key}."))
        return out
    return {prefix.rstrip("."): node}


def _default(leaves: dict[str, Any], key: str) -> tuple[bool, Any]:
    return key in leaves, leaves.get(key)


def _platform_eks(*args: str) -> list[str]:
    return _render(
        PLATFORM,
        "-f",
        str(PLATFORM / "values-eks.yaml"),
        "--set-string",
        f"gateway.hostname={HOST}",
        "--set-string",
        f"gateway.aws.certificateArn={CERT}",
        "--set-string",
        "aws-load-balancer-controller.clusterName=c",
        *args,
    )


def _ticketscope_eks(*args: str) -> list[str]:
    return _render(TICKETSCOPE, "-f", str(TICKETSCOPE / "values-eks.yaml"), *_IMAGE_TAGS, *args)


@pytest.mark.criterion("ticketscope--e5-s2--AC-3")
def test_ticketscope_eks_values_hold_only_environment_keys() -> None:
    eks = _leaves(_load(TICKETSCOPE / "values-eks.yaml"))
    assert set(eks) <= TICKETSCOPE_ENV_KEYS, set(eks) - TICKETSCOPE_ENV_KEYS


@pytest.mark.criterion("ticketscope--e5-s2--AC-3")
def test_platform_eks_values_hold_only_environment_keys() -> None:
    eks = _leaves(_load(PLATFORM / "values-eks.yaml"))
    stray = {
        k for k in eks if k not in PLATFORM_ENV_KEYS and not k.startswith(PLATFORM_ENV_PREFIXES)
    }
    assert not stray, stray


def _overrides(eks: dict[str, Any], defaults: dict[str, Any], allowed: set[str]) -> list[str]:
    """Keys an environment file sets that differ from a product default and are not
    environment keys; the snapshot, embedding and retrieval keys are never allowed (AD-25)."""
    bad = []
    for key, value in eks.items():
        has_default, default = _default(defaults, key)
        if key.startswith(("snapshot.", "embeddings.", "retrieval.")) or (
            has_default
            and default not in (None, "", [], {})
            and default != value
            and key not in allowed
            and not key.startswith(PLATFORM_ENV_PREFIXES)
        ):
            bad.append(key)
    return bad


@pytest.mark.criterion("ticketscope--e5-s2--AC-3")
@pytest.mark.parametrize("chart", [PLATFORM, TICKETSCOPE], ids=["platform", "ticketscope"])
def test_eks_values_never_override_a_product_default(chart: Path) -> None:
    defaults = _leaves(_load(chart / "values.yaml"))
    eks = _leaves(_load(chart / "values-eks.yaml"))
    allowed = PLATFORM_ENV_KEYS if chart == PLATFORM else TICKETSCOPE_ENV_KEYS
    assert _overrides(eks, defaults, allowed) == []


@pytest.mark.criterion("ticketscope--e5-s2--AC-3")
def test_the_override_check_reports_a_product_default_override() -> None:
    defaults = _leaves(_load(TICKETSCOPE / "values.yaml"))
    overridden = _leaves({"retrieval": {"defaultMode": "keyword"}, "api": {"replicas": 3}})
    assert _overrides(overridden, defaults, TICKETSCOPE_ENV_KEYS) == ["retrieval.defaultMode"]
    pinned = _leaves({"telemetry": {"recordQueryText": True}})
    assert _overrides(pinned, defaults, TICKETSCOPE_ENV_KEYS) == ["telemetry.recordQueryText"]


@pytest.mark.criterion("ticketscope--e5-s2--AC-3")
def test_eks_values_commit_no_account_id_hostname_or_arn() -> None:
    for path in (PLATFORM / "values-eks.yaml", TICKETSCOPE / "values-eks.yaml"):
        text = path.read_text(encoding="utf-8")
        data = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
        assert not re.search(r"\b\d{12}\b", data)
        assert "arn:aws" not in data and "hostname:" not in data


@pytest.mark.criterion("ticketscope--e5-s2--AC-3")
def test_ticketscope_renders_on_eks_with_gp3_and_no_backup() -> None:
    docs = _ticketscope_eks()
    [cluster] = _docs(docs, "Cluster", "ticketscope-db")
    assert "storageClass: gp3" in cluster
    assert "instances: 2" in cluster
    assert not _docs(docs, "ObjectStore")
    assert "plugins:" not in cluster
    # The pin is the product default's.
    assert not _docs(docs, "Job", "ticketscope-eval")


@pytest.mark.criterion("ticketscope--e5-s2--AC-1")
@needs_platform_deps
def test_gateway_has_an_https_listener_and_names_the_load_balancer_configuration() -> None:
    docs = _platform_eks()
    [gateway] = _docs(docs, "Gateway", "ticketscope")
    assert "gatewayClassName: alb" in gateway
    assert "protocol: HTTPS" in gateway and "port: 443" in gateway
    assert "mode: Terminate" in gateway
    assert "options:" in gateway
    assert "kind: LoadBalancerConfiguration" in gateway
    assert "certificateRefs" not in gateway
    [cls] = _docs(docs, "GatewayClass", "alb")
    assert "controllerName: gateway.k8s.aws/alb" in cls


@pytest.mark.criterion("ticketscope--e5-s2--AC-1")
@needs_platform_deps
def test_certificate_is_an_explicit_arn_on_an_internet_facing_alb() -> None:
    docs = _platform_eks()
    [config] = _docs(docs, "LoadBalancerConfiguration", "ticketscope")
    assert "scheme: internet-facing" in config
    assert f'defaultCertificate: "{CERT}"' in config
    assert 'protocolPort: "HTTPS:443"' in config


@pytest.mark.criterion("ticketscope--e5-s2--AC-1")
@needs_platform_deps
def test_each_routed_service_has_target_type_ip() -> None:
    docs = _platform_eks()
    for service in ("ticketscope-api", "ticketscope-mcp"):
        [tgc] = _docs(docs, "TargetGroupConfiguration", service)
        assert "namespace: ticketscope" in tgc
        assert f"name: {service}\n" in tgc.split("targetReference:")[1]
        assert "targetType: ip" in tgc


@pytest.mark.criterion("ticketscope--e5-s2--AC-1")
@needs_platform_deps
def test_missing_certificate_arn_fails_the_render() -> None:
    from tests.unit.test_chart_backup import _template

    result = _template(
        PLATFORM,
        "-f",
        str(PLATFORM / "values-eks.yaml"),
        "--set-string",
        "aws-load-balancer-controller.clusterName=c",
    )
    assert result.returncode != 0
    assert "certificateArn is required" in result.stderr


@pytest.mark.criterion("ticketscope--e5-s2--AC-4")
@needs_platform_deps
def test_controller_default_tags_and_gateway_feature_gate_are_set() -> None:
    docs = _platform_eks()
    controller = next(d for d in _docs(docs, "Deployment") if "aws-load-balancer-controller" in d)
    assert "--default-tags=environment=eks" in controller
    assert "--feature-gates=ALBGatewayAPI=true" in controller


@pytest.mark.criterion("ticketscope--e5-s2--AC-2")
@needs_platform_deps
def test_external_dns_reads_gateway_routes_into_the_hosted_zone_of_the_hostname() -> None:
    docs = _platform_eks("--set-string", f"external-dns.domainFilters[0]={HOST}")
    dns = next(d for d in _docs(docs, "Deployment") if "external-dns" in d.split("spec:")[0])
    assert "--source=gateway-httproute" in dns
    assert "--provider=aws" in dns
    assert "--policy=sync" in dns
    assert f"--domain-filter={HOST}" in dns


@pytest.mark.criterion("ticketscope--e5-s2--AC-2")
@needs_platform_deps
def test_target_annotation_is_the_fallback_and_absent_by_default() -> None:
    [plain] = _docs(_platform_eks(), "Gateway", "ticketscope")
    assert "external-dns.kubernetes.io/target" not in plain
    [annotated] = _docs(
        _platform_eks("--set-string", "gateway.externalDnsTarget=alb.example.test"),
        "Gateway",
        "ticketscope",
    )
    assert 'external-dns.kubernetes.io/target: "alb.example.test"' in annotated


@pytest.mark.criterion("ticketscope--e5-s2--AC-3")
@needs_platform_deps
def test_eks_platform_has_one_gateway_no_ingress_and_no_envoy() -> None:
    docs = _platform_eks()
    assert len(_docs(docs, "Gateway")) == 1
    assert not _docs(docs, "Ingress")
    assert not any("envoy-gateway" in d.split("spec:")[0] for d in _docs(docs, "Deployment"))
    [sc] = _docs(docs, "StorageClass", "gp3")
    assert "provisioner: ebs.csi.aws.com" in sc and "type: gp3" in sc


@pytest.mark.criterion("ticketscope--e5-s2--AC-3")
@needs_platform_deps
def test_kind_platform_render_has_no_eks_resources_and_its_old_gateway() -> None:
    docs = _render(PLATFORM, "-f", str(PLATFORM / "values-kind.yaml"))
    for kind in ("LoadBalancerConfiguration", "TargetGroupConfiguration", "StorageClass"):
        assert not _docs(docs, kind), kind
    [gateway] = _docs(docs, "Gateway", "ticketscope")
    assert "protocol: HTTPS" not in gateway
    assert "infrastructure:" not in gateway and "annotations:" not in gateway
    assert "gatewayClassName: envoy" in gateway
    names = [d for d in _docs(docs, "Deployment") if "load-balancer" in d or "external-dns" in d]
    assert not names
    [cls] = _docs(docs, "GatewayClass", "envoy")
    assert "controllerName: gateway.envoyproxy.io/gatewayclass-controller" in cls


def _ticketscope_render(environment: str) -> list[str]:
    """The ticketscope chart with one environment file. EKS has no hostname of its own, so the
    live-style host is passed the way eks-deploy.sh passes it; kind keeps its own."""
    args = ["-f", str(TICKETSCOPE / f"values-{environment}.yaml"), *_IMAGE_TAGS[:4]]
    if environment == "eks":
        args += ["--set-string", f"hostname={HOST}"]
    return _render(TICKETSCOPE, *args)


@pytest.mark.criterion("ticketscope--e5-s5--AC-1")
@pytest.mark.parametrize("environment", ["kind", "eks"])
@pytest.mark.parametrize("chart", ["platform", "ticketscope"])
@needs_platform_deps
def test_both_charts_render_with_both_environment_files(chart: str, environment: str) -> None:
    if chart == "ticketscope":
        assert _ticketscope_render(environment)
    elif environment == "eks":
        assert _platform_eks()
    else:
        assert _render(PLATFORM, "-f", str(PLATFORM / "values-kind.yaml"))


@pytest.mark.criterion("ticketscope--e5-s5--AC-1")
def test_eks_mcp_allows_exactly_the_live_hostname_and_no_kind_name_renders() -> None:
    text = "\n".join(_ticketscope_render("eks"))
    match = re.search(r'name: TICKETSCOPE_MCP_ALLOWED_HOSTS\s+value: "([^"]*)"', text)
    assert match is not None, "mcp renders no allowed-hosts list"
    assert match.group(1) == HOST
    assert "*" not in match.group(1)
    assert "kind.internal" not in text


@pytest.mark.criterion("ticketscope--e5-s5--AC-2")
def test_the_override_and_allowlist_checks_name_each_stray_key() -> None:
    defaults = _leaves(_load(TICKETSCOPE / "values.yaml"))
    stray = _leaves(
        {
            "snapshot": {"version": "x"},
            "retrieval": {"defaultMode": "keyword"},
            "database": {"unlisted": "x"},
        }
    )
    assert _overrides(stray, defaults, TICKETSCOPE_ENV_KEYS) == [
        "snapshot.version",
        "retrieval.defaultMode",
    ]
    assert {k for k in stray if k not in TICKETSCOPE_ENV_KEYS} == {
        "snapshot.version",
        "retrieval.defaultMode",
        "database.unlisted",
    }


@pytest.mark.criterion("ticketscope--e5-s5--AC-2")
def test_the_reserved_names_are_the_ad25_irsa_and_placement_keys() -> None:
    assert {
        "database.serviceAccount.annotations",
        "database.instancePlacement",
    } == RESERVED_ENV_KEYS
    assert RESERVED_ENV_KEYS <= TICKETSCOPE_ENV_KEYS


@pytest.mark.criterion("ticketscope--e5-s2--AC-3")
def test_kind_ticketscope_render_is_the_one_mcp_e2e_runs_against() -> None:
    docs = _render(TICKETSCOPE, "-f", str(TICKETSCOPE / "values-kind.yaml"), *_IMAGE_TAGS)
    [cluster] = _docs(docs, "Cluster", "ticketscope-db")
    assert "storageClass: standard" in cluster
    assert _docs(docs, "ObjectStore")
