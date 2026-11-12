"""Dense checks on kind. They run when values.yaml pins an embedding asset (then `load` has
bulk-loaded it and computed nothing), or when TICKETSCOPE_DENSE_ENABLED is 1 (local
computeOnKind) or 0 (flag-off kind-up). With no pin and no variable they skip, as keyword-only
CI does before a person merges the pin.

Run with -m kind and Gateway environment variables.
"""

import json
import os
import secrets
from concurrent.futures import ThreadPoolExecutor

import httpx2
import pytest

from tests import tempo
from tests.kind import gateway
from tests.smoke.test_gateway import _kubectl, _sql
from tests.target import embeddings_pin
from tests.waiting import eventually
from ticketscope.contract.search import SearchResponse

PINNED = bool(embeddings_pin()["assetVersion"])


def _dense_enabled() -> bool:
    if PINNED:  # a pinned asset always wins in the chart, whatever the flag says
        return True
    return os.environ.get("TICKETSCOPE_DENSE_ENABLED") == "1"


pytestmark = [
    pytest.mark.kind,
    pytest.mark.skipif(
        not PINNED and os.environ.get("TICKETSCOPE_DENSE_ENABLED") not in {"0", "1"},
        reason="no embeddings pin in values.yaml; set TICKETSCOPE_DENSE_ENABLED to the flag",
    ),
]

MODEL = "BAAI/bge-small-en-v1.5"


@pytest.mark.parametrize(
    "query",
    [
        "my world disappears when I try to play",
        "Launcher crash java.lang.NullPointerException\n"
        "at net.minecraft.client.main.Main.main(Main.java:1)\n" * 100,
    ],
)
def test_dense_gateway_queries_and_tempo(query: str) -> None:
    url, host = gateway()
    trace_id = secrets.token_hex(16)
    response = httpx2.post(
        f"{url}/v1/search",
        json={"query": query, "mode": "dense", "k": 10},
        headers={"Host": host, "traceparent": f"00-{trace_id}-{secrets.token_hex(8)}-01"},
        timeout=60,
    )
    if not _dense_enabled():
        assert response.status_code == 503, response.text
        assert response.headers["content-type"].startswith("application/problem+json")
        assert "not available" in response.json()["detail"]
        return
    assert response.status_code == 200, response.text
    body = SearchResponse.model_validate(response.json())
    assert body.mode == "dense" and body.score_kind == "cosine"
    assert len(body.results) == 10
    assert [r.rank for r in body.results] == list(range(1, 11))
    assert [(-r.score, r.issue.number) for r in body.results] == sorted(
        (-r.score, r.issue.number) for r in body.results
    )
    assert all(r.outcome.status for r in body.results)
    numbers = ",".join(str(r.issue.number) for r in body.results)
    outcomes = json.loads(
        _sql(
            "SELECT json_object_agg(number, json_build_object("
            "'status', outcome_status, 'summary', outcome_summary,"
            "'source', outcome_source, 'ref', outcome_ref)) FROM issue "
            f"WHERE number IN ({numbers})"
        )
    )
    assert all(r.outcome.model_dump() == outcomes[str(r.issue.number)] for r in body.results)

    def trace_has_embeddings() -> None:
        status, text = tempo.trace_by_id(trace_id)
        assert status == 200, text
        spans = tempo.spans(json.loads(text))
        retrievals = [s for s in spans if s["name"] == "retrieval dense"]
        embeddings = [s for s in spans if s["name"] == f"embeddings {MODEL}"]
        assert len(retrievals) == len(embeddings) == 1, spans
        [retrieval], [embedding] = retrievals, embeddings
        assert embedding["parentSpanId"] == retrieval["spanId"]
        assert embedding["attrs"]["gen_ai.request.model"] == MODEL

    eventually(trace_has_embeddings, timeout=60, interval=2)


def test_concurrent_dense_requests() -> None:
    if not _dense_enabled():
        pytest.skip("concurrent inference needs computeOnKind")
    url, host = gateway()

    def search(_number: int) -> None:
        response = httpx2.post(
            f"{url}/v1/search",
            json={
                "query": "Launcher crash java.lang.NullPointerException " * 50,
                "mode": "dense",
                "k": 10,
            },
            headers={"Host": host},
            timeout=60,
        )
        assert response.status_code == 200, response.text
        assert len(SearchResponse.model_validate(response.json()).results) == 10

    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(search, range(16)))


