"""Story 9 expanded chart coverage: the ticketscope chart's telemetry values plumbing (AD-10,
AD-13, AD-25). Offline `helm template` renders; no platform dependencies needed."""

import shutil

import pytest

from tests.unit.test_chart_backup import _IMAGE_TAGS, TICKETSCOPE, _docs, _flat, _render

pytestmark = pytest.mark.skipif(shutil.which("helm") is None, reason="needs helm")

COLLECTOR = "http://otel-collector.platform.svc:4318"
WORKLOADS = (
    ("Deployment", "ticketscope-api"),
    ("Job", "ticketscope-migrate"),
    ("Job", "ticketscope-load"),
)


def _ticketscope(*args: str) -> list[str]:
    return _render(TICKETSCOPE, "-f", str(TICKETSCOPE / "values-kind.yaml"), *_IMAGE_TAGS, *args)


def test_record_query_text_true_reaches_the_api_as_a_string() -> None:
    [api] = _docs(
        _ticketscope("--set", "telemetry.recordQueryText=true"), "Deployment", "ticketscope-api"
    )
    assert '- name: TICKETSCOPE_TRACE_QUERY_TEXT value: "true"' in _flat(api)


def test_query_text_opt_in_is_on_the_api_only() -> None:
    docs = _ticketscope("--set", "telemetry.recordQueryText=true")
    for kind, name in WORKLOADS[1:]:
        [doc] = _docs(docs, kind, name)
        assert "TICKETSCOPE_TRACE_QUERY_TEXT" not in doc, name


def test_an_empty_endpoint_renders_empty_on_every_workload() -> None:
    docs = _ticketscope("--set-string", "telemetry.otlpEndpoint=")
    for kind, name in WORKLOADS:
        [doc] = _docs(docs, kind, name)
        assert '- name: TICKETSCOPE_OTLP_ENDPOINT value: ""' in _flat(doc), name


def test_each_workload_gets_the_endpoint_exactly_once() -> None:
    docs = _ticketscope()
    for kind, name in WORKLOADS:
        [doc] = _docs(docs, kind, name)
        assert doc.count("name: TICKETSCOPE_OTLP_ENDPOINT") == 1, name
    [api] = _docs(docs, "Deployment", "ticketscope-api")
    assert api.count("name: TICKETSCOPE_TRACE_QUERY_TEXT") == 1


def test_endpoint_is_the_same_in_every_environment() -> None:
    # AD-13: the platform release is identical, so values.yaml holds the endpoint and the
    # kind values never override it (AD-25: kind values carry environment facts only).
    kind_values = (TICKETSCOPE / "values-kind.yaml").read_text(encoding="utf-8")
    assert "telemetry" not in kind_values
    assert "otlp" not in kind_values.lower()
    defaults = (TICKETSCOPE / "values.yaml").read_text(encoding="utf-8")
    assert f'otlpEndpoint: "{COLLECTOR}"' in defaults
    assert "recordQueryText: false" in defaults


def test_no_otel_env_var_is_rendered_into_the_app_chart() -> None:
    # Config convention: our code reads TICKETSCOPE_* only; the semconv opt-in is set in code.
    for doc in _ticketscope():
        assert "name: OTEL_" not in doc
