"""The env-down leftover check (story 5.4, R3), driven on recorded `get-resources` output: no AWS.

`down.json` (after a teardown) is the clean oracle; `up.json` (an environment that is up) is the
positive control. Each kind of leftover is injected into `down.json` and must fail and be named."""

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from tests.target import REPO

CHECK = REPO / "scripts" / "leftover_check.py"
WRAPPER = REPO / "scripts" / "leftover-check.sh"
FIXTURES = REPO / "tests" / "fixtures" / "aws"
ACCOUNT = "000000000000"

ENV_TAGS = [{"Key": "environment", "Value": "eks"}]
CLUSTER_TAGS = [{"Key": "elbv2.k8s.aws/cluster", "Value": "ticketscope-env"}]
ARNS = {
    "alb": f"arn:aws:elasticloadbalancing:us-east-1:{ACCOUNT}:loadbalancer/app/k8s-x/abc",
    "target group": f"arn:aws:elasticloadbalancing:us-east-1:{ACCOUNT}:targetgroup/k8s-x/abc",
    "volume": f"arn:aws:ec2:us-east-1:{ACCOUNT}:volume/vol-0123",
    "security group": f"arn:aws:ec2:us-east-1:{ACCOUNT}:security-group/sg-0123",
    "kms key": f"arn:aws:kms:us-east-1:{ACCOUNT}:key/11111111-2222-3333-4444-555555555555",
    "log group": f"arn:aws:logs:us-east-1:{ACCOUNT}:log-group:/aws/eks/ticketscope-env/cluster",
}


def _run(*args: str, files: list[Path] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK), *args, *[str(f) for f in files or []]],
        capture_output=True,
        text=True,
        check=False,
    )


def _write(tmp_path: Path, doc: Any, name: str = "listing.json") -> Path:
    path = tmp_path / name
    path.write_text(doc if isinstance(doc, str) else json.dumps(doc), encoding="utf-8")
    return path


def _tagging(*rows: tuple[str, list[dict[str, str]]]) -> dict[str, Any]:
    return {"ResourceTagMappingList": [{"ResourceARN": arn, "Tags": tags} for arn, tags in rows]}


@pytest.mark.criterion("ticketscope--e5-s4--AC-1")
def test_the_recording_taken_after_a_teardown_is_clean() -> None:
    result = _run(files=[FIXTURES / "down.json"])
    assert result.returncode == 0, result.stderr
    assert "clean" in result.stdout


@pytest.mark.criterion("ticketscope--e5-s4--AC-1")
@pytest.mark.parametrize("kind", sorted(ARNS))
def test_each_kind_of_tagged_leftover_fails_and_is_named(kind: str, tmp_path: Path) -> None:
    listing = _write(tmp_path, _tagging((ARNS[kind], ENV_TAGS)))
    result = _run(files=[FIXTURES / "down.json", listing])
    assert result.returncode == 1
    assert ARNS[kind] in result.stdout


@pytest.mark.criterion("ticketscope--e5-s4--AC-1")
def test_a_tagged_network_interface_fails_and_is_named(tmp_path: Path) -> None:
    listing = _write(
        tmp_path,
        {"NetworkInterfaces": [{"NetworkInterfaceId": "eni-0abc", "TagSet": ENV_TAGS}]},
    )
    result = _run(files=[FIXTURES / "down.json", listing])
    assert result.returncode == 1
    assert "eni-0abc" in result.stdout and "network-interface" in result.stdout


def test_the_controllers_cluster_tag_alone_counts(tmp_path: Path) -> None:
    listing = _write(tmp_path, _tagging((ARNS["alb"], CLUSTER_TAGS)))
    result = _run(files=[listing])
    assert result.returncode == 1 and ARNS["alb"] in result.stdout


def test_the_recording_of_an_environment_that_is_up_lists_its_resources() -> None:
    result = _run("--list", files=[FIXTURES / "up.json"])
    assert result.returncode == 0
    for kind in ("loadbalancer", "targetgroup", "security-group", "volume"):
        assert f":{kind} " in result.stdout, kind
    # The same recording fails the check.
    assert _run(files=[FIXTURES / "up.json"]).returncode == 1


