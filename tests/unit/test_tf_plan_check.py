"""The no-credential plan check of infra/env and the kind path filter (story 5.5, AD-25 and R7),
checked as text: the PR gate runs the plan itself (scripts/tf-plan-check.sh), so these tests
need neither terraform nor AWS."""

import re

import pytest
import yaml

from tests.target import REPO

CI = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
CHECK = (REPO / "scripts" / "check.sh").read_text(encoding="utf-8")
SCRIPT = REPO / "scripts" / "tf-plan-check.sh"
PLAN_TEST = REPO / "infra" / "env" / "tests" / "plan.tftest.hcl"
KIND_PATHS = yaml.safe_load((REPO / ".github" / "kind-paths.yml").read_text(encoding="utf-8"))


def _job(name: str) -> str:
    """The text of one job in ci.yml, from its header to the next job header (two spaces)."""
    rest = CI.split(f"\n  {name}:\n", 1)[1]
    return re.split(r"\n  [A-Za-z][\w-]*:\n", rest, maxsplit=1)[0]


@pytest.mark.criterion("ticketscope--e5-s5--AC-3")
def test_the_plan_check_is_a_script_that_the_terraform_job_runs_without_aws() -> None:
    assert SCRIPT.exists()
    assert SCRIPT.stat().st_mode & 0o111, "the script must be executable"
    terraform = _job("terraform")
    assert "run: scripts/tf-plan-check.sh" in terraform
    # The job never configures AWS credentials: the plan is mocked, not signed in.
    assert "configure-aws-credentials" not in terraform
    assert "AWS_" not in terraform


@pytest.mark.criterion("ticketscope--e5-s5--AC-3")
def test_the_plan_test_mocks_the_aws_provider_and_plans_the_root_module() -> None:
    text = PLAN_TEST.read_text(encoding="utf-8")
    assert 'mock_provider "aws"' in text
    assert "command = plan" in text
    # main.tf slices two availability zones, so the mock must supply two.
    assert re.search(r'names\s*=\s*\["[^"]+",\s*"[^"]+"\]', text)


@pytest.mark.criterion("ticketscope--e5-s5--AC-4")
def test_the_negative_case_is_planted_and_must_fail_for_that_reason() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "local.does_not_exist" in text
    assert "undeclared local value" in text
    assert "deliberately broken copy passed" in text


@pytest.mark.criterion("ticketscope--e5-s5--AC-4")
def test_the_script_is_in_ci_and_in_check_sh_and_is_shellchecked() -> None:
    assert "run scripts/tf-plan-check.sh" in CHECK
    assert "run shellcheck scripts/tf-plan-check.sh" in CHECK
    assert "shellcheck scripts/tf-plan-check.sh" in CI


@pytest.mark.criterion("ticketscope--e5-s5--AC-5")
def test_the_kind_filter_is_not_triggered_by_infra_and_still_covers_the_charts() -> None:
    kind = KIND_PATHS["kind"]
    assert not [p for p in kind if p.startswith("infra")]
    assert "deploy/**" in kind
    assert "scripts/**" in kind
