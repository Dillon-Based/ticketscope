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


def test_ci_integrated_check_call_is_unchanged() -> None:
    text = CI.read_text(encoding="utf-8")
    expected = (
        "  integrated-check:\n"
        "    # One kind cluster per PR. The integrated suite runs first, on the freshly deployed\n"
        "    # state, before smoke's upgrades and forced reloads.\n"
        "    uses: ./.github/workflows/_kind-deploy.yml\n"
        "    with:\n"
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