def test_foreign_and_bootstrap_resources_are_ignored(tmp_path: Path) -> None:
    listing = _write(
        tmp_path,
        _tagging(
            (ARNS["alb"], [{"Key": "environment", "Value": "someone-else"}]),
            (
                ARNS["volume"],
                [{"Key": "environment", "Value": "eks"}, {"Key": "stack", "Value": "bootstrap"}],
            ),
            (ARNS["kms key"], [{"Key": "stack", "Value": "bootstrap"}]),
            (ARNS["log group"], []),
        ),
    )
    result = _run(files=[listing])
    assert result.returncode == 0, result.stdout


@pytest.mark.criterion("ticketscope--e5-s4--AC-2")
@pytest.mark.parametrize(
    "content",
    [
        "",
        "not json",
        "[]",
        "{}",
        '{"ResourceTagMappingList": null}',
        '{"ResourceTagMappingList": [{}]}',
    ],
)
def test_an_unreadable_or_incomplete_listing_fails(content: str, tmp_path: Path) -> None:
    result = _run(files=[_write(tmp_path, content)])
    assert result.returncode != 0
    assert "clean" not in result.stdout


def test_a_missing_file_and_no_file_at_all_fail(tmp_path: Path) -> None:
    assert _run(files=[tmp_path / "absent.json"]).returncode != 0
    assert _run().returncode != 0


def test_list_still_fails_on_a_listing_it_cannot_read(tmp_path: Path) -> None:
    assert _run("--list", files=[_write(tmp_path, "oops")]).returncode != 0


@pytest.mark.criterion("ticketscope--e5-s4--AC-1")
def test_dry_run_injects_a_tagged_alb_and_fails_naming_it() -> None:
    result = _run("--dry-run")
    assert result.returncode == 1
    assert "loadbalancer" in result.stdout and "dry-run" in result.stdout


pytestmark_bash = pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")


@pytestmark_bash
def test_the_wrapper_dry_run_needs_no_aws_and_fails() -> None:
    result = subprocess.run(
        [str(WRAPPER), "--dry-run"], capture_output=True, text=True, check=False
    )
    assert result.returncode == 1 and "dry-run" in result.stdout


