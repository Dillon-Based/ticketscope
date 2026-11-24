"""Story 5.10 refactor sweep: behaviour of the shared script libs and the platform labels helper.

The sweep must not change behaviour, so these run the libs in a real bash and render the chart
templates that call `platform.labels`.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from tests.unit.test_chart_backup import PLATFORM, _render

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "scripts" / "lib"
BASH = shutil.which("bash")

pytestmark = pytest.mark.criterion("ticketscope--e5-s10--AC-1")

needs_bash = pytest.mark.skipif(BASH is None, reason="needs bash")


def _bash(snippet: str) -> subprocess.CompletedProcess[str]:
    assert BASH is not None
    return subprocess.run(
        [BASH, "-c", snippet], capture_output=True, text=True, check=False, timeout=30
    )


@needs_bash
def test_x_echoes_the_command_to_stderr_then_runs_it() -> None:
    result = _bash(f'source "{LIB / "x.sh"}"; x printf "%s" "a b"')
    assert result.stdout == "a b"
    assert result.stderr == "+ printf %s a b\n"
    assert result.returncode == 0


@needs_bash
def test_x_returns_the_command_exit_status() -> None:
    result = _bash(f'source "{LIB / "x.sh"}"; x false')
    assert result.returncode == 1
    assert result.stderr == "+ false\n"


@needs_bash
def test_stages_summary_lists_each_stage_and_total_under_the_title() -> None:
    result = _bash(
        f'STAGES_TITLE=demo; source "{LIB / "stages.sh"}"; stage one; stage two; summary'
    )
    assert result.returncode == 0
    lines = result.stdout.splitlines()
    assert "--- demo stage times ---" in lines
    body = lines[lines.index("--- demo stage times ---") + 1 :]
    assert [re.match(r"(\S+)\s+\d+s$", line).group(1) for line in body] == [  # type: ignore[union-attr]
        "one",
        "two",
        "total",
    ]
    assert re.search(r"\[\d\d:\d\d:\d\d \+\s*\d+s\] stage: one", result.stdout)


@needs_bash
def test_stages_summary_with_no_stage_prints_only_the_total() -> None:
    result = _bash(f'STAGES_TITLE=empty; source "{LIB / "stages.sh"}"; summary')
    assert result.returncode == 0
    lines = result.stdout.splitlines()
    assert lines[0] == "--- empty stage times ---"
    assert len(lines) == 2 and lines[1].startswith("total")


@needs_bash
def test_stages_summary_runs_from_an_exit_trap_on_a_failed_run() -> None:
    result = _bash(
        f'STAGES_TITLE=boom; source "{LIB / "stages.sh"}"; trap summary EXIT; stage doomed; exit 3'
    )
    assert result.returncode == 3
    assert "--- boom stage times ---" in result.stdout
    assert re.search(r"^doomed\s+\d+s$", result.stdout, re.MULTILINE)


def test_each_script_sources_the_shared_lib_and_defines_no_copy() -> None:
    for name, lib, helper in [
        ("eks-deploy.sh", "stages.sh", "stage()"),
        ("eks-teardown.sh", "stages.sh", "stage()"),
        ("restore-drill.sh", "x.sh", "x()"),
        ("failure-drill.sh", "x.sh", "x()"),
    ]:
        text = (ROOT / "scripts" / name).read_text(encoding="utf-8")
        assert f'source "$ROOT/scripts/lib/{lib}"' in text, name
        assert helper not in text, f"{name} still defines {helper}"


def test_deploy_and_teardown_set_their_stage_titles() -> None:
    for name, title in [("eks-deploy.sh", "eks-deploy"), ("eks-teardown.sh", "eks-teardown")]:
        text = (ROOT / "scripts" / name).read_text(encoding="utf-8")
        assert f"STAGES_TITLE={title}\n" in text
        assert text.index("STAGES_TITLE=") < text.index('source "$ROOT/scripts/lib/stages.sh"')


def test_the_libs_are_linted_by_check_and_ci() -> None:
    for path in (ROOT / "scripts" / "check.sh", ROOT / ".github" / "workflows" / "ci.yml"):
        text = path.read_text(encoding="utf-8")
        for lib in ("scripts/lib/stages.sh", "scripts/lib/x.sh"):
            assert f"shellcheck {lib}" in text, (path.name, lib)


@pytest.mark.skipif(shutil.which("helm") is None, reason="needs helm")
def test_every_platform_object_carries_the_shared_labels(tmp_path: Path) -> None:
    root = tmp_path / "platform"
    (root / "templates").mkdir(parents=True)
    (root / "Chart.yaml").write_text("apiVersion: v2\nname: platform\nversion: 0.1.0\n")
    for name in (
        "_helpers.tpl",
        "gateway.yaml",
        "loadbalancerconfiguration.yaml",
        "targetgroupconfiguration.yaml",
        "storageclass.yaml",
        "barman-cloud-tls.yaml",
    ):
        shutil.copy(PLATFORM / "templates" / name, root / "templates" / name)
    docs = _render(
        root,
        "-f",
        str(PLATFORM / "values.yaml"),
        "-f",
        str(PLATFORM / "values-eks.yaml"),
        "--set-string",
        "gateway.aws.certificateArn=test",
    )
    objects = [yaml.safe_load(doc) for doc in docs]
    assert sorted(obj["kind"] for obj in objects) == [
        "Gateway",
        "GatewayClass",
        "LoadBalancerConfiguration",
        "Secret",
        "Secret",
        "StorageClass",
        "TargetGroupConfiguration",
        "TargetGroupConfiguration",
    ]
    for obj in objects:
        assert obj["metadata"]["labels"] == {
            "app.kubernetes.io/part-of": "ticketscope",
            "app.kubernetes.io/managed-by": "Helm",
        }


def test_no_template_inlines_the_labels_the_helper_owns() -> None:
    for path in (PLATFORM / "templates").glob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        assert "app.kubernetes.io/part-of: ticketscope" not in text, path.name
