"""ci.yml's `containers` job runs the image-backed tiers on every kind-relevant PR (epic 3
retro, F2 and G1): tests/postgres and tests/image, with the require flag so a missing image
fails instead of skipping, and its report reaching the evidence job."""

import re

from tests.target import REPO

CI = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")


def _job(name: str) -> str:
    start = CI.index(f"\n  {name}:\n")
    rest = CI[start + 1 :]
    following = re.search(r"\n  [a-z][\w-]*:\n", rest[len(name) + 4 :])
    return rest[: len(name) + 4 + following.start()] if following else rest


def test_containers_builds_both_images_and_runs_both_tiers_with_the_require_flag() -> None:
    job = _job("containers")
    assert "if: needs.changes.outputs.containers == 'true'" in job
    assert "containers: ${{ steps.kind.outputs.containers }}" in _job("changes")
    assert "-f images/postgres.Dockerfile -t ticketscope-postgres:18-${{ github.sha }}" in job
    assert "-f images/app.Dockerfile -t ticketscope-app:${{ github.sha }}" in job
    assert 'TICKETSCOPE_REQUIRE_CONTAINER_TESTS: "1"' in job
    assert "TICKETSCOPE_TEST_PG_IMAGE: ticketscope-postgres:18-${{ github.sha }}" in job
    assert "TICKETSCOPE_TEST_APP_IMAGE: ticketscope-app:${{ github.sha }}" in job
    assert "run: uv run pytest tests/postgres tests/image --junitxml=reports/containers.xml" in job
    upload = job[job.index("Upload test report") :]
    assert "if: always()" in upload and "name: reports-containers" in upload


def test_containers_runs_when_its_tests_or_what_they_test_change() -> None:
    paths = (REPO / ".github" / "kind-paths.yml").read_text(encoding="utf-8")
    block = paths.split("\ncontainers:\n")[1].split("\n\n")[0]
    globs = re.findall(r"^  - '([^']+)'$", block, re.MULTILINE)
    for needed in ("tests/postgres/**", "tests/image/**", "src/**", "migrations/**", "images/**"):
        assert needed in globs, needed


def test_checks_leaves_the_image_tiers_to_containers() -> None:
    # A skipped copy in unit.xml would outrank the pass in containers.xml (live_results).
    assert "pytest --ignore=tests/postgres --ignore=tests/image --junitxml=reports/unit.xml" in (
        _job("checks")
    )


def test_evidence_waits_for_containers() -> None:
    needs = re.search(r"needs: \[([^\]]+)\]", _job("evidence"))
    assert needs and "containers" in [n.strip() for n in needs.group(1).split(",")]
