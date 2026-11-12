"""The platform Gateway's tunnel listener (story 4.2, R-006).

Renders only `gateway.yaml` in a scratch chart, so it needs no built dependencies.
"""

import shutil
from pathlib import Path

import pytest

from tests.unit.test_chart_backup import PLATFORM, _docs, _render

pytestmark = pytest.mark.skipif(shutil.which("helm") is None, reason="needs helm")

VALUES = ["-f", str(PLATFORM / "values.yaml")]


@pytest.fixture()
def chart(tmp_path: Path) -> Path:
    root = tmp_path / "platform"
    (root / "templates").mkdir(parents=True)
    (root / "Chart.yaml").write_text("apiVersion: v2\nname: platform\nversion: 0.1.0\n")
    shutil.copy(PLATFORM / "templates" / "gateway.yaml", root / "templates" / "gateway.yaml")
    return root


def _gateway(chart: Path, *args: str) -> str:
    [gateway] = _docs(_render(chart, *VALUES, *args), "Gateway")
    return gateway


def test_unset_tunnel_hostname_renders_one_listener(chart: Path) -> None:
    gateway = _gateway(chart, "--set", "gateway.hostname=ticketscope.kind.internal")
    assert gateway.count("- name: ") == 1 and "tunnel" not in gateway


def test_tunnel_hostname_adds_a_second_listener_and_keeps_the_kind_host(chart: Path) -> None:
    gateway = _gateway(
        chart,
        "--set",
        "gateway.hostname=ticketscope.kind.internal",
        "--set",
        "gateway.tunnelHostname=tunnel.example.org",
    )
    assert gateway.count("- name: ") == 2
    assert 'hostname: "ticketscope.kind.internal"' in gateway
    assert 'hostname: "tunnel.example.org"' in gateway
