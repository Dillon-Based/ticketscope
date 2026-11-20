"""scripts/eks-teardown.sh (story 5.4) against stubs of helm, kubectl, aws and terraform on PATH:
the calls arrive in AD-24 order, a Gateway or controller configuration object that never goes
stops the run before the controller (`platform`) is uninstalled, and stale DNS records fail the
run after the destroy. No cluster, no AWS."""

import json
import re
import shutil
import subprocess
import sys
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
  *describe-vpcs*)
    [[ -n "${VPC_ERROR:-}" ]] && { echo "boom" >&2; exit 255; }
    echo "${VPC_ID-vpc-0abc}"
    ;;
  *describe-network-interfaces*)
    [[ -n "${ENI_LIST_ERROR:-}" ]] && { echo "boom" >&2; exit 255; }
    if [[ "$*" == *Name=vpc-id* ]]; then
      echo "${CNI_ORPHANS:-}"
    elif [[ "$*" == *eks:eni:owner* ]]; then
      [[ -n "${CNI_WAIT_STUCK:-}" ]] && echo "eni-0cni"
    else
      [[ -n "${ENI_STUCK:-}" ]] && echo "eni-0abc"
    fi
    ;;
  *route53*)
    exec "$(dirname "$0")/route53.py" "$@"
    ;;
esac
exit 0
"""
# A stand-in for the zone: it evaluates the Name and Type terms of the JMESPath filter the script
# sends (no jmespath here) against the records in $ZONE_FILE, and applies a change batch to it.
ROUTE53 = """#!{python}
import json, os, re, sys

args = sys.argv[1:]
zone_file = os.environ["ZONE_FILE"]
records = json.load(open(zone_file))
if "list-resource-record-sets" in args:
    if os.environ.get("DNS_ERROR") or (
        os.environ.get("DNS_LIST_FAILS_AFTER_DELETE") and os.path.exists(zone_file + ".changed")
    ):
        print("AccessDenied", file=sys.stderr)
        sys.exit(254)
    query = args[args.index("--query") + 1]
    names = re.findall(r"Name=='([^']*)'", query)
    types = re.findall(r"Type=='(\\w+)'", query)
    chosen = [r for r in records if r["Name"] in names and r["Type"] in types]
    if query.startswith("{{Changes"):
        batch = [{{"Action": "DELETE", "ResourceRecordSet": r}} for r in chosen]
        print(json.dumps({{"Changes": batch}}))
    else:
        for r in chosen:
            print(r["Name"] + "\\t" + r["Type"])
elif "change-resource-record-sets" in args:
    if os.environ.get("DNS_DELETE_FAILS"):
        print("AccessDenied", file=sys.stderr)
        sys.exit(254)
    batch = json.load(open(args[args.index("--change-batch") + 1].removeprefix("file://")))
    open(os.environ["BATCH_LOG"], "a").write(json.dumps(batch) + "\\n")
    open(zone_file + ".changed", "w").write("")
    if not os.environ.get("DNS_DELETE_NOOP"):
        gone = {{
            (c["ResourceRecordSet"]["Name"], c["ResourceRecordSet"]["Type"])
            for c in batch["Changes"]
        }}
        records = [r for r in records if (r["Name"], r["Type"]) not in gone]
        json.dump(records, open(zone_file, "w"))
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
    terraform = 'sleep "${TF_SLEEP:-0}"; exit "${TF_RC:-0}"'
    bodies = {"helm": "exit 0", "terraform": terraform, "aws": AWS_BODY, "kubectl": KUBECTL_BODY}
    for name, body in bodies.items():
        stub = bin_dir / name
        stub.write_text(STUB.format(name=name, body=body))
        stub.chmod(0o755)
    route53 = bin_dir / "route53.py"
    route53.write_text(ROUTE53.format(python=sys.executable))
    route53.chmod(0o755)
    kubeconfig = tmp_path / "kubeconfig"
    kubeconfig.write_text("")
    return bin_dir, log, kubeconfig


def _zone(*records: tuple[str, str]) -> list[dict[str, object]]:
    return [{"Name": name, "Type": kind, "TTL": 60} for name, kind in records]


