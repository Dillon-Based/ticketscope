"""Smoke and load checks against the kind cluster on the pinned snapshot (marker `kind`).

Needs `TICKETSCOPE_GATEWAY_URL` (e.g. `http://172.18.0.5`) and
`TICKETSCOPE_GATEWAY_HOST` (the route hostname), plus `kubectl` and `helm` on the cluster.
Run with `uv run pytest -m kind tests/smoke`. The tests run in file order: (1) search
through the Gateway, (1b) the rest of the /v1 contract through the Gateway, (2) SQL on
the CNPG primary, (3) the load report, (4) a same-pin upgrade is a no-op, (5) a stale
preprocessing version reloads, (6) two ready instances.
"""

import json
import os
import re
import subprocess

import httpx2
import pytest

from tests.target import NO_MATCH_QUERY, REPO, snapshot_pin
from ticketscope.contract.search import IssueResponse, Problem, SearchResponse
from ticketscope.core.derive import preprocessing_version

pytestmark = pytest.mark.kind

NAMESPACE = os.environ.get("TICKETSCOPE_NAMESPACE", "ticketscope")
CLUSTER = os.environ.get("TICKETSCOPE_CLUSTER_NAME", "ticketscope-db")
PIN = snapshot_pin()["version"]
ISSUE_COUNT = 32153  # issues in snapshot 2026.11.1
RESULTS_QUERY = "launcher crash"
OUTCOMES = ("fixed", "duplicate", "not_planned", "stale", "answered", "unknown")


def _gateway() -> tuple[str, str]:
    url = os.environ.get("TICKETSCOPE_GATEWAY_URL")
    host = os.environ.get("TICKETSCOPE_GATEWAY_HOST")
    if not url or not host:
        pytest.fail("TICKETSCOPE_GATEWAY_URL and TICKETSCOPE_GATEWAY_HOST must be set")
    return url.rstrip("/"), host


def _post_search(payload: dict[str, object]) -> httpx2.Response:
    url, host = _gateway()
    return httpx2.post(f"{url}/v1/search", json=payload, headers={"Host": host}, timeout=30)


def _search(query: str) -> SearchResponse:
    response = _post_search({"query": query, "mode": "keyword"})
    assert response.status_code == 200, response.text
    return SearchResponse.model_validate(response.json())


def _get_issue(number: int) -> httpx2.Response:
    url, host = _gateway()
    return httpx2.get(f"{url}/v1/issues/{number}", headers={"Host": host}, timeout=30)


def _assert_problem(response: httpx2.Response, status: int) -> Problem:
    assert response.status_code == status, response.text
    assert response.headers["content-type"].startswith("application/problem+json")
    problem = Problem.model_validate(response.json())
    assert (problem.type, problem.status) == ("about:blank", status)
    assert problem.title and problem.detail
    return problem


def _kubectl(*args: str) -> str:
    return subprocess.run(
        ["kubectl", "-n", NAMESPACE, *args], check=True, capture_output=True, text=True
    ).stdout


def _sql(statement: str) -> str:
    """Run `statement` with psql on the CNPG primary; return its unaligned output."""
    pod = _kubectl(
        "get",
        "pod",
        "-l",
        f"cnpg.io/cluster={CLUSTER},cnpg.io/instanceRole=primary",
        "-o",
        "jsonpath={.items[0].metadata.name}",
    ).strip()
    assert pod, "no CNPG primary pod"
    return _kubectl("exec", pod, "-c", "postgres", "--", "psql", "-d", "app", "-tAc", statement)


def _corpus_meta() -> tuple[str, str, str]:
    """`snapshot_version|embedding_model_id|preprocessing_version` (NULL reads as '')."""
    row = _sql(
        "SELECT snapshot_version, coalesce(embedding_model_id, ''),"
        " coalesce(preprocessing_version, '') FROM corpus_meta"
    ).strip()
    version, model, pre = row.split("|")
    return version, model, pre


def _load_log() -> str:
    """The log of the load Job's Succeeded pod (newest if several): with `backoffLimit`,
    `kubectl logs job/...` may pick a failed attempt."""
    pods = _kubectl(
        "get",
        "pod",
        "-l",
        "job-name=ticketscope-load",
        "--field-selector",
        "status.phase=Succeeded",
        "--sort-by",
        ".metadata.creationTimestamp",
        "-o",
        "jsonpath={.items[*].metadata.name}",
    ).split()
    assert pods, "no Succeeded ticketscope-load pod"
    return _kubectl("logs", pods[-1])


def _upgrade() -> None:
    """A Helm upgrade with the same values: re-runs migrate and load as hooks."""
    subprocess.run(
        [
            "helm",
            "upgrade",
            "ticketscope",
            str(REPO / "deploy" / "charts" / "ticketscope"),
            "-n",
            NAMESPACE,
            "--reuse-values",
            "--timeout",
            "15m",
        ],
        check=True,
    )


# (1) ---------------------------------------------------------------------------------------


