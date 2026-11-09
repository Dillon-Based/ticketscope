"""Workflow wiring for eval (story 2.1, risk R-008), on the workflow text: eval.yml runs on
PRs through `_kind-deploy.yml`, the new reusable-workflow input has a default so ci.yml's
call is unchanged, the reports upload stays always-run, and kind-up leaves eval off."""

import re

from tests.target import REPO

WORKFLOWS = REPO / ".github" / "workflows"
EVAL = WORKFLOWS / "eval.yml"
KIND_DEPLOY = WORKFLOWS / "_kind-deploy.yml"
CI = WORKFLOWS / "ci.yml"
KIND_UP = REPO / "scripts" / "kind-up.sh"


def _block(text: str, key: str, indent: int) -> str:
    """The lines under `<indent spaces><key>:` up to the next key at that indent or less."""
    lines = text.splitlines()
    start = lines.index(" " * indent + f"{key}:")
    body: list[str] = []
    for line in lines[start + 1 :]:
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        body.append(line)
    return "\n".join(body)


def test_eval_workflow_runs_on_pull_request_and_calls_kind_deploy_with_eval_enabled() -> None:
    text = EVAL.read_text(encoding="utf-8")
    assert re.search(r"^on:\n  pull_request:\n", text, re.MULTILINE)
    assert "uses: ./.github/workflows/_kind-deploy.yml" in text
    assert "eval_enabled: true" in text
    assert "check: uv run pytest -m kind tests/eval --junitxml=reports/eval.xml" in text


def test_kind_deploy_eval_input_is_an_optional_boolean_defaulting_to_false() -> None:
    inputs = _block(KIND_DEPLOY.read_text(encoding="utf-8"), "inputs", 4)
    block = _block(inputs, "eval_enabled", 6)
    assert "type: boolean" in block
    assert "required: false" in block
    assert "default: false" in block


def test_every_kind_deploy_input_but_check_has_a_default() -> None:
    inputs = _block(KIND_DEPLOY.read_text(encoding="utf-8"), "inputs", 4)
    names = re.findall(r"^      (\w+):$", inputs, re.MULTILINE)
    assert "check" in names and "eval_enabled" in names
    for name in names:
        if name != "check":
            assert "default:" in _block(inputs, name, 6), name


def test_kind_deploy_passes_eval_enabled_to_kind_up() -> None:
    text = KIND_DEPLOY.read_text(encoding="utf-8")
    assert "EVAL_ENABLED: ${{ inputs.eval_enabled && '1' || '0' }}" in text


def test_reports_upload_runs_always_after_the_check() -> None:
    text = KIND_DEPLOY.read_text(encoding="utf-8")
    check = text.index("      - name: Check\n")
    upload = text.index("      - name: Upload test reports\n")
    assert check < upload
    upload_step = text[upload:]
    assert "if: always()" in upload_step
    assert "path: reports/" in upload_step


def test_kind_jobs_skip_inside_the_reusable_workflow_when_no_kind_path_changed() -> None:
    # The skip sits in `deploy`, not on the caller, so a skipped run still reports the
    # `<caller> / deploy` check name that branch protection may require.
    assert "    if: inputs.enabled\n" in KIND_DEPLOY.read_text(encoding="utf-8")
    eval_text = EVAL.read_text(encoding="utf-8")
    assert "needs: changes" in eval_text
    assert "enabled: ${{ needs.changes.outputs.kind == 'true' }}" in eval_text
    for workflow in (EVAL, CI):
        assert "filters: .github/kind-paths.yml" in workflow.read_text(encoding="utf-8")


def test_kind_paths_cover_what_a_kind_deploy_depends_on() -> None:
    paths = (REPO / ".github" / "kind-paths.yml").read_text(encoding="utf-8")
    for needed in ("src/**", "migrations/**", "deploy/**", "images/**", "eval/**", "uv.lock"):
        assert f"'{needed}'" in paths, needed
    for needed in (
        "tests/eval/**",
        "tests/integrated/**",
        "tests/smoke/**",
        ".github/workflows/**",
    ):
        assert f"'{needed}'" in paths, needed
    assert "_bmad-output" not in paths and ".bmad-loop" not in paths


def test_ci_integrated_check_call_only_gains_the_path_filter() -> None:
    text = CI.read_text(encoding="utf-8")
    expected = (
        "  integrated-check:\n"
        "    # One kind cluster per PR. The integrated suite runs first, on the freshly deployed\n"
        "    # state, before smoke's upgrades and forced reloads.\n"
        "    needs: changes\n"
        "    uses: ./.github/workflows/_kind-deploy.yml\n"
        "    with:\n"
        "      # Skipped inside the reusable workflow, so the check still reports as\n"
        "      # `integrated-check / deploy`. A manual dispatch always runs it.\n"
        "      enabled: ${{ needs.changes.outputs.kind == 'true' ||"
        " github.event_name == 'workflow_dispatch' }}\n"
        "      check: uv run pytest -m kind tests/integrated tests/smoke"
        " --junitxml=reports/kind.xml\n"
        "      # Story 10 AC-4: the first smoke run after an in-place upgrade passes (3).\n"
        "      upgrade_check: uv run pytest -m kind tests/smoke"
        " --junitxml=reports/kind-upgrade.xml\n"
        "\n"
    )
    assert expected in text
    assert "eval_enabled" not in text


def test_ci_chart_render_job_runs_the_eval_chart_tests() -> None:
    assert "tests/unit/test_chart_eval.py" in CI.read_text(encoding="utf-8")


def test_base_commit_is_fetched_and_the_gate_runs_after_the_eval_check() -> None:
    eval_text = EVAL.read_text(encoding="utf-8")
    assert "base_sha: ${{ github.event.pull_request.base.sha }}" in eval_text
    pytest_at = eval_text.index("uv run pytest -m kind tests/eval")
    gate_at = eval_text.index("python -m ticketscope.jobs.eval.gate")
    assert pytest_at < gate_at
    assert '--base-sha "$BASE_SHA"' in eval_text
    assert "--results reports/eval-results.json" in eval_text

    text = KIND_DEPLOY.read_text(encoding="utf-8")
    block = _block(_block(text, "inputs", 4), "base_sha", 6)
    assert "type: string" in block and 'default: ""' in block
    fetch = text.index("      - name: Fetch the PR base commit\n")
    check = text.index("      - name: Check\n")
    assert fetch < check
    assert 'git fetch --no-tags --depth=1 origin "$BASE_SHA"' in text[fetch:check]
    assert "BASE_SHA: ${{ inputs.base_sha }}" in text[check:]


def test_kind_up_leaves_eval_off_unless_asked() -> None:
    text = KIND_UP.read_text(encoding="utf-8")
    assert 'if [[ "${EVAL_ENABLED:-0}" == 1 ]]; then' in text
    # The only place eval is switched on is inside that branch.
    assert text.count("eval.enabled=true") == 1
    branch = text[text.index('if [[ "${EVAL_ENABLED:-0}" == 1 ]]; then') :]
    branch = branch[: branch.index("\nfi\n")]
    assert "EVAL_ARGS=(--set eval.enabled=true)" in branch
    assert "HELM_TIMEOUT=40m" in branch
    assert "HELM_TIMEOUT=25m" in text
