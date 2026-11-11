"""The mcp Deployment, Service and HTTPRoute on offline renders (story 4.1)."""

import shutil

import pytest

from tests.unit.test_chart_backup import _IMAGE_TAGS, TICKETSCOPE, _docs, _render, _template

pytestmark = pytest.mark.skipif(shutil.which("helm") is None, reason="needs helm")

KIND = ["-f", str(TICKETSCOPE / "values-kind.yaml")]


def _mcp(*args: str) -> list[str]:
    # --set beats -f, so restate the kind hostname the shared image-tag args override.
    host = ["--set", "hostname=ticketscope.kind.internal"]
    return _render(TICKETSCOPE, *KIND, *_IMAGE_TAGS, *host, *args)


def test_kind_renders_two_replicas_with_process_only_probes() -> None:
    [deploy] = _docs(_mcp(), "Deployment", "ticketscope-mcp")
    assert "replicas: 2" in deploy
    assert 'command: ["ticketscope-mcp"]' in deploy
    assert "livenessProbe:" in deploy and "readinessProbe:" in deploy
    assert deploy.count("path: /healthz") == 2
    assert "/readyz" not in deploy and "path: /v1" not in deploy


def test_no_secret_database_or_mode_env() -> None:
    [deploy] = _docs(_mcp(), "Deployment", "ticketscope-mcp")
    for absent in ("secretKeyRef", "TICKETSCOPE_DB_", "DEFAULT_MODE", "EMBEDDING", "volumes:"):
        assert absent not in deploy, absent


def test_api_url_is_the_in_cluster_service() -> None:
    [deploy] = _docs(_mcp(), "Deployment", "ticketscope-mcp")
    assert 'value: "http://ticketscope-api.ticketscope.svc"' in deploy
    assert "TICKETSCOPE_API_TIMEOUT_SECONDS" in deploy


def test_hosts_come_from_values_on_the_deployment_and_the_route() -> None:
    docs = _mcp("--set", "mcp.hosts={mcp.example.org}")
    [deploy] = _docs(docs, "Deployment", "ticketscope-mcp")
    assert 'value: "ticketscope.kind.internal,mcp.example.org"' in deploy
    [route] = _docs(docs, "HTTPRoute", "ticketscope-mcp")
    assert '- "ticketscope.kind.internal"' in route and '- "mcp.example.org"' in route
    assert "value: /mcp" in route and "type: PathPrefix" in route
    assert "name: ticketscope-mcp" in route


@pytest.mark.parametrize("hosts", ["{*}", "{*.example.org}", "{}"])
def test_wildcard_hosts_are_refused(hosts: str) -> None:
    result = _template(
        TICKETSCOPE, *_IMAGE_TAGS, "--set", f"mcp.hosts={hosts}", "--set", "hostname="
    )
    assert result.returncode != 0
    assert "mcp" in result.stderr and "host" in result.stderr


def test_a_wildcard_hostname_is_refused_too() -> None:
    result = _template(TICKETSCOPE, *_IMAGE_TAGS, "--set", "hostname=*")
    assert result.returncode != 0
    assert "wildcard" in result.stderr


def test_default_replicas_is_one_and_kind_overrides_it() -> None:
    docs = _render(
        TICKETSCOPE, *_IMAGE_TAGS, "--set", "hostname=h.test", "--set", "backup.enabled=false"
    )
    [deploy] = _docs(docs, "Deployment", "ticketscope-mcp")
    assert "replicas: 1" in deploy


def test_query_text_opt_in_follows_values() -> None:
    [off] = _docs(_mcp(), "Deployment", "ticketscope-mcp")
    assert 'name: TICKETSCOPE_TRACE_QUERY_TEXT\n              value: "false"' in off
    [on] = _docs(_mcp("--set", "telemetry.recordQueryText=true"), "Deployment", "ticketscope-mcp")
    assert 'name: TICKETSCOPE_TRACE_QUERY_TEXT\n              value: "true"' in on
