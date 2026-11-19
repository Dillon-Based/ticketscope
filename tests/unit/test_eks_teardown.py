"""scripts/eks-teardown.sh (story 5.4) against stubs of helm, kubectl, aws and terraform on PATH:
the calls arrive in AD-24 order, and a Gateway whose ALB never goes stops the run before the
controller (`platform`) is uninstalled. No cluster, no AWS."""

import shutil
import subprocess
from pathlib import Path

import pytest

from tests.target import REPO

SCRIPT = REPO / "scripts" / "eks-teardown.sh"

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
esac
exit 0
"""
KUBECTL_BODY = """\
if [[ "$*" == *"get gateway"* && "$*" == *"-o name"* ]]; then
  [[ -n "${GATEWAY_STUCK:-}" ]] && echo "gateway.gateway.networking.k8s.io/ticketscope"
elif [[ "$*" == *"get gateway"* ]]; then
  echo '["gateway.k8s.aws/resources"]'
fi
exit 0
"""


def _setup(tmp_path: Path) -> tuple[Path, Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
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
    full_args = args or ("--kubeconfig", str(kubeconfig))
    result = subprocess.run(
        [str(SCRIPT), *full_args],
        capture_output=True,
        text=True,
        check=False,
        env={
            "PATH": f"{bin_dir}:/usr/bin:/bin",
            "STUB_LOG": str(log),
            "POLL_SECONDS": "1",
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
        _index(calls, "helm uninstall platform"),
        _index(calls, "describe-network-interfaces"),
        _index(calls, "describe-volumes"),
        _index(calls, "terraform -chdir=infra/env destroy"),
    ]
    assert order == sorted(order)
    assert "--- eks-teardown stage times ---" in result.stdout


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
    assert 'ENI_VOLUME_WAIT_SECONDS="${ENI_VOLUME_WAIT_SECONDS:-600}"' in text
    result, _ = _run(tmp_path, ALB_STUCK="1", ALB_WAIT_SECONDS="1")
    assert "after 1s" in result.stderr


def test_skip_cluster_runs_only_terraform(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, "--skip-cluster")
    assert result.returncode == 0, result.stderr
    assert len(calls) == 1 and calls[0].startswith("terraform -chdir=infra/env destroy")


def test_a_missing_kubeconfig_is_a_usage_error_and_calls_nothing(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, "--kubeconfig", str(tmp_path / "absent"))
    assert result.returncode == 2 and "usage:" in result.stderr
    assert calls == []


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
