"""scripts/eks-teardown.sh (story 5.4) against stubs of helm, kubectl, aws and terraform on PATH:
the calls arrive in AD-24 order, a Gateway or controller configuration object that never goes
stops the run before the controller (`platform`) is uninstalled, and stale DNS records fail the
run after the destroy. No cluster, no AWS."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.target import REPO

SCRIPT = REPO / "scripts" / "eks-teardown.sh"
PLATFORM_TEMPLATES = REPO / "deploy" / "charts" / "platform" / "templates"
HOSTNAME = "ticketscope.example.test"
ZONE_ID = "ZEXAMPLE"

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")

STUB = """#!/usr/bin/env bash
echo "{name} $*" >> "$STUB_LOG"
{body}
"""

AWS_BODY = """\
case "$*" in
  *elasticloadbalancing:loadbalancer*)
    [[ -n "${ALB_ERROR:-}" ]] && { echo "boom" >&2; exit 255; }
    [[ -n "${ALB_STUCK:-}" ]] && echo "arn:aws:elasticloadbalancing:::loadbalancer/app/k8s/x"
    ;;
  *describe-network-interfaces*)
    [[ -n "${ENI_STUCK:-}" ]] && echo "eni-0abc"
    ;;
  *list-resource-record-sets*)
    [[ -n "${DNS_ERROR:-}" ]] && { echo "AccessDenied" >&2; exit 254; }
    [[ -n "${DNS_STALE:-}" ]] && printf '%s.\\tA\\n%s.\\tAAAA\\n' "$DNS_STALE" "$DNS_STALE"
    ;;
esac
exit 0
"""
KUBECTL_BODY = """\
args="$*"
if [[ "$args" == *custom-columns* ]]; then
  echo 'NAME FINALIZERS'
  echo 'stuck ["gateway.k8s.aws/stuck-finalizer"]'
elif [[ "$args" == *"get gateway ticketscope"* && "$args" == *"-o name"* ]]; then
  [[ -n "${GATEWAY_STUCK:-}" ]] && echo "gateway.gateway.networking.k8s.io/ticketscope"
elif [[ "$args" == *"get gateway ticketscope"* ]]; then
  echo '["gateway.k8s.aws/resources"]'
elif [[ "$args" == *"get "* && "$args" == *"-o name"* && -n "${CONFIG_STUCK:-}" ]]; then
  [[ "$args" == *"$CONFIG_STUCK"* ]] && echo "$CONFIG_STUCK/stuck"
