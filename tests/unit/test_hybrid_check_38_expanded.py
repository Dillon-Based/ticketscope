"""Cluster-free coverage of story 3.8's integrated check: the pieces it reads statically."""

import ast
import json

from tests.integrated import test_hybrid_check as check
from tests.target import REPO


def _test_names(path: str) -> set[str]:
    tree = ast.parse((REPO / "tests" / "integrated" / path).read_text())
    return {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def test_default_mode_is_a_known_mode() -> None:
    assert check._default_mode() in check.MODES


def test_chart_default_matches_best_overall_baseline_mrr() -> None:
    overall = {m: check._baseline()[m]["overall"]["mrr@10"] for m in check.MODES}
    best = max(overall.values())
    expected = "hybrid" if overall["hybrid"] == best else max(overall, key=overall.__getitem__)
    assert check._default_mode() == expected


def test_baseline_modes_cover_every_kind() -> None:
    for mode in check.MODES:
        assert set(check.KINDS) <= set(check._baseline()[mode])


def test_docstring_references_existing_tests() -> None:
    names = _test_names("test_hybrid_check.py") | _test_names("test_dense_kind.py")
    for ref in (
        "test_dense_corpus_and_load",
        "test_api_survives_dense_load_within_its_memory_budget",
        "test_api_reports_ready_on_the_loaded_corpus",
        "test_dense_gateway_queries_and_tempo",
        "test_hybrid_gateway_queries_and_tempo",
        "test_model_choice_record_names_the_chosen_model",
        "test_committed_baseline_and_readme_carry_all_three_modes",
        "test_omitted_mode_is_served_by_the_chart_default",
        "test_readiness_fails_on_a_model_mismatch",
    ):
        assert ref in names, ref


def test_baseline_file_is_json_with_modes() -> None:
    # The value, not the key: an empty, null or partial `modes` must fail.
    modes = json.loads((REPO / "eval" / "baseline.json").read_text())["modes"]
    assert set(modes) == {"keyword", "dense", "hybrid"}