def test_search_serves_the_pinned_snapshot_with_outcomes() -> None:
    body = _search(RESULTS_QUERY)
    assert body.mode == "keyword"
    assert body.score_kind == "bm25"
    assert body.corpus_version == PIN
    assert body.results, "no results"
    assert [r.rank for r in body.results] == list(range(1, len(body.results) + 1))
    scores = [r.score for r in body.results]
    assert scores == sorted(scores, reverse=True)
    assert all(r.outcome.status in OUTCOMES for r in body.results)
    assert any(r.outcome.status != "unknown" for r in body.results)


def test_no_match_is_empty_through_the_gateway() -> None:
    body = _search(NO_MATCH_QUERY)
    assert body.corpus_version == PIN
    assert body.results == []


# (1b) --------------------------------------------------------------------------------------


def test_issue_detail_matches_the_search_hit() -> None:
    top = _search(RESULTS_QUERY).results[0]
    response = _get_issue(top.issue.number)
    assert response.status_code == 200, response.text
    body = IssueResponse.model_validate(response.json())
    assert body.issue.number == top.issue.number
    assert body.issue.body, "empty body"
    assert body.outcome == top.outcome


def test_unknown_issue_is_a_404_problem() -> None:
    problem = _assert_problem(_get_issue(1), 404)
    assert "1" in problem.detail


@pytest.mark.parametrize(
    "payload",
    [
        {"query": RESULTS_QUERY, "mode": "keyword", "k": 0},
        {"query": RESULTS_QUERY, "mode": "keyword", "k": 51},
        {"query": RESULTS_QUERY, "mode": "nope"},
    ],
    ids=["k=0", "k=51", "mode=nope"],
)
def test_invalid_search_is_a_422_problem(payload: dict[str, object]) -> None:
    problem = _assert_problem(_post_search(payload), 422)
    assert problem.errors


def test_operator_characters_rank() -> None:
    body = _search('crash & launcher | (java:!) !! "x')
    assert body.results, "no results"


def test_a_pasted_stack_trace_of_4kb_ranks() -> None:
    frames = [
        "\tat net.minecraft.client.renderer.GameRenderer.render(GameRenderer.java:{n})",
        "\tat net.minecraft.client.Minecraft.runTick(Minecraft.java:{n})",
        "\tat com.mojang.blaze3d.systems.RenderSystem.flipFrame(RenderSystem.java:{n})",
    ]
    trace = 'java.lang.NullPointerException: Cannot invoke "Object.toString()"\n' + "\n".join(
        frames[i % len(frames)].format(n=100 + i) for i in range(60)
    )
    assert len(trace.encode()) >= 4096
    body = _search("Game crashed on launch\n" + trace)
    assert body.results, "no results"


# (2) ---------------------------------------------------------------------------------------


def test_every_issue_is_loaded_with_a_kind_and_an_outcome() -> None:
    assert int(_sql("SELECT count(*) FROM issue")) == ISSUE_COUNT
    missing = _sql(
        "SELECT count(*) FROM issue WHERE coalesce(kind, '') = ''"
        " OR coalesce(outcome_status, '') = ''"
    )
    assert int(missing) == 0
    assert int(_sql("SELECT count(DISTINCT outcome_status) FROM issue")) > 1
    assert _corpus_meta() == (PIN, "", preprocessing_version())


# (3) ---------------------------------------------------------------------------------------


def test_load_log_has_the_report() -> None:
    reports = [line for line in _load_log().splitlines() if "load report:" in line]
    assert reports, "no load report line"
    line = reports[-1]
    assert f"issues={ISSUE_COUNT}" in line
    kinds = dict(re.findall(r"kind\.(\w+)=([\d.]+)%", line))
    assert set(kinds) == {"short", "log_heavy"}
    outcomes = dict(re.findall(r"outcome\.(\w+)=([\d.]+)%", line))
    assert set(outcomes) == set(OUTCOMES)
    assert "budget_seconds=600" in line
    assert "within_budget=true" in line


# (4) ---------------------------------------------------------------------------------------


def test_upgrade_with_the_same_pin_is_a_no_op() -> None:
    _upgrade()
    log = _load_log()
    assert "no-op" in log, log
    assert "load report:" not in log
    assert _search(RESULTS_QUERY).corpus_version == PIN


# (5) ---------------------------------------------------------------------------------------


def test_stale_preprocessing_version_reloads() -> None:
    current = (PIN, "", preprocessing_version())
    _sql("UPDATE corpus_meta SET preprocessing_version = 'pre0.stale'")
    try:
        _upgrade()
        log = _load_log()
        assert "reloading" in log and "preprocessing_version" in log, log
        assert "load report:" in log
        assert _corpus_meta() == current
    finally:
        # Never leave corpus_meta stale: a failed check above still gets one more reload.
        if _corpus_meta() != current:
            _upgrade()


# (6) ---------------------------------------------------------------------------------------


def test_cluster_has_two_ready_instances() -> None:
    out = _kubectl("get", "clusters.postgresql.cnpg.io", CLUSTER, "-o", "json")
    status = json.loads(out)["status"]
    assert status.get("readyInstances") == 2, status
