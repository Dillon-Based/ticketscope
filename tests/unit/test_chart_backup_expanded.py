"""Expanded coverage for story 8 (backups to SeaweedFS through the Barman Cloud Plugin,
AD-18, AD-25), on offline renders and static repo files.

Adds to `test_chart_backup.py`: the generated plugin certificates themselves (subject,
SAN, lifetime, key pair, ca.crt), the plugin Deployment mounting them, the two charts
agreeing on the SeaweedFS endpoint and bucket, the credential guard, value overrides
reaching both the ObjectStore and the Cluster, AD-25's "environment facts only" rule
for the kind values files, no key material in git, and every chart repository being
added before `helm dependency build` in CI and kind-up.
"""

import base64
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.target import REPO

CHARTS = REPO / "deploy" / "charts"
PLATFORM = CHARTS / "platform"
TICKETSCOPE = CHARTS / "ticketscope"
PLATFORM_KIND = PLATFORM / "values-kind.yaml"
TICKETSCOPE_KIND = TICKETSCOPE / "values-kind.yaml"
# mcp refuses to render without a host (story 4.1), so every render has one.
_IMAGE_TAGS = [
    "--set-string",
    "image.app.tag=t",
    "--set-string",
    "image.postgres.tag=18-t",
    "--set",
    "hostname=ticketscope.test",
]

needs_helm = pytest.mark.skipif(shutil.which("helm") is None, reason="needs helm")
needs_openssl = pytest.mark.skipif(shutil.which("openssl") is None, reason="needs openssl")


def _platform_deps_built() -> bool:
    lock = (PLATFORM / "Chart.lock").read_text(encoding="utf-8")
    pairs = re.findall(r"- name: (\S+)\n\s+repository: \S+\n\s+version: (\S+)", lock)
    return bool(pairs) and all((PLATFORM / "charts" / f"{n}-{v}.tgz").exists() for n, v in pairs)


needs_platform_deps = pytest.mark.skipif(
    shutil.which("helm") is None or not _platform_deps_built(),
    reason="needs helm and built platform dependencies (helm dependency build)",
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
        if f"\nkind: {kind}\n" in f"\n{d}\n"
        and (name is None or re.search(rf'^  name: "?{re.escape(name)}"?$', d, re.M))
    ]


def _flat(doc: str) -> str:
    return " ".join(doc.split())


def _data(secret: str, key: str) -> bytes:
    match = re.search(rf"^  {re.escape(key)}: (\S+)$", secret, re.M)
    assert match, (key, secret)
    return base64.b64decode(match.group(1))


