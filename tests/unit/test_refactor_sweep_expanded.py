"""Expanded coverage for story 10 (refactor sweep).

The sweep retired the GitHub (schema v1) snapshot shapes and outcome rules from core,
kept the derivation and preprocessing versions, made `kind-up.sh` restart api after a
rebuild under the deployed tag (DW-2), and dropped the missing-`Chart.lock` fallback
from CI and `kind-up.sh`.

`kind-up.sh` is exercised for real here, against stub `docker`, `kind`, `kubectl`,
`helm`, `git` and `uname` binaries on `PATH`. Each stub appends its argv to a call log,
so the tests assert which commands ran and in what order, without a cluster.
"""

import os
import re
import stat
import subprocess
from pathlib import Path

import pytest

from tests.target import REPO
from ticketscope.core import derive, snapshot

KIND_UP = REPO / "scripts" / "kind-up.sh"
CI = REPO / ".github" / "workflows" / "ci.yml"
TAG = "deadbeef"
APP_IMAGE = f"ticketscope-app:{TAG}"
PG_IMAGE = f"ticketscope-postgres:18-{TAG}"

# --- retired v1 surface (AC 1) ---------------------------------------------------------------

# Assembled from pieces, so this file never names a retired symbol and the plan's own
# `grep -rnE ... src tests` stays empty with it in the tree.
_V1_ISSUE = "Snapshot" + "Issue"
_V1_EVENT = "Timeline" + "Event"
_GH_OUTCOME = "_github" + "_outcome"
_MAINTAINERS = "MAINTAINER" + "_ASSOCIATIONS"
_RETIRED = re.compile(rf"{_V1_ISSUE}([^V]|$)|{_V1_EVENT}|{_GH_OUTCOME}|{_MAINTAINERS}")


def _retired_symbols_in(path: Path) -> list[str]:
    return [
        f"{path.relative_to(REPO)}:{n}: {line.strip()}"
        for n, line in enumerate(path.read_text("utf-8").splitlines(), 1)
        if _RETIRED.search(line)
    ]


def test_no_source_or_test_names_a_retired_v1_symbol() -> None:
    """The plan's AC grep, as a regression guard, over every file it would read."""
    hits = []
    for root in (REPO / "src", REPO / "tests"):
        for path in root.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            hits.extend(_retired_symbols_in(path))
    assert not hits, "\n".join(hits)


@pytest.mark.parametrize("name", ["SCHEMA_VERSION", "Label", "Comment", _V1_EVENT, _V1_ISSUE])
def test_snapshot_module_no_longer_exports_v1_shapes(name: str) -> None:
    assert not hasattr(snapshot, name)


@pytest.mark.parametrize("name", ["JiraComment", "DuplicateLink", "SnapshotIssueV2", "_Frozen"])
def test_snapshot_module_keeps_the_v2_shapes(name: str) -> None:
    assert hasattr(snapshot, name)


@pytest.mark.parametrize(
    "name",
    [
        "DUPLICATE_LABEL",
        "STALE_LABELS",
        "SUPPORT_LABEL",
        _MAINTAINERS,
        "_PR_EVENTS",
        _GH_OUTCOME,
        "_event_key",
        "_duplicate",
        "_fixed",
        "_not_planned",
        "_stale",
        "_comment_key",
        "_answered",
    ],
)
def test_derive_module_no_longer_carries_github_rules(name: str) -> None:
    assert not hasattr(derive, name)


# --- versions unchanged (AC 2) ---------------------------------------------------------------


def test_preprocessing_version_is_unchanged_by_the_sweep() -> None:
    """A changed version would force every deployed corpus to reload."""
    assert derive.preprocessing_version() == "pre1.kind2-t3.outcome3"
    assert derive.derivation_version() == "kind2-t3.outcome3"


def test_a_jira_code_toggle_body_is_log_heavy_without_an_isinstance_branch() -> None:
    """`derive_kind` now always applies `jira_to_fences`: a `{code}` block of log
    lines scores like a fenced one."""
    from tests.factories import snapshot_issue
    from tests.unit.test_derive import body_with_score

    fenced = body_with_score(derive.DEFAULT_KIND_THRESHOLD)
    jira = fenced.replace("```", "{code}")
    assert derive.derive_kind(snapshot_issue(body=jira)) == "log_heavy"
    assert derive.derive_kind(snapshot_issue(body=jira)) == derive.derive_kind(
        snapshot_issue(body=fenced)
    )


# --- CI: dependencies from the lock only ----------------------------------------------------


def test_ci_builds_platform_dependencies_from_the_lock_only() -> None:
    text = CI.read_text("utf-8")
    assert "helm dependency build deploy/charts/platform" in text
    assert "helm dependency update" not in text
    assert "Chart.lock is missing" not in text


def test_kind_up_builds_platform_dependencies_from_the_lock_only() -> None:
    text = KIND_UP.read_text("utf-8")
    assert "helm dependency update" not in text
    assert "Chart.lock" not in text


# --- kind-up.sh behaviour, on stub tools -----------------------------------------------------

_STUB = """#!/usr/bin/env bash
echo "{name} $*" >> "$STUB_LOG"
{body}
"""

