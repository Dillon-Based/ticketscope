"""Smoke check against the kind cluster, through the Gateway (marker `kind`).

Needs `TICKETSCOPE_GATEWAY_URL` (e.g. `http://172.18.0.5`) and
`TICKETSCOPE_GATEWAY_HOST` (the route hostname), plus `kubectl` and `helm` on the cluster.
Run with `uv run pytest -m kind tests/smoke`.
"""

import json
import os
import subprocess

import httpx2
import pytest

from tests.target import NO_MATCH_QUERY, REPO, TARGET_NUMBER, TARGET_QUERY
from ticketscope.contract.search import SearchResponse

pytestmark = pytest.mark.kind

NAMESPACE = os.environ.get("TICKETSCOPE_NAMESPACE", "ticketscope")
CLUSTER = os.environ.get("TICKETSCOPE_CLUSTER_NAME", "ticketscope-db")


def _gateway() -> tuple[str, str]:
    url = os.environ.get("TICKETSCOPE_GATEWAY_URL")
    host = os.environ.get("TICKETSCOPE_GATEWAY_HOST")
    if not url or not host:
        pytest.fail("TICKETSCOPE_GATEWAY_URL and TICKETSCOPE_GATEWAY_HOST must be set")
    return url.rstrip("/"), host


def _search(query: str = TARGET_QUERY) -> SearchResponse:
    url, host = _gateway()
    response = httpx2.post(
        f"{url}/v1/search",
        json={"query": query, "mode": "keyword"},
        headers={"Host": host},
        timeout=30,
    )
    assert response.status_code == 200, response.text
    return SearchResponse.model_validate(response.json())


def test_keyword_search_through_the_gateway() -> None:
    body = _search()
    assert body.mode == "keyword"
    assert body.score_kind == "bm25"
    assert body.corpus_version == "fixture"
    assert body.results, "no results"
    assert body.results[0].issue.number == TARGET_NUMBER
    assert [r.rank for r in body.results] == list(range(1, len(body.results) + 1))
    scores = [r.score for r in body.results]
    assert scores == sorted(scores, reverse=True)
    for result in body.results:
        assert result.issue.number >= 900000
        assert result.outcome.status == "unknown"


def test_no_match_is_empty_through_the_gateway() -> None:
    body = _search(NO_MATCH_QUERY)
    assert body.corpus_version == "fixture"
    assert body.results == []


def test_cluster_has_two_ready_instances() -> None:
    out = subprocess.run(
        ["kubectl", "-n", NAMESPACE, "get", "clusters.postgresql.cnpg.io", CLUSTER, "-o", "json"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    status = json.loads(out)["status"]
    assert status.get("readyInstances") == 2, status


def test_load_rerun_replaces_the_corpus_without_duplicates() -> None:
    """A Helm upgrade with the same pin re-runs migrate and load and keeps the answers.

    `issue.number` is the primary key and `corpus_meta` has a singleton key, so a
    load that appended instead of replacing would fail its hook and the upgrade.
    """
    before = _search()
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
            "10m",
        ],
        check=True,
    )
    after = _search()
    assert after.corpus_version == "fixture"
    assert [r.issue.number for r in after.results] == [r.issue.number for r in before.results]
