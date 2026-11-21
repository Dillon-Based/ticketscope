"""CloudNativePG backs up to the bootstrap bucket through an IRSA role (story 5.6, R6, R8):
the chart's EKS render, the role's policy in infra/env, and the deploy and backup wiring."""

import re
import shutil
import subprocess
from typing import Any

import pytest
import yaml

from tests.target import REPO
from tests.unit.test_chart_backup import _IMAGE_TAGS, TICKETSCOPE, _docs, _flat, _render

ROLE_ARN = "arn:aws:iam::000000000000:role/ticketscope-env-cnpg-backup"
ANNOTATION = "database.serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
IRSA = (REPO / "infra" / "env" / "irsa.tf").read_text(encoding="utf-8")
DEPLOY = (REPO / "scripts" / "eks-deploy.sh").read_text(encoding="utf-8")
BACKUP = REPO / "scripts" / "eks-backup.sh"
WORKFLOW: dict[str, Any] = yaml.safe_load(
    (REPO / ".github" / "workflows" / "env-up.yml").read_text(encoding="utf-8")
)

needs_helm = pytest.mark.skipif(shutil.which("helm") is None, reason="needs helm")


def _eks(*extra: str) -> list[str]:
    return _render(
        TICKETSCOPE,
        *_IMAGE_TAGS,
        "-f",
        str(TICKETSCOPE / "values-eks.yaml"),
        "--set-string",
        "backup.destinationPath=s3://bucket/backups/",
        "--set-string",
        "backup.serverName=inc-1-1",
        "--set-string",
        f"{ANNOTATION}={ROLE_ARN}",
        *extra,
    )


@needs_helm
def test_eks_render_annotates_the_account_inherits_the_role_and_names_the_server() -> None:
    docs = _eks()
    [cluster] = _docs(docs, "Cluster", "ticketscope-db")
    flat = _flat(cluster)
    assert (
        f"serviceAccountTemplate: metadata: annotations: eks.amazonaws.com/role-arn: {ROLE_ARN}"
        in flat
    )
    assert 'barmanObjectName: ticketscope-backup serverName: "inc-1-1"' in flat
    # R6: the account is the operator's, and the skip-check annotation is never used.
    assert "serviceAccountName" not in cluster
    assert "skipEmptyWalArchiveCheck" not in "\n".join(docs)
    [store] = _docs(docs, "ObjectStore", "ticketscope-backup")
    assert "inheritFromIAMRole: true" in store
    assert "accessKeyId" not in store and "endpointURL" not in store
    assert not _docs(docs, "Secret", "ticketscope-backup-s3")
    [scheduled] = _docs(docs, "ScheduledBackup")
    assert "method: plugin" in scheduled and "name: ticketscope-db" in scheduled


@needs_helm
def test_kind_render_keeps_seaweedfs_credentials_and_no_annotation_or_server_name() -> None:
    docs = _render(TICKETSCOPE, *_IMAGE_TAGS, "-f", str(TICKETSCOPE / "values-kind.yaml"))
    [cluster] = _docs(docs, "Cluster", "ticketscope-db")
    assert "serviceAccountTemplate" not in cluster and "serverName" not in cluster
    [store] = _docs(docs, "ObjectStore", "ticketscope-backup")
    assert "ticketscope-backup-s3" in store and "inheritFromIAMRole" not in store


@needs_helm
def test_the_role_without_an_arn_fails_to_render() -> None:
    result = subprocess.run(
        ["helm", "template", "t", str(TICKETSCOPE), *_IMAGE_TAGS, "-f",
         str(TICKETSCOPE / "values-eks.yaml"), "--set-string", "backup.destinationPath=s3://b/"],
        capture_output=True, text=True, check=False,
    )  # fmt: skip
    assert result.returncode != 0 and "role-arn" in result.stderr


def test_the_eks_values_hold_no_arn_bucket_or_incarnation() -> None:
    text = (TICKETSCOPE / "values-eks.yaml").read_text(encoding="utf-8")
    values = yaml.safe_load(text)
    assert values["backup"] == {
        "enabled": True,
        "credentials": {"inheritFromIAMRole": True},
        "scheduled": {"enabled": True},
    }
    assert not re.search(r"arn:aws|s3://|serverName", re.sub(r"(?m)^\s*#.*$", "", text))


