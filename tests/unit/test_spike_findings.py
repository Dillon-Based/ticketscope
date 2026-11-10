"""Spike 3.3's findings file holds every figure its AC-1 names (epic 3 retro, G1).

AC-1: "it holds Recall@10 and MRR@10 by kind and overall for every candidate, embedding time
per issue and total, peak memory, image-size impact and the cut test." The integrated check
(`test_model_choice_record_names_the_chosen_model`) looks for headings; this reads the values.
"""

import re

import pytest

from tests.target import REPO

FINDINGS = (
    REPO
    / "_bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/tickets"
    / "spike-choose-the-embedding-model-findings.md"
)
SCORE = r"\*{0,2}0\.\d{3}\*{0,2}"  # a 3-decimal score, bold when it leads


def _text() -> str:
    return FINDINGS.read_text(encoding="utf-8")


def _candidates() -> set[str]:
    rows = re.findall(r"^\| ([\w.\-]+) \| (?:dense|hybrid) \|", _text(), re.MULTILINE)
    return set(rows)


def _section(heading: str) -> str:
    return _text().split(f"## {heading}")[1].split("\n## ")[0]


@pytest.mark.criterion("ticketscope--e3-s3--AC-1")
def test_quality_has_recall_and_mrr_by_kind_and_overall_for_every_candidate() -> None:
    candidates = _candidates()
    assert len(candidates) >= 2, candidates
    quality = _section("Quality")
    assert "| Overall | short | log_heavy |" in quality
    for model in candidates:
        for mode in ("dense", "hybrid"):
            # Three cells (overall, short, log_heavy), each "Recall@10 / MRR@10".
            cell = rf"{SCORE} / {SCORE}"
            row = rf"^\| {re.escape(model)} \| {mode} \| {cell} \| {cell} \| {cell} \|$"
            assert re.search(row, quality, re.MULTILINE), (model, mode)


@pytest.mark.criterion("ticketscope--e3-s3--AC-1")
def test_cost_has_cut_count_embed_time_and_memory_for_every_candidate() -> None:
    cost = _section("Cost")
    header = (
        "| Model | Dim | Token limit | Issues cut by the limit (of 32,153) |"
        " Embed time per issue / whole snapshot | Model size on disk |"
        " Memory after model load (process, MB) |"
    )
    assert header in cost
    for model in _candidates():
        match = re.search(
            rf"^\| {re.escape(model)} \| (\d+) \| (\d+) \| ([\d,]+) \(([\d.]+)%\) \|"
            r" ([\d.]+) ms / ([\d,]+) s \| (\d+) MB \| (\d+)",
            cost,
            re.MULTILINE,
        )
        assert match, f"no complete cost row for {model}"
        dim, limit, cut, _pct, per_issue_ms, total_s, size_mb, memory_mb = match.groups()
        assert int(dim) > 0 and int(limit) > 0
        assert int(cut.replace(",", "")) >= 0
        assert float(per_issue_ms) > 0 and int(total_s.replace(",", "")) > 0
        assert int(size_mb) > 0 and int(memory_mb) > 0


@pytest.mark.criterion("ticketscope--e3-s3--AC-1")
def test_image_size_impact_and_the_cut_test_are_recorded() -> None:
    cost = _section("Cost")
    assert re.search(r"^Image size: .*\d+ MB", cost, re.MULTILINE), "no image-size impact"
    limits = _section("Limits of this run (read before relying on the cost numbers)")
    assert "**The cut was tested, not varied.**" in limits
    assert re.search(r"cut at \d+ characters", _section("Recommendation"))
