"""Backups through the Barman Cloud Plugin (story 8, AD-18, AD-25), on offline renders:
the platform chart brings the plugin with Helm-generated mTLS Secrets (no cert-manager)
and, on kind only, SeaweedFS all-in-one with S3 auth and the backup bucket; the
ticketscope chart renders the ObjectStore and the Cluster's plugin WAL archiver, and
refuses to render backups without a destination."""

import shutil
import subprocess
from pathlib import Path

import pytest

from tests.target import REPO

CHARTS = REPO / "deploy" / "charts"
PLATFORM = CHARTS / "platform"
TICKETSCOPE = CHARTS / "ticketscope"
_IMAGE_TAGS = ["--set-string", "image.app.tag=t", "--set-string", "image.postgres.tag=18-t"]

pytestmark = pytest.mark.skipif(shutil.which("helm") is None, reason="needs helm")


def _platform_deps_built() -> bool:
    lock = (PLATFORM / "Chart.lock").read_text(encoding="utf-8")
    pairs: list[tuple[str, str]] = []
    name = ""
    for line in lock.splitlines():
        stripped = line.strip().removeprefix("- ")
        if stripped.startswith("name:"):
            name = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("version:") and name:
            pairs.append((name, stripped.split(":", 1)[1].strip()))
            name = ""
    return bool(pairs) and all((PLATFORM / "charts" / f"{n}-{v}.tgz").exists() for n, v in pairs)


needs_platform_deps = pytest.mark.skipif(
    not _platform_deps_built(),
    reason="platform chart dependencies not built (helm dependency build deploy/charts/platform)",
)