def _run(
    tmp_path: Path, *args: str, zone: list[dict[str, object]] | None = None, **env: str
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    bin_dir, log, kubeconfig = _setup(tmp_path)
    (tmp_path / "zone.json").write_text(json.dumps(zone or []))
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
            "ZONE_FILE": str(tmp_path / "zone.json"),
            "BATCH_LOG": str(tmp_path / "batches.log"),
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
    # The CNI sweep (aws ec2) runs beside the destroy; nothing of Kubernetes or helm is called.
    assert not any(c.startswith(("helm", "kubectl")) for c in calls)
    rest = [c for c in calls if not c.startswith("aws ec2")]
    assert len(rest) == 2
    assert rest[0].startswith("terraform -chdir=infra/env destroy")
    assert rest[1].startswith(f"aws route53 list-resource-record-sets --hosted-zone-id {ZONE_ID}")


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


STALE = _zone((f"{HOSTNAME}.", "A"), (f"{HOSTNAME}.", "AAAA"))
# Records that must never be selected: the zone's own NS and SOA, a certificate validation
# CNAME, another name's A record, and a TXT and an NS record at the hostname itself.
OTHERS = _zone(
    ("example.test.", "NS"),
    ("example.test.", "SOA"),
    (f"_abc.{HOSTNAME}.", "CNAME"),
    (f"other.{HOSTNAME}.", "A"),
    (f"{HOSTNAME}.", "TXT"),
    (f"{HOSTNAME}.", "NS"),
)


def _changes(tmp_path: Path) -> list[dict[str, dict[str, object]]]:
    path = tmp_path / "batches.log"
    if not path.exists():
        return []
    return [c for line in path.read_text().splitlines() for c in json.loads(line)["Changes"]]


def _remaining(tmp_path: Path) -> list[dict[str, object]]:
    return json.loads((tmp_path / "zone.json").read_text())


@pytest.mark.criterion("ticketscope--e5-s12--AC-1")
def test_stale_records_are_deleted_after_the_destroy_and_the_run_is_clean(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, zone=STALE + OTHERS)
    assert result.returncode == 0, result.stderr
    destroy = _index(calls, "terraform -chdir=infra/env destroy")
    change = _index(calls, "change-resource-record-sets")
    assert destroy < change  # the environment is destroyed first, so billing stops anyway
    assert f"--hosted-zone-id {ZONE_ID}" in calls[change]
    deleted = {
        (c["Action"], c["ResourceRecordSet"]["Name"], c["ResourceRecordSet"]["Type"])
        for c in _changes(tmp_path)
    }
    assert deleted == {
        ("DELETE", f"{HOSTNAME}.", "A"),
        ("DELETE", f"{HOSTNAME}.", "AAAA"),
    }
    # Listed again after the delete, and nothing else in the zone changed.
    assert max(i for i, c in enumerate(calls) if "list-resource-record-sets" in c) > change
    assert _remaining(tmp_path) == OTHERS
    assert "--- eks-teardown stage times ---" in result.stdout and "dns-records" in result.stdout


@pytest.mark.criterion("ticketscope--e5-s12--AC-3")
def test_the_zone_ns_soa_certificate_and_other_records_are_never_selected(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, zone=OTHERS)
    assert result.returncode == 0, result.stderr
    assert _changes(tmp_path) == []
    assert not any("change-resource-record-sets" in c for c in calls)
    assert _remaining(tmp_path) == OTHERS
    # Every query names the hostname and only the A and AAAA types.
    queries = [c for c in calls if "list-resource-record-sets" in c]
    assert queries
    for query in queries:
        assert f"Name=='{HOSTNAME}.'" in query
        assert re.findall(r"Type=='(\w+)'", query) == ["A", "AAAA"]


def test_a_clean_zone_makes_no_change_call(tmp_path: Path) -> None:
    result, calls = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    assert not any("change-resource-record-sets" in c for c in calls)


@pytest.mark.criterion("ticketscope--e5-s12--AC-1")
def test_a_failed_delete_exits_3_with_the_manual_remedy(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, zone=STALE, DNS_DELETE_FAILS="1")
    assert result.returncode == 3
    assert any("terraform -chdir=infra/env destroy" in c for c in calls)
    assert f"{HOSTNAME}.\tA" in result.stderr and "change-resource-record-sets" in result.stderr
    assert "--- eks-teardown stage times ---" in result.stdout


def test_records_still_present_after_the_delete_exit_3(tmp_path: Path) -> None:
    result, _ = _run(tmp_path, zone=STALE, DNS_DELETE_NOOP="1")
    assert result.returncode == 3
    assert "still holds records" in result.stderr


def test_an_unreadable_zone_after_the_delete_is_never_read_as_clean(tmp_path: Path) -> None:
    result, _ = _run(tmp_path, zone=STALE, DNS_LIST_FAILS_AFTER_DELETE="1")
    assert result.returncode == 3
    assert "not clean" in result.stderr


@pytest.mark.criterion("ticketscope--e5-s12--AC-4")
def test_an_unreadable_zone_exits_3_and_deletes_nothing(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, zone=STALE, DNS_ERROR="1")
    assert result.returncode == 3
    assert any("terraform -chdir=infra/env destroy" in c for c in calls)
    assert "not clean" in result.stderr
    assert not any("change-resource-record-sets" in c for c in calls)


def test_the_dns_step_asks_only_for_the_hostnames_a_and_aaaa_records(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, "--skip-cluster", "--hostname", f"{HOSTNAME}.")
    assert result.returncode == 0, result.stderr
    (query,) = [c for c in calls if "list-resource-record-sets" in c]
    assert f"Name=='{HOSTNAME}.'" in query and "Type=='A'" in query and "Type=='AAAA'" in query


# Bug 5.14: the VPC CNI leaves a detached interface with neither environment tag behind.
def _aws(calls: list[str], verb: str) -> list[str]:
    return [c for c in calls if f"aws ec2 {verb}" in c]


@pytest.mark.criterion("ticketscope--bug-5-14--AC-3")
def test_the_sweep_selects_only_available_cni_interfaces_of_the_environments_vpc(
    tmp_path: Path,
) -> None:
    result, calls = _run(tmp_path, CNI_ORPHANS="eni-0leak")
    assert result.returncode == 0, result.stderr
    (vpcs, *_) = _aws(calls, "describe-vpcs")
    assert "Name=tag:environment,Values=eks" in vpcs
    listings = [c for c in _aws(calls, "describe-network-interfaces") if "vpc-id" in c]
    assert listings
    for listing in listings:
        assert "Name=vpc-id,Values=vpc-0abc" in listing
        assert "Name=status,Values=available" in listing
        assert "Name=tag:eks:eni:owner,Values=amazon-vpc-cni" in listing
    deletes = _aws(calls, "delete-network-interface")
    assert deletes
    assert all(d.endswith("--network-interface-id eni-0leak") for d in deletes)
    # Before the wait for tagged ENIs and before the destroy; nothing is forced.
    assert _index(calls, "delete-network-interface") < _index(calls, "terraform -chdir")
    assert "--force" not in "\n".join(calls)


@pytest.mark.criterion("ticketscope--bug-5-14--AC-1")
def test_the_sweep_also_runs_beside_the_destroy(tmp_path: Path) -> None:
    # A slow destroy: the interface only appears once the nodes go, so the loop must sweep again.
    result, calls = _run(tmp_path, CNI_ORPHANS="eni-0leak", TF_SLEEP="3")
    assert result.returncode == 0, result.stderr
    destroy = _index(calls, "terraform -chdir=infra/env destroy")
    during = [c for c in calls[destroy:] if "delete-network-interface" in c]
    assert during, "no sweep ran while terraform destroy ran"


@pytest.mark.criterion("ticketscope--bug-5-14--AC-1")
def test_a_failed_destroy_keeps_its_exit_status_and_skips_the_dns_step(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, TF_RC="7")
    assert result.returncode == 7
    assert not any("route53" in c for c in calls)


@pytest.mark.criterion("ticketscope--bug-5-14--AC-3")
def test_no_vpc_found_skips_the_sweep_and_the_run_continues(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, VPC_ID="")
    assert result.returncode == 0, result.stderr
    assert not _aws(calls, "delete-network-interface")
    assert not [c for c in _aws(calls, "describe-network-interfaces") if "vpc-id" in c]
    assert "sweep is skipped" in result.stdout


@pytest.mark.criterion("ticketscope--bug-5-14--AC-4")
def test_a_vpc_lookup_error_fails_the_job_before_terraform(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, VPC_ERROR="1")
    assert result.returncode == 1
    assert not any("terraform" in c for c in calls)


@pytest.mark.criterion("ticketscope--bug-5-14--AC-2")
def test_a_cni_interface_that_remains_stops_the_run_before_terraform(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, CNI_WAIT_STUCK="1", ENI_VOLUME_WAIT_SECONDS="2")
    assert result.returncode == 1
    assert not any("terraform" in c for c in calls)
    wait = [c for c in _aws(calls, "describe-network-interfaces") if "vpc-id" not in c]
    assert any(
        "tag:eks:eni:owner,Values=amazon-vpc-cni" in c
        and "tag:cluster.k8s.amazonaws.com/name,Values=ticketscope-env" in c
        # The nodes are still up at this wait: only detached interfaces may stop it.
        and "status,Values=available" in c
        for c in wait
    )


@pytest.mark.criterion("ticketscope--bug-5-14--AC-4")
def test_an_unreadable_interface_listing_is_never_read_as_clean(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, ENI_LIST_ERROR="1", ENI_VOLUME_WAIT_SECONDS="2")
    assert result.returncode == 1
    assert not any("terraform" in c for c in calls)