@pytestmark_bash
@pytest.mark.criterion("ticketscope--e5-s4--AC-2")
def test_the_wrapper_fails_when_the_api_is_unreachable(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "aws"
    stub.write_text("#!/usr/bin/env bash\necho 'Could not connect' >&2\nexit 255\n")
    stub.chmod(0o755)
    env = {"PATH": f"{bin_dir}:/usr/bin:/bin"}
    result = subprocess.run([str(WRAPPER)], capture_output=True, text=True, check=False, env=env)
    assert result.returncode == 2 and "FAIL" in result.stderr
    assert "clean" not in result.stdout


@pytestmark_bash
def test_the_wrapper_fails_when_aws_prints_nothing(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "aws"
    stub.write_text("#!/usr/bin/env bash\nexit 0\n")
    stub.chmod(0o755)
    env = {"PATH": f"{bin_dir}:/usr/bin:/bin"}
    result = subprocess.run([str(WRAPPER)], capture_output=True, text=True, check=False, env=env)
    assert result.returncode == 2 and "clean" not in result.stdout


@pytestmark_bash
def test_the_wrapper_reads_clean_listings_and_filters_on_the_environment_tag(
    tmp_path: Path,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "aws.log"
    stub = bin_dir / "aws"
    stub.write_text(
        "#!/usr/bin/env bash\n"
        f'echo "$*" >> "{log}"\n'
        'if [[ "$1" == ec2 ]]; then echo \'{"NetworkInterfaces": []}\'; '
        "else echo '{\"ResourceTagMappingList\": []}'; fi\n"
    )
    stub.chmod(0o755)
    env = {"PATH": f"{bin_dir}:/usr/bin:/bin"}
    result = subprocess.run([str(WRAPPER)], capture_output=True, text=True, check=False, env=env)
    assert result.returncode == 0, result.stderr
    calls = log.read_text()
    assert "Key=environment,Values=eks" in calls and "Key=elbv2.k8s.aws/cluster" in calls
    assert "describe-network-interfaces" in calls
    assert "bootstrap" not in calls


def test_the_check_has_no_destructive_verb() -> None:
    for path in (CHECK, WRAPPER):
        text = path.read_text(encoding="utf-8").lower()
        assert "delete" not in text and "terminate" not in text and "destroy" not in text, path


# The tagging API lags (run 44570082818: two volumes listed minutes after EC2 said NotFound), so
# the wrapper confirms each candidate with its own service. The stub answers each describe call
# from a map of id or ARN to: "found", "empty", "notfound:<Code>", "error" or "state:<KeyState>".
AWS_STUB = f"""#!{sys.executable}
import json, os, sys
args = sys.argv[1:]
with open(os.environ["AWS_LOG"], "a") as log:
    log.write(" ".join(args) + "\\n")
if args[:2] == ["resourcegroupstaggingapi", "get-resources"]:
    if "Key=environment,Values=eks" in args:
        print(open(os.environ["TAGGING_FILE"]).read())
    else:
        print('{{"ResourceTagMappingList": []}}')
    sys.exit(0)
if "--filters" in args:
    print('{{"NetworkInterfaces": []}}')
    sys.exit(0)
answers = json.load(open(os.environ["ANSWERS_FILE"]))
answer = next((answers[a] for a in args if a in answers), None)
if answer is None:
    print("stub: no recorded answer", file=sys.stderr)
    sys.exit(254)
if answer == "found":
    print("present")
elif answer == "empty":
    pass
elif answer.startswith("state:"):
    print(answer.split(":", 1)[1])
elif answer.startswith("notfound:"):
    code = answer.split(":", 1)[1]
    print(f"An error occurred ({{code}}) when calling Describe: not found", file=sys.stderr)
    sys.exit(254)
else:
    print("An error occurred (UnauthorizedOperation) when calling Describe", file=sys.stderr)
    sys.exit(254)
"""

UNKNOWN_ARN = f"arn:aws:eks:us-east-1:{ACCOUNT}:cluster/ticketscope-env"


def _confirmed_run(
    tmp_path: Path, rows: list[str], answers: dict[str, str], *args: str
) -> tuple[subprocess.CompletedProcess[str], str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "aws"
    stub.write_text(AWS_STUB)
    stub.chmod(0o755)
    log = tmp_path / "aws.log"
    log.write_text("")
    tagging = _write(tmp_path, _tagging(*[(arn, ENV_TAGS) for arn in rows]), "tagging.json")
    answers_file = _write(tmp_path, answers, "answers.json")
    env = {
        "PATH": f"{bin_dir}:/usr/bin:/bin",
        "AWS_LOG": str(log),
        "TAGGING_FILE": str(tagging),
        "ANSWERS_FILE": str(answers_file),
    }
    result = subprocess.run(
        [str(WRAPPER), *args], capture_output=True, text=True, check=False, env=env
    )
    return result, log.read_text()


@pytestmark_bash
@pytest.mark.criterion("ticketscope--e5-s4--AC-1")
def test_a_tagged_volume_that_ec2_no_longer_finds_is_dropped_and_the_check_passes(
    tmp_path: Path,
) -> None:
    result, calls = _confirmed_run(
        tmp_path, [ARNS["volume"]], {"vol-0123": "notfound:InvalidVolume.NotFound"}
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"GONE ec2:volume {ARNS['volume']} (tagging API lag)" in result.stdout
    assert "clean" in result.stdout
    assert "ec2 describe-volumes --volume-ids vol-0123" in calls


@pytestmark_bash
@pytest.mark.criterion("ticketscope--e5-s4--AC-1")
def test_a_volume_that_ec2_still_finds_fails(tmp_path: Path) -> None:
    result, _ = _confirmed_run(tmp_path, [ARNS["volume"]], {"vol-0123": "found"})
    assert result.returncode == 1
    assert f"LEFTOVER ec2:volume {ARNS['volume']}" in result.stdout
    assert "GONE" not in result.stdout


@pytestmark_bash
@pytest.mark.criterion("ticketscope--e5-s4--AC-2")
@pytest.mark.parametrize(
    "answer",
    ["error", "notfound:InvalidGroup.NotFound"],  # an error, or another type's not-found code
)
def test_a_describe_error_other_than_not_found_fails(tmp_path: Path, answer: str) -> None:
    result, _ = _confirmed_run(tmp_path, [ARNS["volume"]], {"vol-0123": answer})
    assert result.returncode == 1
    assert f"LEFTOVER ec2:volume {ARNS['volume']} (error)" in result.stdout
    assert "clean" not in result.stdout


@pytestmark_bash
@pytest.mark.parametrize(
    ("state", "dropped"), [("PendingDeletion", True), ("Disabled", True), ("Enabled", False)]
)
def test_a_kms_key_pending_deletion_is_dropped(tmp_path: Path, state: str, dropped: bool) -> None:
    arn = ARNS["kms key"]
    result, calls = _confirmed_run(tmp_path, [arn], {arn: f"state:{state}"})
    assert result.returncode == (0 if dropped else 1), result.stdout
    assert ("GONE kms:key" in result.stdout) is dropped
    assert "kms describe-key --key-id" in calls


@pytestmark_bash
def test_each_confirmable_type_asks_its_own_service(tmp_path: Path) -> None:
    rows = [ARNS[k] for k in ("alb", "target group", "security group", "log group")]
    log_group = "/aws/eks/ticketscope-env/cluster"
    answers = {
        ARNS["alb"]: "notfound:LoadBalancerNotFound",
        ARNS["target group"]: "notfound:TargetGroupNotFound",
        "sg-0123": "notfound:InvalidGroup.NotFound",
        log_group: "empty",  # no exact name match
    }
    result, calls = _confirmed_run(tmp_path, rows, answers)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.count("GONE ") == 4
    assert "elbv2 describe-load-balancers --load-balancer-arns" in calls
    assert "elbv2 describe-target-groups --target-group-arns" in calls
    assert "ec2 describe-security-groups --group-ids sg-0123" in calls
    assert f"logs describe-log-groups --log-group-name-prefix {log_group}" in calls
    assert f"logGroupName=='{log_group}'" in calls


@pytestmark_bash
def test_an_unknown_type_stays_a_leftover(tmp_path: Path) -> None:
    result, calls = _confirmed_run(tmp_path, [UNKNOWN_ARN], {UNKNOWN_ARN: "notfound:x"})
    assert result.returncode == 1
    assert f"LEFTOVER eks:cluster {UNKNOWN_ARN} (unconfirmed)" in result.stdout
    assert UNKNOWN_ARN not in calls  # no describe call is made for it


@pytestmark_bash
@pytest.mark.criterion("ticketscope--e5-s4--AC-1")
def test_list_drops_nothing_and_confirms_nothing(tmp_path: Path) -> None:
    result, calls = _confirmed_run(
        tmp_path, [ARNS["volume"]], {"vol-0123": "notfound:InvalidVolume.NotFound"}, "--list"
    )
    assert result.returncode == 0
    assert f"found ec2:volume {ARNS['volume']}" in result.stdout
    assert "GONE" not in result.stdout and "describe-volumes" not in calls


def test_only_a_gone_confirmation_drops_a_candidate(tmp_path: Path) -> None:
    listing = _write(tmp_path, _tagging((ARNS["volume"], ENV_TAGS), (ARNS["alb"], ENV_TAGS)))
    confirmations = _write(tmp_path, f"{ARNS['volume']}\tgone\n", "confirmations.tsv")
    result = _run("--confirmations", str(confirmations), files=[listing])
    assert result.returncode == 1
    assert f"GONE ec2:volume {ARNS['volume']} (tagging API lag)" in result.stdout
    alb = f"LEFTOVER elasticloadbalancing:loadbalancer {ARNS['alb']} (unconfirmed)"
    assert alb in result.stdout


def test_malformed_confirmations_fail(tmp_path: Path) -> None:
    listing = _write(tmp_path, _tagging((ARNS["volume"], ENV_TAGS)))
    confirmations = _write(tmp_path, f"{ARNS['volume']}\tprobably\n", "confirmations.tsv")
    result = _run("--confirmations", str(confirmations), files=[listing])
    assert result.returncode == 2 and "clean" not in result.stdout


def test_candidates_prints_type_and_id_only(tmp_path: Path) -> None:
    listing = _write(tmp_path, _tagging((ARNS["volume"], ENV_TAGS)))
    result = _run("--candidates", files=[listing])
    assert result.returncode == 0
    assert result.stdout == f"ec2:volume\t{ARNS['volume']}\n"


# Bug 5.14: the interface the VPC CNI left behind, as `describe-network-interfaces` records it
# (tags per the bug's reproduction): detached, with neither the environment nor the controller tag.
CNI_ENI = {
    "NetworkInterfaces": [
        {
            "NetworkInterfaceId": "eni-0leak",
            "Status": "available",
            "Description": "aws-K8S-i-0example",
            "TagSet": [
                {"Key": "node.k8s.amazonaws.com/instance_id", "Value": "i-0example"},
                {"Key": "eks:eni:owner", "Value": "amazon-vpc-cni"},
                {"Key": "cluster.k8s.amazonaws.com/name", "Value": "ticketscope-env"},
                {"Key": "node.k8s.amazonaws.com/createdAt", "Value": "2026-11-19T00:00:00Z"},
            ],
        }
    ]
}


@pytest.mark.criterion("ticketscope--bug-5-14--AC-2")
def test_a_detached_cni_interface_without_the_environment_tags_fails_and_is_named(
    tmp_path: Path,
) -> None:
    result = _run(files=[FIXTURES / "down.json", _write(tmp_path, CNI_ENI)])
    assert result.returncode == 1
    assert "eni-0leak" in result.stdout and "network-interface" in result.stdout


@pytest.mark.criterion("ticketscope--bug-5-14--AC-2")
def test_a_cni_interface_of_another_cluster_or_without_the_owner_tag_is_ignored(
    tmp_path: Path,
) -> None:
    other = json.loads(json.dumps(CNI_ENI))
    other["NetworkInterfaces"][0]["TagSet"][2]["Value"] = "someone-else"
    no_owner = json.loads(json.dumps(CNI_ENI))
    del no_owner["NetworkInterfaces"][0]["TagSet"][1]
    for doc in (other, no_owner):
        assert _run(files=[_write(tmp_path, doc)]).returncode == 0


@pytestmark_bash
@pytest.mark.criterion("ticketscope--bug-5-14--AC-2")
def test_the_wrapper_lists_interfaces_by_the_cnis_own_tags_and_fails_on_a_leaked_one(
    tmp_path: Path,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "aws.log"
    cni = _write(tmp_path, CNI_ENI, "cni.json")
    stub = bin_dir / "aws"
    stub.write_text(
        "#!/usr/bin/env bash\n"
        f'echo "$*" >> "{log}"\n'
        'if [[ "$*" == *eks:eni:owner* ]]; then\n'
        f'  cat "{cni}"\n'
        'elif [[ "$1" == ec2 && "$*" == *--filters* ]]; then echo \'{"NetworkInterfaces": []}\'\n'
        'elif [[ "$*" == *--network-interface-ids* ]]; then echo eni-0leak\n'
        "else echo '{\"ResourceTagMappingList\": []}'; fi\n"
    )
    stub.chmod(0o755)
    env = {"PATH": f"{bin_dir}:/usr/bin:/bin"}
    result = subprocess.run([str(WRAPPER)], capture_output=True, text=True, check=False, env=env)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "eni-0leak" in result.stdout
    calls = log.read_text()
    assert "Name=tag:cluster.k8s.amazonaws.com/name,Values=ticketscope-env" in calls