def _template(chart: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["helm", "template", chart.name, str(chart), "--namespace", chart.name, *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _render(chart: Path, *args: str) -> list[str]:
    result = _template(chart, *args)
    assert result.returncode == 0, result.stderr
    return [d for d in result.stdout.split("\n---\n") if "\nkind: " in f"\n{d}"]


def _docs(docs: list[str], kind: str, name: str | None = None) -> list[str]:
    return [
        d
        for d in docs
        if f"\nkind: {kind}\n" in f"\n{d}\n" and (name is None or f"  name: {name}\n" in d)
    ]


def _flat(doc: str) -> str:
    return " ".join(doc.split())


# --- platform ------------------------------------------------------------------------------


@needs_platform_deps
def test_platform_kind_renders_seaweedfs_all_in_one_with_s3_auth_and_the_bucket() -> None:
    docs = _render(PLATFORM, "-f", str(PLATFORM / "values-kind.yaml"))
    [deploy] = _docs(docs, "Deployment", "seaweedfs-all-in-one")
    assert "-s3 \\" in deploy
    assert "-s3.config=/etc/sw/s3/seaweedfs_s3_config" in deploy
    assert "claimName: seaweedfs-all-in-one-data" in deploy
    assert "podAntiAffinity" not in deploy
    [svc] = _docs(docs, "Service", "seaweedfs-all-in-one")
    assert "type: ClusterIP" in svc
    assert "port: 8333" in svc
    [pvc] = _docs(docs, "PersistentVolumeClaim", "seaweedfs-all-in-one-data")
    assert "storageClassName: standard" in pvc
    [creds] = _docs(docs, "Secret", "seaweedfs-s3-secret")
    assert "admin_access_key_id:" in creds and "admin_secret_access_key:" in creds
    [hook] = [d for d in _docs(docs, "Job") if "bucket-hook" in d]
    assert "s3.bucket.create --name ticketscope-backups" in hook
    # Only the all-in-one pod: no standalone components, nothing exposed (AD-14).
    for name in ("seaweedfs-master", "seaweedfs-volume", "seaweedfs-filer", "seaweedfs-s3"):
        assert not [d for d in docs if f"  name: {name}\n" in d], name
    assert not _docs(docs, "HTTPRoute", "seaweedfs-all-in-one")
    assert not _docs(docs, "Ingress")
    assert "type: LoadBalancer" not in "\n".join(_docs(docs, "Service"))


@needs_platform_deps
@pytest.mark.parametrize("values", [[], ["-f", str(PLATFORM / "values-kind.yaml")]])
def test_platform_renders_the_plugin_with_helm_generated_tls_and_no_cert_manager(
    values: list[str],
) -> None:
    docs = _render(PLATFORM, *values)
    assert not [d for d in docs if "cert-manager.io" in d]
    [svc] = _docs(docs, "Service", "barman-cloud")
    assert "cnpg.io/pluginServerSecret: barman-cloud-server-tls" in svc
    assert "cnpg.io/pluginClientSecret: barman-cloud-client-tls" in svc
    assert "namespace: platform" in svc
    for name in ("barman-cloud-server-tls", "barman-cloud-client-tls"):
        [secret] = _docs(docs, "Secret", name)
        assert "type: kubernetes.io/tls" in secret
        assert "namespace: platform" in secret
        for key in ("tls.crt:", "tls.key:", "ca.crt:"):
            assert key in secret, (name, key)


@needs_platform_deps
def test_platform_without_kind_values_renders_no_seaweedfs() -> None:
    docs = _render(PLATFORM)
    assert not [d for d in docs if "seaweedfs" in d]


# --- ticketscope ---------------------------------------------------------------------------


def test_ticketscope_kind_renders_the_object_store_and_the_wal_archiver() -> None:
    docs = _render(TICKETSCOPE, *_IMAGE_TAGS, "-f", str(TICKETSCOPE / "values-kind.yaml"))
    [store] = _docs(docs, "ObjectStore", "ticketscope-backup")
    assert "apiVersion: barmancloud.cnpg.io/v1" in store
    assert 'destinationPath: "s3://ticketscope-backups/"' in store
    assert 'endpointURL: "http://seaweedfs-all-in-one.platform.svc:8333"' in store
    flat = _flat(store)
    assert "accessKeyId: name: ticketscope-backup-s3 key: ACCESS_KEY_ID" in flat
    assert "secretAccessKey: name: ticketscope-backup-s3 key: ACCESS_SECRET_KEY" in flat
    assert "wal: compression: gzip" in flat
    assert 'retentionPolicy: "7d"' in store
    [cluster] = _docs(docs, "Cluster", "ticketscope-db")
    assert (
        "plugins: - name: barman-cloud.cloudnative-pg.io isWALArchiver: true"
        " parameters: barmanObjectName: ticketscope-backup"
    ) in _flat(cluster)
    assert "instances: 2" in cluster
    # Offline: no cluster to copy the keys from, so no copied Secret and no keys in git.
    assert not _docs(docs, "Secret", "ticketscope-backup-s3")


def test_ticketscope_backup_disabled_renders_neither() -> None:
    docs = _render(
        TICKETSCOPE,
        *_IMAGE_TAGS,
        "-f",
        str(TICKETSCOPE / "values-kind.yaml"),
        "--set",
        "backup.enabled=false",
    )
    assert not _docs(docs, "ObjectStore")
    [cluster] = _docs(docs, "Cluster", "ticketscope-db")
    assert "plugins:" not in cluster
    assert "barman" not in cluster


def test_ticketscope_backup_without_destination_fails_to_render() -> None:
    result = _template(TICKETSCOPE, *_IMAGE_TAGS)
    assert result.returncode != 0
    assert "backup.destinationPath is required" in result.stderr


def test_ticketscope_live_cluster_without_platform_secret_fails_to_render() -> None:
    result = _template(
        TICKETSCOPE,
        *_IMAGE_TAGS,
        "-f",
        str(TICKETSCOPE / "values-kind.yaml"),
        "--api-versions",
        "postgresql.cnpg.io/v1",
    )
    assert result.returncode != 0
    assert "platform release" in result.stderr


def test_ticketscope_iam_role_credentials_need_no_secret() -> None:
    docs = _render(
        TICKETSCOPE,
        *_IMAGE_TAGS,
        "--set-string",
        "backup.destinationPath=s3://bucket/",
        "--set",
        "backup.credentials.inheritFromIAMRole=true",
    )
    [store] = _docs(docs, "ObjectStore", "ticketscope-backup")
    assert "inheritFromIAMRole: true" in store
    assert "endpointURL" not in store
    assert "accessKeyId" not in store
