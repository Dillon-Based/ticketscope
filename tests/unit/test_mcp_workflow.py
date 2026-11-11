"""Workflow and script wiring for the MCP server (story 4.1), on the file text."""

import re

from tests.target import REPO

WORKFLOWS = REPO / ".github" / "workflows"
MCP_E2E = WORKFLOWS / "mcp-e2e.yml"
CI = WORKFLOWS / "ci.yml"
KIND_UP = REPO / "scripts" / "kind-up.sh"
KIND_PATHS = REPO / ".github" / "kind-paths.yml"


def test_mcp_e2e_runs_on_pull_request_through_kind_deploy_behind_the_kind_filter() -> None:
    text = MCP_E2E.read_text(encoding="utf-8")
    assert re.search(r"^on:\n  pull_request:\n", text, re.MULTILINE)
    assert "uses: ./.github/workflows/_kind-deploy.yml" in text
    assert "needs: changes" in text
    assert "filters: .github/kind-paths.yml" in text
    assert "enabled: ${{ needs.changes.outputs.kind == 'true' }}" in text
    assert "check: uv run pytest -m kind tests/mcp --junitxml=reports/mcp.xml" in text
    assert "eval_enabled" not in text


def test_kind_paths_kind_list_includes_the_mcp_tests() -> None:
    text = KIND_PATHS.read_text(encoding="utf-8")
    kind = text.split("\ncontainers:")[0]
    assert "  - 'tests/mcp/**'\n" in kind


def test_ci_charts_job_lists_the_mcp_chart_tests() -> None:
    assert "tests/unit/test_chart_mcp.py" in CI.read_text(encoding="utf-8")


def test_kind_up_restarts_and_waits_for_mcp() -> None:
    text = KIND_UP.read_text(encoding="utf-8")
    assert "get deploy/ticketscope-mcp" in text
    assert 'DEPLOYED_MCP_IMAGE" == "$APP_IMAGE"' in text
    assert "rollout restart deploy/ticketscope-mcp" in text
    assert "rollout status deploy/ticketscope-mcp" in text
    # The wait comes before the script returns to its caller: before the Gateway address step.
    assert text.index("rollout status deploy/ticketscope-mcp") < text.index("# 7. Gateway address")