_BODIES = {
    # `image inspect` succeeds only for images listed in $STUB_PRESENT_IMAGES.
    "docker": """
case "$1" in
  image) for i in $STUB_PRESENT_IMAGES; do [[ "$i" == "${@: -1}" ]] && exit 0; done; exit 1 ;;
  inspect) echo true ;;
esac
exit 0
""",
    "kind": """[[ "$1" == get ]] && echo "$STUB_CLUSTER"; exit 0""",
    # `get deploy/ticketscope-api` prints $STUB_DEPLOYED_IMAGE, or fails when it is empty.
    "kubectl": """
if [[ "$*" == *"get deploy/ticketscope-api"* ]]; then
  [[ -n "${STUB_DEPLOYED_IMAGE:-}" ]] || { echo "NotFound" >&2; exit 1; }
  printf '%s' "$STUB_DEPLOYED_IMAGE"; exit 0
fi
[[ "$*" == *"get gateway/"* ]] && printf '10.0.0.1'
exit 0
""",
    "helm": "exit 0",
    "git": "echo unused-sha",
    # Linux path: no port-forward, no /tmp writes.
    "uname": "echo Linux",
}


@pytest.fixture
def kind_up(tmp_path: Path):
    """Run kind-up.sh on stubs; return (returncode, output, calls)."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, body in _BODIES.items():
        stub = bin_dir / name
        stub.write_text(_STUB.format(name=name, body=body), "utf-8")
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    log = tmp_path / "calls.log"

    def run(
        *,
        present: tuple[str, ...] = (),
        deployed: str = "",
        force_build: bool = False,
        cluster: str = "ticketscope",
    ) -> tuple[int, str, list[str]]:
        log.write_text("", "utf-8")
        env = {
            "PATH": f"{bin_dir}{os.pathsep}/usr/bin:/bin",
            "HOME": str(tmp_path),
            "TAG": TAG,
            "STUB_LOG": str(log),
            "STUB_PRESENT_IMAGES": " ".join(present),
            "STUB_DEPLOYED_IMAGE": deployed,
            "STUB_CLUSTER": cluster,
        }
        if force_build:
            env["FORCE_BUILD"] = "1"
        proc = subprocess.run(
            ["bash", str(KIND_UP)],
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        calls = log.read_text("utf-8").splitlines()
        return proc.returncode, proc.stdout + proc.stderr, calls

    return run


def _index(calls: list[str], needle: str) -> int:
    matches = [i for i, c in enumerate(calls) if needle in c]
    assert matches, f"no call contains {needle!r}:\n" + "\n".join(calls)
    return matches[0]


def _restarted(calls: list[str]) -> bool:
    return any("rollout restart deploy/ticketscope-api" in c for c in calls)


def test_same_tag_rebuild_restarts_api_before_waiting_for_it(kind_up) -> None:
    """DW-2: FORCE_BUILD under the deployed tag leaves the pod template unchanged, so
    the script must roll api itself, after the Helm upgrade and before rollout status."""
    code, out, calls = kind_up(present=(APP_IMAGE, PG_IMAGE), deployed=APP_IMAGE, force_build=True)
    assert code == 0, out
    assert "restarting api" in out
    read = _index(calls, "get deploy/ticketscope-api")
    upgrade = _index(calls, "upgrade --install ticketscope")
    restart = _index(calls, "rollout restart deploy/ticketscope-api")
    status = _index(calls, "rollout status deploy/ticketscope-api")
    assert read < upgrade < restart < status


def test_new_tag_rebuild_does_not_restart_api(kind_up) -> None:
    """Helm's own rollout covers a tag change; a restart would roll api twice."""
    code, out, calls = kind_up(deployed="ticketscope-app:older", force_build=True)
    assert code == 0, out
    assert not _restarted(calls)
    assert any("rollout status deploy/ticketscope-api" in c for c in calls)


def test_fresh_install_without_an_api_deployment_does_not_restart(kind_up) -> None:
    code, out, calls = kind_up(deployed="", cluster="")
    assert code == 0, out
    assert any("create cluster" in c for c in calls)
    assert not _restarted(calls)


def test_same_tag_without_rebuild_does_not_restart(kind_up) -> None:
    code, out, calls = kind_up(present=(APP_IMAGE, PG_IMAGE), deployed=APP_IMAGE)
    assert code == 0, out
    assert not any(c.startswith("docker build") for c in calls)
    assert not _restarted(calls)


def test_only_a_postgres_rebuild_does_not_restart_api(kind_up) -> None:
    """`build` resets BUILT per image; the app's result must be captured before the
    Postgres build overwrites it."""
    code, out, calls = kind_up(present=(APP_IMAGE,), deployed=APP_IMAGE)
    assert code == 0, out
    builds = [c for c in calls if c.startswith("docker build")]
    assert builds == [f"docker build -f images/postgres.Dockerfile -t {PG_IMAGE} ."]
    assert not _restarted(calls)


def test_app_rebuild_under_deployed_tag_restarts_even_when_postgres_is_present(
    kind_up,
) -> None:
    code, out, calls = kind_up(present=(PG_IMAGE,), deployed=APP_IMAGE)
    assert code == 0, out
    assert _restarted(calls)


def test_platform_dependencies_build_from_the_lock_only(kind_up) -> None:
    code, out, calls = kind_up(present=(APP_IMAGE, PG_IMAGE), deployed=APP_IMAGE)
    assert code == 0, out
    helm_dep = [c for c in calls if c.startswith("helm dependency")]
    assert helm_dep == ["helm dependency build deploy/charts/platform"]
    assert _index(calls, "helm dependency build") < _index(calls, "upgrade --install platform")
