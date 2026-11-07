"""Kind derivation and the derivation version in core (story 4; test design R2, closed R-002).

The Jira outcome rules are covered in `test_derive_jira.py` and
`test_derive_jira_expanded.py`.
"""

import pytest

from tests.factories import snapshot_issue
from ticketscope.core.derive import (
    DEFAULT_KIND_THRESHOLD,
    KIND_RULE_VERSION,
    OUTCOME_RULE_VERSION,
    derivation_version,
    derive_kind,
    kind_score,
)

# --- kind -----------------------------------------------------------------------------------


def body_with_score(score: int) -> str:
    """A fenced block plus `score - 1` klog lines: score exactly `score` (>= 1)."""
    lines = [f"E1105 10:00:{i:02d}.000001 1 x.go:{i}] boom" for i in range(score - 1)]
    return "Intro.\n\n```\n" + "\n".join(lines) + "\n```\n"


@pytest.mark.parametrize("threshold", [2, 5, 10])
def test_kind_just_below_threshold_is_short(threshold: int) -> None:
    body = body_with_score(threshold - 1)
    assert kind_score(body) == threshold - 1
    assert derive_kind(snapshot_issue(body=body), threshold) == "short"


@pytest.mark.parametrize("threshold", [1, 5, 10])
def test_kind_at_threshold_is_log_heavy(threshold: int) -> None:
    body = body_with_score(threshold)
    assert kind_score(body) == threshold
    assert derive_kind(snapshot_issue(body=body), threshold) == "log_heavy"


@pytest.mark.parametrize("body", [None, ""])
def test_empty_body_is_short(body: str | None) -> None:
    assert derive_kind(snapshot_issue(body=body)) == "short"


@pytest.mark.parametrize("threshold", [0, -1])
def test_threshold_below_one_raises(threshold: int) -> None:
    with pytest.raises(ValueError):
        derive_kind(snapshot_issue(), threshold)
    with pytest.raises(ValueError):
        derivation_version(threshold)


def test_plain_body_scores_zero() -> None:
    assert kind_score("The controller ignores the annotation.\nExpected a default.") == 0


@pytest.mark.parametrize(
    "line",
    [
        "I1201 12:00:00.000001 1 drain.go:101] evicting",
        "2025-01-10T09:00:00Z something happened",
        'time="x" level=error msg="boom"',
        "panic: runtime error: nil pointer",
        "goroutine 1 [running]:",
        "Traceback (most recent call last):",
        '  File "app.py", line 3, in <module>',
        "\t/src/cache.go:88 +0x1c",
        "    at com.example.Main.run(Main.java:10)",
        "the pod reported ERROR on start",
        "WARNING: deprecated flag",
        'Error from server (Forbidden): admission webhook "x" denied the request',
        "error: unable to recognize manifest.yaml",
    ],
)
def test_log_like_line_scores_one(line: str) -> None:
    assert kind_score(line) == 1


@pytest.mark.parametrize(
    "line",
    [
        "Error handling in the controller is wrong: it retries forever",
        "  at the moment the pod restarts, the cache is empty",
    ],
)
def test_prose_line_scores_zero(line: str) -> None:
    assert kind_score(line) == 0


def test_fence_with_info_string_does_not_close() -> None:
    # Were "```yaml" a close, the last line would open a second fence (score 2).
    assert kind_score("```\nx\n```yaml\n```\n") == 1


def test_shorter_fence_run_does_not_close() -> None:
    # Were "```" a close, the last line would open a second fence (score 2).
    assert kind_score("````\n```\n````\n") == 1


def test_line_matching_several_patterns_counts_once() -> None:
    assert kind_score("E1105 10:00:01.000001 1 x.go:42] panic: ERROR level=fatal") == 1


def test_fences_count_openings_including_unclosed() -> None:
    assert kind_score("```\nplain\n```\n~~~\nplain\n~~~\n  ```yaml\nkind: Pod\n") == 3


# --- derivation version ---------------------------------------------------------------------


def test_derivation_version_names_every_rule() -> None:
    version = derivation_version()
    assert version == f"{KIND_RULE_VERSION}-t{DEFAULT_KIND_THRESHOLD}.{OUTCOME_RULE_VERSION}"


def test_derivation_version_changes_with_threshold() -> None:
    assert derivation_version(3) != derivation_version(4)