def _openssl(*args: str, stdin: bytes) -> str:
    result = subprocess.run(["openssl", *args], input=stdin, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr.decode()
    return result.stdout.decode()


def _top_level_keys(values_file: Path) -> list[str]:
    return [
        m.group(1) for m in re.finditer(r"^([A-Za-z][\w-]*):", values_file.read_text("utf-8"), re.M)
    ]


# --- platform: the plugin's Helm-generated mTLS certificates (no cert-manager) -------------


@pytest.fixture(scope="module")
def platform_kind_docs() -> list[str]:
    if shutil.which("helm") is None or not _platform_deps_built():
        pytest.skip("needs helm and built platform dependencies")
    return _render(PLATFORM, "-f", str(PLATFORM_KIND))


@needs_platform_deps
@needs_openssl
@pytest.mark.parametrize(
    ("secret_name", "cn", "san"),
    [
        ("barman-cloud-server-tls", "barman-cloud", "DNS:barman-cloud"),
        ("barman-cloud-client-tls", "barman-cloud-client", None),
    ],
)
def test_plugin_tls_secret_holds_a_valid_self_signed_cert_for_its_role(
    platform_kind_docs: list[str], secret_name: str, cn: str, san: str | None
) -> None:
    [secret] = _docs(platform_kind_docs, "Secret", secret_name)
    crt, key, ca = _data(secret, "tls.crt"), _data(secret, "tls.key"), _data(secret, "ca.crt")
    assert crt.startswith(b"-----BEGIN CERTIFICATE-----")
    assert b"PRIVATE KEY-----" in key
    # Self-signed: each cert is its own CA.
    assert ca == crt
    subject = _openssl("x509", "-noout", "-subject", "-issuer", stdin=crt)
    assert f"CN={cn}" in subject.replace(" = ", "=")
    text = _openssl("x509", "-noout", "-text", stdin=crt)
    if san is None:
        assert "Subject Alternative Name" not in text or "DNS:" not in text
    else:
        assert san in text
    # About ten years, so a long-lived kind cluster never meets an expired plugin cert.
    assert _openssl("x509", "-noout", "-checkend", str(9 * 365 * 24 * 3600), stdin=crt)
    # The key belongs to the cert.
    cert_pub = _openssl("x509", "-noout", "-pubkey", stdin=crt)
    key_pub = _openssl("pkey", "-pubout", stdin=key)
    assert cert_pub == key_pub


@needs_platform_deps
def test_server_and_client_certs_are_distinct(platform_kind_docs: list[str]) -> None:
    [server] = _docs(platform_kind_docs, "Secret", "barman-cloud-server-tls")
    [client] = _docs(platform_kind_docs, "Secret", "barman-cloud-client-tls")
    assert _data(server, "tls.crt") != _data(client, "tls.crt")
    assert _data(server, "tls.key") != _data(client, "tls.key")


@needs_platform_deps
def test_plugin_deployment_runs_in_platform_and_mounts_the_generated_secrets(
    platform_kind_docs: list[str],
) -> None:
    [deploy] = [
        d
        for d in _docs(platform_kind_docs, "Deployment")
        if "app.kubernetes.io/name: barman-cloud" in d
    ]
    assert "namespace: platform" in deploy
    flat = _flat(deploy)
    assert "secret: secretName: barman-cloud-server-tls" in flat
    assert "secret: secretName: barman-cloud-client-tls" in flat
    assert "--server-cert=/server/tls.crt" in deploy
    assert "--client-cert=/client/tls.crt" in deploy


@needs_helm
def test_plugin_disabled_renders_no_tls_secrets_and_no_plugin() -> None:
    # The TLS template is gated on the same flag as the subchart; gating does not need
    # the subchart archives, so this runs wherever helm and the deps are present.
    if not _platform_deps_built():
        pytest.skip("platform chart dependencies not built")
    docs = _render(PLATFORM, "--set", "barman-cloud.enabled=false")
    assert not _docs(docs, "Secret", "barman-cloud-server-tls")
    assert not _docs(docs, "Secret", "barman-cloud-client-tls")
    assert not _docs(docs, "Service", "barman-cloud")


# --- the two charts agree on the backup target ---------------------------------------------


@needs_platform_deps
def test_ticketscope_kind_endpoint_names_the_rendered_seaweedfs_s3_service(
    platform_kind_docs: list[str],
) -> None:
    kind = TICKETSCOPE_KIND.read_text("utf-8")
    endpoint = re.search(r"endpointURL: (\S+)", kind)
    assert endpoint, kind
    match = re.fullmatch(
        r"http://([a-z0-9-]+)\.([a-z0-9-]+)\.svc(?:\.cluster\.local)?:(\d+)", endpoint.group(1)
    )
    assert match, endpoint.group(1)
    service, namespace, port = match.groups()
    [svc] = _docs(platform_kind_docs, "Service", service)
    assert re.search(rf'^  namespace: "?{namespace}"?$', svc, re.M)
    assert f"port: {port}" in svc


@needs_platform_deps
def test_ticketscope_kind_destination_bucket_is_one_the_platform_creates(
    platform_kind_docs: list[str],
) -> None:
    kind = TICKETSCOPE_KIND.read_text("utf-8")
    dest = re.search(r"destinationPath: s3://([^/\s]+)/", kind)
    assert dest, kind
    [hook] = [d for d in _docs(platform_kind_docs, "Job") if "bucket-hook" in d]
    assert f"s3.bucket.create --name {dest.group(1)}" in hook


@needs_platform_deps
def test_ticketscope_kind_copies_keys_the_platform_secret_actually_has(
    platform_kind_docs: list[str],
) -> None:
    kind = TICKETSCOPE_KIND.read_text("utf-8")
    fields = dict(
        re.findall(r"^\s+(namespace|secret|accessKeyIdKey|secretAccessKeyKey): (\S+)$", kind, re.M)
    )
    [creds] = _docs(platform_kind_docs, "Secret", fields["secret"])
    assert re.search(rf'^  namespace: "?{fields["namespace"]}"?$', creds, re.M)
    assert f"  {fields['accessKeyIdKey']}:" in creds
    assert f"  {fields['secretAccessKeyKey']}:" in creds
    # The chart keeps the keys across upgrades and uninstalls (the copy depends on them).
    assert '"helm.sh/resource-policy": keep' in creds


# --- ticketscope: guards and value plumbing ------------------------------------------------


@needs_helm
def test_backup_without_any_credential_source_fails_to_render() -> None:
    result = _template(TICKETSCOPE, *_IMAGE_TAGS, "--set-string", "backup.destinationPath=s3://b/")
    assert result.returncode != 0
    assert "set copyFrom.secret or inheritFromIAMRole" in result.stderr


@needs_helm
def test_custom_object_store_name_reaches_both_store_and_cluster() -> None:
    docs = _render(
        TICKETSCOPE,
        *_IMAGE_TAGS,
        "-f",
        str(TICKETSCOPE_KIND),
        "--set-string",
        "backup.objectStoreName=other-store",
    )
    assert _docs(docs, "ObjectStore", "other-store")
    assert not _docs(docs, "ObjectStore", "ticketscope-backup")
    [cluster] = _docs(docs, "Cluster", "ticketscope-db")
    assert "barmanObjectName: other-store" in cluster


@needs_helm
def test_retention_and_compression_overrides_reach_the_object_store() -> None:
    docs = _render(
        TICKETSCOPE,
        *_IMAGE_TAGS,
        "-f",
        str(TICKETSCOPE_KIND),
        "--set-string",
        "backup.retentionPolicy=30d",
        "--set-string",
        "backup.wal.compression=bzip2",
    )
    [store] = _docs(docs, "ObjectStore", "ticketscope-backup")
    assert 'retentionPolicy: "30d"' in store
    assert "wal: compression: bzip2" in _flat(store)


@needs_helm
def test_object_store_and_cluster_live_in_the_release_namespace() -> None:
    docs = _render(TICKETSCOPE, *_IMAGE_TAGS, "-f", str(TICKETSCOPE_KIND))
    [store] = _docs(docs, "ObjectStore", "ticketscope-backup")
    [cluster] = _docs(docs, "Cluster", "ticketscope-db")
    assert "namespace: ticketscope" in store
    assert "namespace: ticketscope" in cluster
    assert "app.kubernetes.io/part-of: ticketscope" in store


@needs_helm
def test_enabling_backup_leaves_the_rest_of_the_cluster_spec_unchanged() -> None:
    def cluster(*extra: str) -> str:
        docs = _render(TICKETSCOPE, *_IMAGE_TAGS, "-f", str(TICKETSCOPE_KIND), *extra)
        [doc] = _docs(docs, "Cluster", "ticketscope-db")
        return doc

    on = cluster()
    off = cluster("--set", "backup.enabled=false")
    plugins = re.search(r"(?:\n  #.*)*\n  plugins:\n(?:    .*\n)+", on)
    assert plugins, on
    assert on.replace(plugins.group(0), "\n") == off


@needs_helm
def test_no_in_tree_barman_object_store_and_no_scheduled_backup() -> None:
    docs = _render(TICKETSCOPE, *_IMAGE_TAGS, "-f", str(TICKETSCOPE_KIND))
    joined = "\n".join(docs)
    assert "barmanObjectStore" not in joined
    assert not _docs(docs, "ScheduledBackup")
    assert not _docs(docs, "Backup")


# --- AD-25: values-kind files hold only environment facts; no keys in git ------------------


def test_platform_kind_values_set_only_environment_facts() -> None:
    assert set(_top_level_keys(PLATFORM_KIND)) == {"gateway", "seaweedfs"}
    text = PLATFORM_KIND.read_text("utf-8")
    seaweed = text.split("seaweedfs:", 1)[1]
    leaf_keys = re.findall(r"^[ \t]+(\w+):[ \t]*[^\s#]", seaweed, re.M)
    assert sorted(leaf_keys) == ["enabled", "storageClass"]


def test_ticketscope_kind_backup_values_set_only_environment_facts() -> None:
    text = TICKETSCOPE_KIND.read_text("utf-8")
    backup = text.split("\nbackup:\n", 1)[1]
    leaf_keys = re.findall(r"^[ \t]+(\w+):[ \t]*[^\s#]", backup, re.M)
    assert sorted(leaf_keys) == sorted(
        [
            "destinationPath",
            "endpointURL",
            "namespace",
            "secret",
            "accessKeyIdKey",
            "secretAccessKeyKey",
        ]
    )


def test_default_values_hold_no_environment_backup_facts() -> None:
    text = (TICKETSCOPE / "values.yaml").read_text("utf-8")
    assert 'destinationPath: ""' in text
    assert 'endpointURL: ""' in text
    assert "seaweedfs" not in text.lower().split("\nbackup:", 1)[1].split("#")[0]


@pytest.mark.parametrize(
    "path",
    [
        PLATFORM / "values.yaml",
        PLATFORM_KIND,
        TICKETSCOPE / "values.yaml",
        TICKETSCOPE_KIND,
        TICKETSCOPE / "templates" / "backup.yaml",
        PLATFORM / "templates" / "barman-cloud-tls.yaml",
    ],
    ids=lambda p: str(p.relative_to(CHARTS)),
)
def test_no_key_material_in_git(path: Path) -> None:
    text = path.read_text("utf-8")
    assert "BEGIN CERTIFICATE" not in text
    assert "PRIVATE KEY" not in text
    # No literal S3 key values: every key-ish field is empty, a key name, or templated.
    for field in ("accessKey", "secretKey", "access_key_id", "secret_access_key"):
        for m in re.finditer(rf"\b{field}\w*:[ \t]*(\S*)", text, re.I):
            value = m.group(1).strip("\"'")
            assert value in {"", "{{"} or value.startswith(("{{", "admin_", "ACCESS_")), (
                field,
                value,
            )


# --- every chart repository is added before `helm dependency build` -----------------------


def _http_repositories() -> set[str]:
    chart = (PLATFORM / "Chart.yaml").read_text("utf-8")
    return set(re.findall(r"repository: (https?://\S+)", chart))


@pytest.mark.parametrize(
    "path",
    [REPO / "scripts" / "kind-up.sh", REPO / ".github" / "workflows" / "ci.yml"],
    ids=["kind-up.sh", "ci.yml"],
)
def test_every_http_chart_repository_is_added_before_dependency_build(path: Path) -> None:
    text = path.read_text("utf-8")
    build = text.index("helm dependency build")
    added = set(re.findall(r"helm repo add \S+ (https?://\S+)", text[:build]))
    missing = _http_repositories() - added
    assert not missing, f"{path.name} never adds {sorted(missing)} before dependency build"


def test_chart_lock_pins_every_chart_yaml_dependency() -> None:
    chart = (PLATFORM / "Chart.yaml").read_text("utf-8")
    lock = (PLATFORM / "Chart.lock").read_text("utf-8")
    wanted = set(re.findall(r"- name: (\S+)\n(?:\s+alias: \S+\n)?\s+version: (\S+)", chart))
    locked = set(re.findall(r"- name: (\S+)\n\s+repository: \S+\n\s+version: (\S+)", lock))
    assert ("plugin-barman-cloud", "0.8.1") in wanted
    assert ("seaweedfs", "4.52.0") in wanted
    assert wanted == locked


def test_kind_deploy_diagnostics_print_backups_and_object_stores() -> None:
    text = (REPO / ".github" / "workflows" / "_kind-deploy.yml").read_text("utf-8")
    assert "backups.postgresql.cnpg.io" in text
    assert "objectstores.barmancloud.cnpg.io" in text


def test_ci_charts_job_runs_the_backup_render_tests_after_dependency_build() -> None:
    text = (REPO / ".github" / "workflows" / "ci.yml").read_text("utf-8")
    build = text.index("helm dependency build deploy/charts/platform")
    run = text.index("pytest tests/unit/test_chart_backup.py")
    assert build < run