def test_dense_corpus_and_load() -> None:
    """R1: every loaded issue has an embedding from the model, and load computed none."""
    enabled = _dense_enabled()
    row = _sql(
        "SELECT (SELECT count(*) FROM issue),"
        " (SELECT count(*) FROM issue_embedding),"
        " coalesce(embedding_model_id, '') FROM corpus_meta"
    ).strip()
    issues, embeddings, model = row.split("|")
    assert int(issues) > 0
    assert int(embeddings) == (int(issues) if enabled else 0)
    assert model == (MODEL if enabled else "")
    if PINNED:
        # The pinned asset was loaded; nothing was computed (the load report has no
        # embedding_seconds, and the Job log has no model-load line).
        log = _kubectl("logs", "job/ticketscope-load")
        assert "embeddings_loaded=" in log or "no-op" in log, log[-2000:]
        assert "embedding_seconds=" not in log


def test_api_survives_dense_load_within_its_memory_budget() -> None:
    """R5: after the dense tests above, api runs under its 512Mi limit with no restart or
    OOM kill, and its cgroup peak stayed within the limit."""
    deployment = json.loads(_kubectl("get", "deploy/ticketscope-api", "-o", "json"))
    container = deployment["spec"]["template"]["spec"]["containers"][0]
    assert container["resources"]["limits"]["memory"] == "512Mi"
    assert deployment["status"]["readyReplicas"] == 1
    pods = json.loads(
        _kubectl("get", "pods", "-l", "app.kubernetes.io/component=api", "-o", "json")
    )
    # Sized first: a selector that matches nothing, or a pod with no status yet, would
    # otherwise skip every restart and OOM assertion below and pass.
    assert len(pods["items"]) == 1, [p["metadata"]["name"] for p in pods["items"]]
    for pod in pods["items"]:
        statuses = pod["status"].get("containerStatuses", [])
        assert statuses, pod["metadata"]["name"]
        for status in statuses:
            assert status["restartCount"] == 0, status
            assert status.get("lastState", {}).get("terminated", {}).get("reason") != "OOMKilled"
    peak = int(
        _kubectl(
            "exec", "deploy/ticketscope-api", "--", "cat", "/sys/fs/cgroup/memory.peak"
        ).strip()
    )
    # The kernel can reclaim cache at the limit without an OOM. Successful requests
    # and zero restarts above establish that touching the limit did not kill the api.
    assert peak <= 512 * 1024 * 1024


def test_api_reports_ready_on_the_loaded_corpus() -> None:
    """Readiness: api's own /readyz, read inside the pod, says ready."""
    response = _kubectl(
        "exec",
        "deploy/ticketscope-api",
        "--",
        "python",
        "-c",
        "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/readyz')"
        ".read().decode())",
    )
    assert json.loads(response)["status"] == "ready"


@pytest.mark.parametrize(
    "query",
    [
        "my world disappears when I try to play",
        "Launcher crash java.lang.NullPointerException\n"
        "at net.minecraft.client.main.Main.main(Main.java:1)\n" * 100,
    ],
)
def test_hybrid_gateway_queries_and_tempo(query: str) -> None:
    url, host = gateway()
    trace_id = secrets.token_hex(16)
    response = httpx2.post(
        f"{url}/v1/search",
        json={"query": query, "mode": "hybrid", "k": 10},
        headers={"Host": host, "traceparent": f"00-{trace_id}-{secrets.token_hex(8)}-01"},
        timeout=60,
    )
    if not _dense_enabled():
        assert response.status_code == 503, response.text
        assert "not available" in response.json()["detail"]
        return
    assert response.status_code == 200, response.text
    body = SearchResponse.model_validate(response.json())
    assert body.mode == "hybrid" and body.score_kind == "rrf"
    assert len(body.results) == 10
    assert [r.rank for r in body.results] == list(range(1, 11))
    assert [(-r.score, r.issue.number) for r in body.results] == sorted(
        (-r.score, r.issue.number) for r in body.results
    )
    assert all(r.outcome.status for r in body.results)

    def trace_has_embeddings() -> None:
        status, text = tempo.trace_by_id(trace_id)
        assert status == 200, text
        spans = tempo.spans(json.loads(text))
        # `assert`, not unpacking: `eventually` retries AssertionError only, and Tempo may not
        # hold every span of the trace yet.
        retrievals = [s for s in spans if s["name"] == "retrieval hybrid"]
        embeddings = [s for s in spans if s["name"] == f"embeddings {MODEL}"]
        assert len(retrievals) == len(embeddings) == 1, spans
        assert embeddings[0]["parentSpanId"] == retrievals[0]["spanId"]

    eventually(trace_has_embeddings, timeout=60, interval=2)
