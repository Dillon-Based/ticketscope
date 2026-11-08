"""Story 2.1 on kind (marker `kind`), run by eval.yml after kind-up with `eval.enabled`:
the eval Job completed after load as `ticketscope_ro`, keyword was scored over every pair
with the corpus lineage, the uploaded results hold no Secret value, and the pairs file
regenerates byte-identical from the pinned asset with the Release notes' counts.

Tests that read the results request `eval_results` (`conftest.py`), which writes
`reports/eval-results.json` from the Job's log first; the pairs check does not need the Job.
"""

import base64
import json
import subprocess
import sys
from typing import Any

import pytest

from tests.eval.conftest import EVAL_JOB, RESULTS_PATH
from tests.smoke.test_gateway import _corpus_meta, _kubectl
from tests.target import REPO

pytestmark = pytest.mark.kind

PAIRS = 10473
SHORT = 10164
LOG_HEAVY = 309
RO_SECRET = "ticketscope-db-ro"
OWNER_SECRET = "ticketscope-db-app"


def _job(name: str) -> dict[str, Any]:
    return json.loads(_kubectl("get", "job", name, "-o", "json"))


def _secret(name: str, key: str) -> str:
    raw = _kubectl("get", "secret", name, "-o", f"jsonpath={{.data.{key}}}").strip()
    return base64.b64decode(raw).decode("utf-8")


@pytest.mark.criterion("ticketscope--e2-s1--AC-1")
def test_eval_job_completed_after_load() -> None:
    job = _job(EVAL_JOB)
    complete = [c for c in job["status"].get("conditions", []) if c["type"] == "Complete"]
    assert complete and complete[0]["status"] == "True", job["status"]
    load = _job("ticketscope-load")
    # RFC 3339 UTC timestamps of one format compare as strings.
    assert load["status"]["completionTime"] <= job["status"]["startTime"]


@pytest.mark.criterion("ticketscope--e2-s1--AC-1")
def test_keyword_is_scored_over_every_pair(eval_results: dict[str, Any]) -> None:
    assert eval_results["k"] == 10
    assert eval_results["relevance"] == "target"
    keyword = eval_results["modes"]["keyword"]
    assert keyword["pairs_scored"] == PAIRS
    for metric in ("recall@10", "mrr@10"):
        assert isinstance(keyword[metric], float)
        assert 0.0 <= keyword[metric] <= 1.0
    assert keyword["mrr@10"] <= keyword["recall@10"]
    assert isinstance(eval_results["wall_seconds"], float)


@pytest.mark.criterion("ticketscope--e2-s1--AC-1")
def test_lineage_equals_corpus_meta(eval_results: dict[str, Any]) -> None:
    version, model, preprocessing = _corpus_meta()
    lineage = eval_results["lineage"]
    assert lineage["snapshot_version"] == version
    assert (lineage["embedding_model_id"] or "") == model
    assert (lineage["preprocessing_version"] or "") == preprocessing
    assert eval_results["pairs_file"] == f"eval/pairs/{version}.jsonl"


@pytest.mark.criterion("ticketscope--e2-s1--AC-1")
def test_eval_job_reads_as_ticketscope_ro() -> None:
    [container] = _job(EVAL_JOB)["spec"]["template"]["spec"]["containers"]
    refs = {
        env["valueFrom"]["secretKeyRef"]["name"]
        for env in container["env"]
        if "secretKeyRef" in env.get("valueFrom", {})
    }
    assert refs == {RO_SECRET}
    assert _secret(RO_SECRET, "username") == "ticketscope_ro"


@pytest.mark.criterion("ticketscope--e2-s1--AC-1")
def test_uploaded_results_hold_no_secret_value(eval_results: dict[str, Any]) -> None:
    text = RESULTS_PATH.read_text(encoding="utf-8")
    for name in (RO_SECRET, OWNER_SECRET):
        password = _secret(name, "password")
        assert password and password not in text, name
    assert "password" not in text.lower()


@pytest.mark.criterion("ticketscope--e2-s1--AC-1")
def test_pairs_regenerate_byte_identical_with_the_release_counts(
    pytestconfig: pytest.Config,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "derive_pairs.py"),
            "--check",
            "--snapshot-dir",
            str(pytestconfig.cache.mkdir("ticketscope-snapshot")),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"{PAIRS} pairs: {SHORT} short, {LOG_HEAVY} log_heavy" in result.stdout
