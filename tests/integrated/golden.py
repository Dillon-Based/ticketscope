"""The golden-query verdict (R-004) and its report, pure so the unit run covers them.

A gated entry (`known_keyword_miss: false`) fails when its expected issue is absent from
the top-k. A recorded known keyword miss is reported but never gated; if it comes back,
it passes with a note so the file can be updated.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

Status = Literal["pass", "fail", "known-miss"]
KNOWN_MISS_FOUND = "known miss now found"


@dataclass(frozen=True)
class Verdict:
    status: Status
    rank: int | None  # 1-based rank of the expected issue, or None when absent
    note: str = ""


def twin_verdict(known_keyword_miss: bool, expected: int, ranked: list[int]) -> Verdict:
    """The verdict for one golden entry, given the returned issue numbers in rank order."""
    rank = ranked.index(expected) + 1 if expected in ranked else None
    if rank is not None:
        return Verdict("pass", rank, KNOWN_MISS_FOUND if known_keyword_miss else "")
    if known_keyword_miss:
        return Verdict("known-miss", None, "recorded known keyword miss, not gated")
    return Verdict("fail", None)


def results_without_outcome(
    results: Sequence[dict[str, object]], outcomes: Sequence[str]
) -> list[object]:
    """Issue numbers of raw `/v1/search` results whose outcome status is empty or not one
    of `outcomes` (the contract's)."""
    bad: list[object] = []
    for result in results:
        outcome = result.get("outcome")
        status = outcome.get("status") if isinstance(outcome, dict) else None
        if status not in outcomes:
            issue = result.get("issue")
            bad.append(issue.get("number") if isinstance(issue, dict) else issue)
    return bad


def page_rank(hrefs: Sequence[str], key: str) -> int | None:
    """1-based row of the page whose title href ends in `/<key>`, or None."""
    for rank, href in enumerate(hrefs, start=1):
        if href.rstrip("/").endswith(f"/{key}"):
            return rank
    return None


@dataclass(frozen=True)
class GoldenRow:
    entry_id: str
    kind: str
    expected_key: str
    verdict: Verdict


def summary_table(rows: Sequence[GoldenRow], *, k: int, mode: str) -> str:
    """A Markdown table of the golden results, for the pytest output and the job summary."""
    lines = [
        f"Golden queries ({mode}, top-{k})",
        "",
        "| entry | kind | expected | verdict | rank | note |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        v = row.verdict
        rank = str(v.rank) if v.rank is not None else "absent"
        lines.append(
            f"| {row.entry_id} | {row.kind} | {row.expected_key} | {v.status} | {rank} | {v.note} |"
        )
    return "\n".join(lines) + "\n"
