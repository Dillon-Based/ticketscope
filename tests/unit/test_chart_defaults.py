"""The chart defaults that carry the model's needs and the best mode (story 3.6, R5)."""

import json
import re

from tests.target import CHART_VALUES, REPO


def _values() -> str:
    return CHART_VALUES.read_text(encoding="utf-8")


def test_default_mode_is_the_best_overall_mrr_in_the_baseline() -> None:
    modes = json.loads((REPO / "eval" / "baseline.json").read_text(encoding="utf-8"))["modes"]
    mrr = {name: doc["overall"]["mrr@10"] for name, doc in modes.items()}
    best = max(mrr.values())
    leaders = [name for name, value in mrr.items() if value == best]
    expected = "hybrid" if "hybrid" in leaders else leaders[0]
    match = re.search(r"^retrieval:\n(?:[ #].*\n)*?  defaultMode: (\w+)$", _values(), re.MULTILINE)
    assert match, "retrieval.defaultMode not found in values.yaml"
    assert match.group(1) == expected


def test_default_mode_comment_records_the_number_it_chose_by() -> None:
    comment = _values().split("defaultMode:")[0].rsplit("retrieval:", 1)[1]
    modes = json.loads((REPO / "eval" / "baseline.json").read_text(encoding="utf-8"))["modes"]
    # Every mode is checked: an empty or partial baseline must fail, not check fewer numbers.
    assert set(modes) == {"keyword", "dense", "hybrid"}
    for name, doc in modes.items():
        assert f"{name} {doc['overall']['mrr@10']:.4f}" in comment


def test_api_resources_set_cpu_and_memory_requests_and_limits() -> None:
    block = re.search(
        r"^api:\n(?:[ #].*\n)*?    requests:\n((?:      .*\n)+)    limits:\n((?:      .*\n)+)",
        _values(),
        re.MULTILINE,
    )
    assert block, "api.resources not found in values.yaml"
    requests, limits = block.groups()
    assert "cpu:" in requests and "memory:" in requests
    assert "cpu:" in limits and "memory:" in limits


def test_values_comments_name_the_measured_memory_and_embedding_time() -> None:
    api = _values().split("\napi:\n")[1].split("\njobs:")[0]
    assert "288 MB" in api and "peak" in api
    assert "35.7 ms per issue" in api
