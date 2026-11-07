"""The traces pipeline on offline renders (story 9, AD-10, AD-11, AD-14): the platform chart
brings the collector (contrib 0.164.0, OTLP to Tempo, traces only), Tempo and Grafana with
a Tempo datasource, none of them exposed; the ticketscope chart points api, migrate and
load at the collector."""

import shutil

import pytest

from tests.unit.test_chart_backup import (
    _IMAGE_TAGS,
    PLATFORM,
    TICKETSCOPE,
    _docs,
    _flat,
    _render,
    needs_platform_deps,
)

pytestmark = pytest.mark.skipif(shutil.which("helm") is None, reason="needs helm")

COLLECTOR = "http://otel-collector.platform.svc:4318"
TELEMETRY_NAMES = ("otel-collector", "tempo", "grafana")


def _platform(*args: str) -> list[str]:
    return _render(PLATFORM, "-f", str(PLATFORM / "values-kind.yaml"), *args)


@needs_platform_deps
def test_collector_is_contrib_0_164_with_one_traces_pipeline_to_tempo() -> None:
    docs = _platform()
    [deploy] = _docs(docs, "Deployment", "otel-collector")
    assert 'image: "otel/opentelemetry-collector-contrib:0.164.0"' in deploy
    [config] = _docs(docs, "ConfigMap", "otel-collector")
    flat = _flat(config)
    assert "otlp_grpc: endpoint: tempo.platform.svc:4317 tls: insecure: true" in flat
    assert "traces: exporters: - otlp_grpc processors: - memory_limiter - batch" in flat
    assert "receivers: - otlp" in flat
    # Traces only (AD-11): no metrics or logs pipeline, no spanmetrics, no legacy receivers.
    for absent in ("metrics:", "logs:", "spanmetrics", "jaeger", "zipkin", "prometheus"):
        assert absent not in config, absent
    [service] = _docs(docs, "Service", "otel-collector")
    assert "port: 4318" in service and "port: 4317" in service
    assert "6831" not in service and "9411" not in service


@needs_platform_deps
def test_tempo_and_grafana_with_a_tempo_datasource() -> None:
    docs = _platform()
    [tempo] = _docs(docs, "StatefulSet", "tempo")
    assert "volumeClaimTemplates" not in tempo
    [tempo_config] = _docs(docs, "ConfigMap", "tempo")
    assert "reporting_enabled: false" in tempo_config
    assert "block_retention: 24h" in tempo_config
    [service] = _docs(docs, "Service", "tempo")
    assert "port: 3200" in service and "port: 4317" in service
    [grafana] = _docs(docs, "ConfigMap", "grafana")
    flat = _flat(grafana)
    assert "type: tempo" in flat
    assert "uid: tempo" in flat
    assert "url: http://tempo.platform.svc:3200" in flat
    assert "isDefault: true" in flat
    assert _docs(docs, "Deployment", "grafana")
    assert not _docs(docs, "PersistentVolumeClaim", "grafana")


@needs_platform_deps
def test_grafana_admin_password_is_chart_generated() -> None:
    docs = _platform()
    [secret] = _docs(docs, "Secret", "grafana")
    assert "admin-password:" in secret
    values = (PLATFORM / "values.yaml").read_text(encoding="utf-8")
    assert "adminPassword" not in values
    # Generated per render, never a fixed value.
    [again] = _docs(_platform(), "Secret", "grafana")
    assert again != secret


@needs_platform_deps
def test_nothing_of_the_traces_pipeline_is_exposed() -> None:
    docs = _platform()
    for doc in _docs(docs, "HTTPRoute") + _docs(docs, "Ingress"):
        assert not any(f"name: {n}" in doc for n in TELEMETRY_NAMES), doc
    for name in TELEMETRY_NAMES:
        [service] = _docs(docs, "Service", name)
        assert "type: LoadBalancer" not in service
        assert "type: NodePort" not in service
    # And on the defaults, not just kind's facts.
    defaults = _render(PLATFORM)
    for name in TELEMETRY_NAMES:
        [service] = _docs(defaults, "Service", name)
        assert "type: LoadBalancer" not in service
        assert "type: NodePort" not in service


@needs_platform_deps
def test_telemetry_resources_are_set() -> None:
    docs = _platform()
    for kind, name in (
        ("Deployment", "otel-collector"),
        ("StatefulSet", "tempo"),
        ("Deployment", "grafana"),
    ):
        [doc] = _docs(docs, kind, name)
        flat = _flat(doc)
        assert "requests: cpu:" in flat, name
        assert "limits: memory:" in flat, name


def test_ticketscope_points_api_migrate_and_load_at_the_collector() -> None:
    docs = _render(TICKETSCOPE, "-f", str(TICKETSCOPE / "values-kind.yaml"), *_IMAGE_TAGS)
    for kind, name in (
        ("Deployment", "ticketscope-api"),
        ("Job", "ticketscope-migrate"),
        ("Job", "ticketscope-load"),
    ):
        [doc] = _docs(docs, kind, name)
        assert f'- name: TICKETSCOPE_OTLP_ENDPOINT value: "{COLLECTOR}"' in _flat(doc), name
    [api] = _docs(docs, "Deployment", "ticketscope-api")
    assert '- name: TICKETSCOPE_TRACE_QUERY_TEXT value: "false"' in _flat(api)
