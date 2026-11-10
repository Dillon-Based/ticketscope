"""Rendered-chart coverage for story 3.6 (R5): the default mode and the api resources."""

import re
import shutil
import subprocess

import pytest

from tests.target import REPO

CHART = REPO / "deploy" / "charts" / "ticketscope"
needs_helm = pytest.mark.skipif(shutil.which("helm") is None, reason="needs helm")
_ARGS = [
    "--set-string",
    "image.app.tag=t",
    "--set-string",
    "image.postgres.tag=18-t",
    "--set",
    "backup.enabled=false",
]


def _render(*args: str) -> str:
    result = subprocess.run(
        ["helm", "template", "t", str(CHART), *_ARGS, *args],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _api(rendered: str) -> str:
    [doc] = [
        d
        for d in rendered.split("\n---\n")
        if "kind: Deployment\n" in d and "name: ticketscope-api\n" in d
    ]
    return doc


def _to_millicores(value: str) -> int:
    return int(value[:-1]) if value.endswith("m") else int(float(value) * 1000)


def _to_mib(value: str) -> int:
    assert value.endswith("Mi"), value
    return int(value[:-2])


@needs_helm
def test_api_receives_the_default_mode_from_values() -> None:
    api = _api(_render())
    assert re.search(r"name: TICKETSCOPE_DEFAULT_MODE\n\s+value: \"hybrid\"", api), (
        "api must carry the chosen default mode"
    )


@needs_helm
def test_default_mode_override_reaches_the_api() -> None:
    api = _api(_render("--set", "retrieval.defaultMode=dense"))
    assert re.search(r"name: TICKETSCOPE_DEFAULT_MODE\n\s+value: \"dense\"", api)


@needs_helm
def test_only_the_api_receives_a_default_mode() -> None:
    """mcp keeps no mode default (AD-25): no other workload sets one."""
    rendered = _render()
    assert rendered.count("TICKETSCOPE_DEFAULT_MODE") == 1


@needs_helm
def test_api_rendered_resources_have_requests_within_limits() -> None:
    api = _api(_render())
    res = re.search(
        r"resources:\n\s+limits:\n\s+cpu: \"?(\S+?)\"?\n\s+memory: (\S+)\n\s+requests:\n"
        r"\s+cpu: \"?(\S+?)\"?\n\s+memory: (\S+)",
        api,
    )
    assert res, "api container resources not rendered with cpu and memory on both sides"
    limit_cpu, limit_mem, req_cpu, req_mem = res.groups()
    assert _to_millicores(req_cpu) <= _to_millicores(limit_cpu)
    assert _to_mib(req_mem) <= _to_mib(limit_mem)


@needs_helm
def test_api_memory_limit_clears_the_measured_peak() -> None:
    """The recorded 288 MB peak must fit under the rendered limit with headroom."""
    api = _api(_render())
    limit = re.search(r"limits:\n(?:\s+cpu: .*\n)?\s+memory: (\d+Mi)", api)
    assert limit
    assert _to_mib(limit.group(1)) * 1024 * 1024 > 288 * 1_000_000 * 1.5
