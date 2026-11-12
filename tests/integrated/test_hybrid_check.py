"""The hybrid-retrieval epic's integrated check (epic 3, story 8), on the kind cluster.

Run in CI by `integrated-check` with the rest of `tests/integrated`. Each Done when line is
covered by one named check, so a broken part fails exactly its own test:

- R1, load from the pinned asset, `corpus_meta` model id, nothing computed:
  `test_dense_kind.py::test_dense_corpus_and_load`.
- R2, a vague and a log-heavy query ranked with outcomes in dense and in hybrid:
  `test_dense_kind.py::test_dense_gateway_queries_and_tempo` and
  `::test_hybrid_gateway_queries_and_tempo`.
- R3, the model choice record: `test_model_choice_record_names_the_chosen_model`.
- R4, the eval artifact with all three modes (the CI eval run's committed baseline and the
  README table; the live eval Job is checked by `tests/eval` in the eval workflow):
  `test_committed_baseline_and_readme_carry_all_three_modes`.
- R5, the api resources and dense answers within them:
  `test_dense_kind.py::test_api_survives_dense_load_within_its_memory_budget`.
  A request without `mode` served by the chart default, and readiness on a model mismatch:
  `test_omitted_mode_is_served_by_the_chart_default`, `test_readiness_fails_on_a_model_mismatch`.
- Readiness on the loaded corpus: `test_dense_kind.py::test_api_reports_ready_on_the_loaded_corpus`.
"""

import json
import re
from typing import Any

import httpx2
import pytest

from tests.kind import gateway
from tests.smoke.test_gateway import _kubectl, _sql
from tests.target import CHART_VALUES, REPO, embeddings_pin
from tests.waiting import eventually
from ticketscope.contract.search import SearchResponse

pytestmark = pytest.mark.kind

KINDS = ("short", "log_heavy", "overall")
MODES = ("keyword", "dense", "hybrid")
FINDINGS = next(
    (REPO / "_bmad-output" / "initiative-ticketscope" / "tickets" / "epic-hybrid-retrieval").glob(
        "tickets/spike-*embedding-model-findings.md"
    )
)


def _default_mode() -> str:
    match = re.search(r"^\s*defaultMode:\s*(\w+)", CHART_VALUES.read_text(), re.MULTILINE)
    assert match, "values.yaml has no retrieval.defaultMode"
    return match.group(1)


def _baseline() -> dict[str, dict[str, Any]]:
    return json.loads((REPO / "eval" / "baseline.json").read_text())["modes"]


def test_omitted_mode_is_served_by_the_chart_default() -> None:
    mode = _default_mode()
    env = json.loads(_kubectl("get", "deploy/ticketscope-api", "-o", "json"))["spec"]["template"][
        "spec"
    ]["containers"][0]["env"]
    assert {e["name"]: e.get("value") for e in env}["TICKETSCOPE_DEFAULT_MODE"] == mode
    # The chart default is the best overall MRR@10 of the committed baseline, hybrid on a tie.
    overall = {name: _baseline()[name]["overall"]["mrr@10"] for name in MODES}
    best = max(overall.values())
    assert mode == (
        "hybrid" if overall["hybrid"] == best else max(overall, key=overall.__getitem__)
    )
    url, host = gateway()
    response = httpx2.post(
        f"{url}/v1/search",
        json={"query": "my world disappears when I try to play", "k": 10},
        headers={"Host": host},
        timeout=60,
    )
    assert response.status_code == 200, response.text
    body = SearchResponse.model_validate(response.json())
    assert body.mode == mode and len(body.results) == 10
    assert all(r.outcome.status for r in body.results)


def _readyz() -> tuple[int, str]:
    """The api pod's own `/readyz`: status code and body (a 503 is data, not an error)."""
    script = (
        "import urllib.request, urllib.error\n"
        "try:\n"
        "    r = urllib.request.urlopen('http://127.0.0.1:8080/readyz')\n"
        "    print(r.status, r.read().decode())\n"
        "except urllib.error.HTTPError as e:\n"
        "    print(e.code, e.read().decode())\n"
    )
    out = _kubectl("exec", "deploy/ticketscope-api", "-c", "api", "--", "python", "-c", script)
    code, _, body = out.strip().partition(" ")
    return int(code), body


def _assert_ready() -> None:
    assert _readyz()[0] == 200


def test_readiness_fails_on_a_model_mismatch() -> None:
    model = _sql("SELECT embedding_model_id FROM corpus_meta").strip()
    assert model == embeddings_pin()["modelId"]
    assert _readyz()[0] == 200
    _sql("UPDATE corpus_meta SET embedding_model_id = 'integrated/not-the-api-model'")
    try:
        code, body = _readyz()
        assert code == 503, body
        assert "embedding model mismatch" in body
    finally:
        _sql(f"UPDATE corpus_meta SET embedding_model_id = '{model}'")
    # Assert, not fail: `eventually` retries AssertionError only.
    eventually(lambda: _assert_ready(), timeout=60, interval=2)
    _kubectl(
        "wait", "--for=condition=Ready", "pod", "-l", "app.kubernetes.io/component=api",
        "--timeout=60s",
    )  # fmt: skip


def test_model_choice_record_names_the_chosen_model() -> None:
    text = FINDINGS.read_text()
    assert embeddings_pin()["modelId"] in text.split("## Quality")[0], "the choice is not named"
    for needle in ("Recall@10", "MRR@10", "short", "log_heavy", "Embed time", "Memory"):
        assert needle in text, needle
    candidates = re.findall(r"^\| ([\w.\-]+) \| (?:dense|hybrid) \|", text, re.MULTILINE)
    assert len(set(candidates)) >= 2, candidates


def test_committed_baseline_and_readme_carry_all_three_modes() -> None:
    baseline = _baseline()
    assert set(baseline) == set(MODES)
    results = json.loads((REPO / "eval" / "baseline.json").read_text())
    assert results["skipped_modes"] == []
    block = (REPO / "README.md").read_text().split("<!-- eval-results:start -->")[1]
    block = block.split("<!-- eval-results:end -->")[0]
    for mode in MODES:
        for kind in KINDS:
            assert baseline[mode][kind]["pairs_scored"] > 0, (mode, kind)
            assert re.search(rf"^\| {mode} \| {kind} \|", block, re.MULTILINE), (mode, kind)
