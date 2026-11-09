"""Stories 2.1 and 2.2 on kind (marker `kind`), run by eval.yml after kind-up with
`eval.enabled`: the eval Job completed after load as `ticketscope_ro`, keyword was scored
on cluster relevance over every pair, split short, log-heavy and overall, with the corpus
lineage, each query's first-member rank (recomputed here independently) and the cost,
the uploaded results hold no Secret value, and the pairs
file regenerates byte-identical from the pinned asset with the Release notes' counts.

Tests that read the results request `eval_results` (`conftest.py`), which writes
`reports/eval-results.json` from the Job's log first; the pairs check does not need the Job.
"""

import base64
import json
import subprocess
import sys
from collections.abc import Callable
from typing import Any

import pytest

from tests.eval.conftest import EVAL_JOB, RESULTS_PATH
from tests.smoke.test_gateway import _corpus_meta, _kubectl
from tests.target import REPO
from ticketscope.core.modes import REGISTRY
from ticketscope.core.pairs import read_pairs

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


@pytest.mark.criterion("ticketscope--e2-s1--AC-2")
def test_eval_job_completed_after_load() -> None:
    job = _job(EVAL_JOB)
    complete = [c for c in job["status"].get("conditions", []) if c["type"] == "Complete"]
    assert complete and complete[0]["status"] == "True", job["status"]
    load = _job("ticketscope-load")
    # RFC 3339 UTC timestamps of one format compare as strings.
    assert load["status"]["completionTime"] <= job["status"]["startTime"]


KINDS = ("short", "log_heavy", "overall")
METRICS = ("recall@1", "recall@5", "recall@10", "mrr@10")


def _recompute(ranks: list[list[Any]], kinds: dict[int, str], kind: str) -> dict[str, float]:
    """Metrics for `kind` from the first-member ranks alone; overall is over every query."""
    chosen = [rank for query, rank in ranks if kind == "overall" or kinds[query] == kind]
    n = len(chosen)

    def rate(hit: Callable[[int], bool]) -> float:
        return sum(1 for r in chosen if r is not None and hit(r)) / n

    return {
        "recall@1": rate(lambda r: r <= 1),
        "recall@5": rate(lambda r: r <= 5),
        "recall@10": rate(lambda r: r <= 10),
        "mrr@10": sum(1 / r for r in chosen if r is not None and r <= 10) / n,
    }


@pytest.mark.criterion("ticketscope--e2-s2--AC-4")
def test_keyword_is_scored_on_clusters_split_by_kind(eval_results: dict[str, Any]) -> None:
    assert eval_results["k"] == 10
    assert eval_results["relevance"] == "cluster"
    # Every registered mode is either scored or named as skipped, so a mode whose
    # embeddings are not loaded (dense, hybrid) is skipped without failing this check.
    assert "keyword" not in eval_results["skipped_modes"]
    assert set(eval_results["modes"]) | set(eval_results["skipped_modes"]) == set(REGISTRY)
    assert not set(eval_results["modes"]) & set(eval_results["skipped_modes"])
    keyword = eval_results["modes"]["keyword"]
    assert {kind: keyword[kind]["pairs_scored"] for kind in KINDS} == {
        "short": SHORT,
        "log_heavy": LOG_HEAVY,
        "overall": PAIRS,
    }
    for kind in KINDS:
        for metric in METRICS:
            assert isinstance(keyword[kind][metric], float)
            assert 0.0 <= keyword[kind][metric] <= 1.0
        assert keyword[kind]["recall@1"] <= keyword[kind]["recall@5"] <= keyword[kind]["recall@10"]
        assert keyword[kind]["mrr@10"] <= keyword[kind]["recall@10"]
        assert keyword[kind]["p95_latency_ms"] > 0.0
    assert isinstance(eval_results["wall_seconds"], float)
    assert eval_results["wall_seconds"] > 0.0


@pytest.mark.criterion("ticketscope--e2-s2--AC-4")
def test_first_member_ranks_recompute_to_the_reported_metrics(
    eval_results: dict[str, Any],
) -> None:
    keyword = eval_results["modes"]["keyword"]
    ranks = keyword["first_member_ranks"]
    pairs = read_pairs((REPO / eval_results["pairs_file"]).read_bytes())
    kinds = {pair.query: pair.kind for pair in pairs}
    assert [query for query, _rank in ranks] == sorted(kinds)
    assert all(rank is None or (type(rank) is int and 1 <= rank <= 10) for _, rank in ranks)
    for kind in KINDS:
        assert keyword[kind] | _recompute(ranks, kinds, kind) == pytest.approx(keyword[kind])


@pytest.mark.criterion("ticketscope--e2-s1--AC-2")
def test_lineage_equals_corpus_meta(eval_results: dict[str, Any]) -> None:
    version, model, preprocessing = _corpus_meta()
    lineage = eval_results["lineage"]
    assert lineage["snapshot_version"] == version
    assert (lineage["embedding_model_id"] or "") == model
    assert (lineage["preprocessing_version"] or "") == preprocessing
    assert eval_results["pairs_file"] == f"eval/pairs/{version}.jsonl"


@pytest.mark.criterion("ticketscope--e2-s1--AC-2")
def test_eval_job_reads_as_ticketscope_ro() -> None:
    [container] = _job(EVAL_JOB)["spec"]["template"]["spec"]["containers"]
    refs = {
        env["valueFrom"]["secretKeyRef"]["name"]
        for env in container["env"]
        if "secretKeyRef" in env.get("valueFrom", {})
    }
    assert refs == {RO_SECRET}
    assert _secret(RO_SECRET, "username") == "ticketscope_ro"


@pytest.mark.criterion("ticketscope--e2-s1--AC-2")
def test_uploaded_results_hold_no_secret_value(eval_results: dict[str, Any]) -> None:
    text = RESULTS_PATH.read_text(encoding="utf-8")
    for name in (RO_SECRET, OWNER_SECRET):
        password = _secret(name, "password")
        assert password and password not in text, name
    assert "password" not in text.lower()


@pytest.mark.criterion("ticketscope--e2-s1--AC-5")
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


@pytest.mark.criterion("ticketscope--e2-s2--AC-3", "ticketscope--e2-s2--AC-4")
def test_recorded_ranks_match_an_independent_second_retrieval_pass(
    eval_results: dict[str, Any],
) -> None:
    # Read through the real adapter and read-only credentials, independently of score's
    # rank helper and tallies. This also checks full-corpus retrieval reproducibility.
    script = r"""
import json
from ticketscope.adapters.postgres import PostgresCorpusStore, read_corpus_meta
from ticketscope.core.modes import KeywordRetriever
from ticketscope.core.pairs import read_pairs
from ticketscope.settings import Settings

settings = Settings()
store = PostgresCorpusStore(settings.conninfo())
meta = read_corpus_meta(settings.conninfo())
pairs = read_pairs((settings.eval_pairs_dir / f"{meta.snapshot_version}.jsonl").read_bytes())
retriever = KeywordRetriever(store)
ranks = []
for pair in pairs:
    detail = store.get_issue(pair.query)
    text = f"{detail.issue.title}\n\n{detail.body or ''}"
    hits = retriever.search(text, 10, exclude=frozenset({pair.query}))
    rank = next((i for i, hit in enumerate(hits, 1) if hit.issue.number in pair.relevant), None)
    ranks.append([pair.query, rank])
print(json.dumps(sorted(ranks)))
"""
    actual = json.loads(
        _kubectl("exec", "deploy/ticketscope-api", "-c", "api", "--", "python", "-c", script)
    )
    assert actual == eval_results["modes"]["keyword"]["first_member_ranks"]