fi
exit 0
"""


def _setup(tmp_path: Path) -> tuple[Path, Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True)
    log = tmp_path / "calls.log"
    log.write_text("")
    bodies = {"helm": "exit 0", "terraform": "exit 0", "aws": AWS_BODY, "kubectl": KUBECTL_BODY}
    for name, body in bodies.items():
        stub = bin_dir / name
        stub.write_text(STUB.format(name=name, body=body))
        stub.chmod(0o755)
    kubeconfig = tmp_path / "kubeconfig"
    kubeconfig.write_text("")
    return bin_dir, log, kubeconfig


def _run(
    tmp_path: Path, *args: str, **env: str
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    bin_dir, log, kubeconfig = _setup(tmp_path)
    full_args = args or ("--kubeconfig", str(kubeconfig), "--hostname", HOSTNAME)
    result = subprocess.run(
        [str(SCRIPT), *full_args],
        capture_output=True,
        text=True,
        check=False,
        env={
            "PATH": f"{bin_dir}:/usr/bin:/bin",
            "STUB_LOG": str(log),
            "POLL_SECONDS": "1",
            "TICKETSCOPE_ZONE_ID": ZONE_ID,
            **env,
        },
    )
    return result, log.read_text().splitlines()


def _index(calls: list[str], fragment: str) -> int:
    return next(i for i, call in enumerate(calls) if fragment in call)


@pytest.mark.criterion("ticketscope--e5-s4--AC-3")
def test_the_calls_arrive_in_ad_24_order(tmp_path: Path) -> None:
    result, calls = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    order = [
        _index(calls, "helm uninstall ticketscope"),
        _index(calls, "kubectl -n ticketscope delete pvc"),
        _index(calls, "kubectl -n platform delete gateway ticketscope"),
        _index(calls, "elasticloadbalancing:loadbalancer"),
        _index(calls, "kubectl -n platform get gateway ticketscope"),
        _index(calls, "delete -n ticketscope targetgroupconfiguration.gateway.k8s.aws --all"),
        _index(calls, "get -n ticketscope targetgroupconfiguration.gateway.k8s.aws"),
        _index(calls, "delete -n platform loadbalancerconfiguration.gateway.k8s.aws --all"),
        _index(calls, "get -n platform loadbalancerconfiguration.gateway.k8s.aws"),
        _index(calls, "delete gatewayclass alb"),
        _index(calls, "get gatewayclass alb"),
        _index(calls, "helm uninstall platform"),
        _index(calls, "describe-network-interfaces"),
        _index(calls, "describe-volumes"),
        _index(calls, "terraform -chdir=infra/env destroy"),
        _index(calls, f"list-resource-record-sets --hosted-zone-id {ZONE_ID}"),
    ]
    assert order == sorted(order)
    assert "--- eks-teardown stage times ---" in result.stdout
    assert "controller-config-objects" in result.stdout and "dns-records" in result.stdout


@pytest.mark.criterion("ticketscope--e5-s4--AC-3")
def test_a_gateway_whose_alb_never_goes_fails_before_platform_is_uninstalled(
    tmp_path: Path,
) -> None:
    result, calls = _run(tmp_path, ALB_STUCK="1", ALB_WAIT_SECONDS="2")
    assert result.returncode == 1
    assert not any("helm uninstall platform" in c for c in calls)
    assert not any("terraform" in c for c in calls)
    assert "gateway.k8s.aws/resources" in result.stderr  # the finalizers
    assert "Remedy" in result.stderr
    # Nothing is forced and no finalizer is touched.
    joined = "\n".join(calls)
    assert "patch" not in joined and "--force" not in joined and "--grace-period" not in joined
    # The stage times still print.
    assert "--- eks-teardown stage times ---" in result.stdout


def test_an_aws_error_while_waiting_is_never_read_as_the_alb_being_gone(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, ALB_ERROR="1", ALB_WAIT_SECONDS="2")
    assert result.returncode == 1
    assert not any("helm uninstall platform" in c for c in calls)


def test_tagged_enis_that_remain_stop_the_run_before_terraform(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, ENI_STUCK="1", ENI_VOLUME_WAIT_SECONDS="2")
    assert result.returncode == 1
    assert any("helm uninstall platform" in c for c in calls)
    assert not any("terraform" in c for c in calls)


def test_the_give_up_times_come_from_env_vars(tmp_path: Path) -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'ALB_WAIT_SECONDS="${ALB_WAIT_SECONDS:-900}"' in text
    assert 'CONFIG_WAIT_SECONDS="${CONFIG_WAIT_SECONDS:-300}"' in text
    assert 'ENI_VOLUME_WAIT_SECONDS="${ENI_VOLUME_WAIT_SECONDS:-600}"' in text
    assert 'GATEWAY_CLASS="${GATEWAY_CLASS:-alb}"' in text
    result, _ = _run(tmp_path, ALB_STUCK="1", ALB_WAIT_SECONDS="1")
    assert "after 1s" in result.stderr
    result, calls = _run(tmp_path / "class", GATEWAY_CLASS="other")
    assert result.returncode == 0, result.stderr
    assert any("delete gatewayclass other" in c for c in calls)


def test_skip_cluster_runs_only_terraform_and_the_dns_check(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, "--skip-cluster", "--hostname", HOSTNAME)
    assert result.returncode == 0, result.stderr
    assert len(calls) == 2
    assert calls[0].startswith("terraform -chdir=infra/env destroy")
    assert calls[1].startswith(f"aws route53 list-resource-record-sets --hosted-zone-id {ZONE_ID}")


def test_a_missing_kubeconfig_is_a_usage_error_and_calls_nothing(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, "--kubeconfig", str(tmp_path / "absent"))
    assert result.returncode == 2 and "usage:" in result.stderr
    assert calls == []


def test_a_missing_hostname_or_zone_id_is_a_usage_error_and_calls_nothing(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, "--skip-cluster")
    assert result.returncode == 2 and "usage:" in result.stderr
    assert calls == []
    result, calls = _run(
        tmp_path / "zone", "--skip-cluster", "--hostname", HOSTNAME, TICKETSCOPE_ZONE_ID=""
    )
    assert result.returncode == 2 and calls == []


def test_the_script_never_forces_deletes_or_touches_bootstrap() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    for forbidden in ("--force", " patch ", "--grace-period", "bootstrap"):
        assert forbidden not in text, forbidden


@pytest.mark.criterion("ticketscope--e5-s4--AC-3")
def test_an_alb_that_is_gone_while_the_gateway_still_exists_does_not_uninstall_the_controller(
    tmp_path: Path,
) -> None:
    # Live finding (first env-down on EKS): the ALB left the tagging API within seconds, but the
    # Gateway stayed Terminating until the controller finished the target groups and security
    # group; uninstalling the controller then stranded it.
    result, calls = _run(tmp_path, GATEWAY_STUCK="1", ALB_WAIT_SECONDS="2")
    assert result.returncode == 1
    assert not any("helm uninstall platform" in c for c in calls)
    assert not any("terraform" in c for c in calls)


@pytest.mark.criterion("ticketscope--e5-s4--AC-3")
@pytest.mark.parametrize(
    "stuck",
    [
        "targetgroupconfiguration.gateway.k8s.aws",
        "loadbalancerconfiguration.gateway.k8s.aws",
        "gatewayclass",
    ],
)
def test_a_configuration_object_that_never_goes_fails_before_platform_is_uninstalled(
    tmp_path: Path, stuck: str
) -> None:
    # Live finding: `helm uninstall platform` deleted these with the controller, the controller
    # went first, and they stayed Terminating on its finalizers until helm gave up at 10 minutes.
    result, calls = _run(tmp_path, CONFIG_STUCK=stuck, CONFIG_WAIT_SECONDS="2")
    assert result.returncode == 1
    assert not any("helm uninstall platform" in c for c in calls)
    assert not any("terraform" in c for c in calls)
    assert "gateway.k8s.aws/stuck-finalizer" in result.stderr  # the finalizers
    assert "Remedy" in result.stderr and "after 2s" in result.stderr
    joined = "\n".join(calls)
    assert "patch" not in joined and "--force" not in joined and "--grace-period" not in joined
    assert "--- eks-teardown stage times ---" in result.stdout


def _template_kinds() -> set[str]:
    kinds: set[str] = set()
    for template in PLATFORM_TEMPLATES.glob("*.yaml"):
        kinds.update(re.findall(r"^kind:\s*(\w+)\s*$", template.read_text(encoding="utf-8"), re.M))
    return kinds


# Kinds the load balancer controller puts its finalizers on, or that it needs to clean up.
FINALIZER_KINDS = {
    "Gateway",
    "GatewayClass",
    "LoadBalancerConfiguration",
    "TargetGroupConfiguration",
    "IngressClassParams",
    "TargetGroupBinding",
}


@pytest.mark.criterion("ticketscope--e5-s4--AC-3")
def test_every_finalizer_carrying_kind_in_platform_is_deleted_before_platform_is_uninstalled(
    tmp_path: Path,
) -> None:
    kinds = _template_kinds() & FINALIZER_KINDS
    # The parse is not vacuous: the kinds the chart ships today are found.
    assert {"Gateway", "GatewayClass", "LoadBalancerConfiguration", "TargetGroupConfiguration"} <= (
        kinds
    )
    result, calls = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    before_platform = calls[: _index(calls, "helm uninstall platform")]
    deleted: set[str] = set()
    for call in before_platform:
        words = call.split()
        if words[0] != "kubectl" or "delete" not in words:
            continue
        for word in words[words.index("delete") + 1 :]:
            deleted.add(word.split(".")[0].lower())
    missing = {kind for kind in kinds if kind.lower() not in deleted}
    assert not missing, f"the teardown does not delete {missing} before `helm uninstall platform`"


@pytest.mark.criterion("ticketscope--e5-s4--AC-3")
def test_stale_dns_records_fail_the_run_after_the_destroy_with_the_remedy(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, DNS_STALE=HOSTNAME)
    assert result.returncode == 3
    destroy = _index(calls, "terraform -chdir=infra/env destroy")
    check = _index(calls, "list-resource-record-sets")
    assert destroy < check  # the environment is destroyed anyway, so billing stops
    assert f"{HOSTNAME}.\tA" in result.stderr and f"{HOSTNAME}.\tAAAA" in result.stderr
    assert "change-resource-record-sets" in result.stderr
    assert f"--hosted-zone-id {ZONE_ID}" in result.stderr
    assert f"Name=='{HOSTNAME}.'" in result.stderr and '"DELETE"' in result.stderr
    # The check is read-only: the remedy is printed, never run.
    assert not any("change-resource-record-sets" in c for c in calls)
    assert "--- eks-teardown stage times ---" in result.stdout


def test_an_aws_error_in_the_dns_check_is_never_read_as_clean(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, DNS_ERROR="1")
    assert result.returncode == 3
    assert any("terraform -chdir=infra/env destroy" in c for c in calls)
    assert "not clean" in result.stderr


def test_the_dns_check_asks_only_for_the_hostnames_a_and_aaaa_records(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, "--skip-cluster", "--hostname", f"{HOSTNAME}.")
    assert result.returncode == 0, result.stderr
    (query,) = [c for c in calls if "list-resource-record-sets" in c]
    assert f"Name=='{HOSTNAME}.'" in query and "Type=='A'" in query and "Type=='AAAA'" in query