def test_the_backup_policy_reaches_only_the_backups_prefix() -> None:
    accounts = '"ticketscope:ticketscope-db", "ticketscope:ticketscope-restore"'
    assert f"namespace_service_accounts = [{accounts}]" in IRSA
    objects = re.search(r'sid\s*=\s*"BackupObjects".*?resources\s*=\s*\[(.*?)\]', IRSA, re.S)
    assert objects and objects.group(1).strip() == '"arn:aws:s3:::${local.backup_bucket}/backups/*"'
    assert 'values   = ["backups/*"]' in IRSA
    # Never the Terraform state prefix, never a wildcard action or resource.
    policy = IRSA[IRSA.index('data "aws_iam_policy_document" "cnpg_backup"') :]
    assert "env/" not in policy and '"s3:*"' not in policy and '"*"' not in policy
    # HeadBucket carries no s3:prefix key, so barman's bucket check needs its own ListBucket
    # statement; it is the Null condition, never an unconditional ListBucket (run 44802980572).
    reachable = re.search(r'sid\s*=\s*"BackupBucketReachable"(.*?)\n  }\n', IRSA, re.S)
    assert reachable and 'test     = "Null"' in reachable.group(1)
    assert 'variable = "s3:prefix"' in reachable.group(1) and '["true"]' in reachable.group(1)
    assert len(re.findall(r'"s3:ListBucket"', policy)) == 2
    for action in ("PutObject", "GetObject", "DeleteObject", "AbortMultipartUpload"):
        assert f"s3:{action}" in policy


def test_the_deploy_script_passes_the_role_bucket_and_incarnation() -> None:
    assert "--incarnation" in DEPLOY and "cnpg_backup_role_arn" in DEPLOY
    assert "backup.destinationPath=s3://${BACKUP_BUCKET}/backups/" in DEPLOY
    assert "backup.serverName=${INCARNATION}" in DEPLOY
    assert "role-arn=${BACKUP_ROLE_ARN}" in DEPLOY


def test_the_deploy_script_without_an_incarnation_is_a_usage_error() -> None:
    result = subprocess.run(
        [str(REPO / "scripts" / "eks-deploy.sh"), "--kubeconfig", "x", "--tag", "t",
         "--hostname", "h", "--certificate-arn", "a", "--ecr-registry", "r"],
        capture_output=True, text=True, check=False,
    )  # fmt: skip
    assert result.returncode == 2 and "usage:" in result.stderr


def test_the_backup_script_usage_and_missing_kubeconfig() -> None:
    bare = subprocess.run([str(BACKUP)], capture_output=True, text=True, check=False)
    assert bare.returncode == 2 and "usage:" in bare.stderr
    absent = subprocess.run(
        [str(BACKUP), "--kubeconfig", "/nonexistent", "--incarnation", "i"],
        capture_output=True, text=True, check=False,
    )  # fmt: skip
    assert absent.returncode == 2


def test_env_up_names_the_incarnation_and_backs_up_after_the_smoke_check() -> None:
    steps = WORKFLOW["jobs"]["env"]["steps"]
    names = [str(s.get("name", "")) for s in steps]
    deploy = steps[next(i for i, n in enumerate(names) if n.startswith("Deploy the releases"))]
    assert '--incarnation "$INCARNATION"' in deploy["run"]
    smoke = next(i for i, n in enumerate(names) if n.startswith("Smoke check"))
    backup = next(i for i, n in enumerate(names) if n.startswith("On-demand backup"))
    summary = next(i for i, n in enumerate(names) if n.startswith("Job summary"))
    assert smoke < backup < summary
    assert "scripts/eks-backup.sh" in steps[backup]["run"]
    facts = steps[next(i for i, n in enumerate(names) if n.startswith("Read the bootstrap"))]
    assert "INCARNATION=inc-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}" in facts["run"]
