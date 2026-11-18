"""The smoke check for a live EKS environment, over its public hostname (story 5.3, marker `eks`).

Needs `TICKETSCOPE_PUBLIC_URL` (`https://<fixed hostname>`, printed by `scripts/eks-deploy.sh`)
and, for the issue count, `kubectl` on a kubeconfig that reads the `ticketscope` namespace
(`KUBECONFIG`) plus network access to the GitHub API. Run with `uv run pytest -m eks tests/eks`.
`env-up` runs it after `eks-deploy.sh` has already waited for the page, so nothing here waits.
"""

import asyncio
import os
import re
import subprocess
from urllib.parse import urlencode

import httpx2
import pytest
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from tests.factories import form_payload
from tests.target import snapshot_pin

pytestmark = pytest.mark.eks

NAMESPACE = os.environ.get("TICKETSCOPE_NAMESPACE", "ticketscope")
QUERY = "launcher crash"
TOOL = "search_similar_issues"
ISSUES_IN_REPORT = re.compile(r"load report: .*?\bissues=(\d+)")
ISSUES_IN_RELEASE = re.compile(r"Issues:\s*(\d+)")


def _public_url() -> str:
    url = os.environ.get("TICKETSCOPE_PUBLIC_URL", "").rstrip("/")
    if not url.startswith("https://"):
        pytest.fail("TICKETSCOPE_PUBLIC_URL must be set to https://<hostname>")
    return url


@pytest.mark.criterion("ticketscope--e5-s3--AC-1")
def test_the_page_answers_a_search_over_https() -> None:
    response = httpx2.post(
        f"{_public_url()}/",
        content=urlencode(form_payload(QUERY)),
        headers={"content-type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    assert response.status_code == 200, response.text[:500]
    assert response.headers["content-type"].startswith("text/html")
    assert '<li class="result"' in response.text, "the page returned no result rows"


@pytest.mark.criterion("ticketscope--e5-s3--AC-1")
def test_mcp_lists_the_tool_and_answers_a_search_over_https() -> None:
    async def run() -> tuple[list[str], dict[str, object]]:
        async with Client(streamable_http_client(f"{_public_url()}/mcp")) as client:
            names = [tool.name for tool in (await client.list_tools()).tools]
            result = await client.call_tool(TOOL, {"query": QUERY})
        assert not result.is_error, result
        assert result.structured_content is not None
        return names, result.structured_content

    names, body = asyncio.run(run())
    assert TOOL in names
    results = body["results"]
    assert isinstance(results, list) and results, "the MCP search returned no results"


def _load_report_count() -> int:
    """`issues=N` from the load Job's `load report:` line, read through the kubeconfig."""
    pods = subprocess.run(
        [
            "kubectl",
            "-n",
            NAMESPACE,
            "get",
            "pod",
            "-l",
            "job-name=ticketscope-load",
            "--field-selector",
            "status.phase=Succeeded",
            "--sort-by",
            ".metadata.creationTimestamp",
            "-o",
            "jsonpath={.items[*].metadata.name}",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    assert pods, "no Succeeded ticketscope-load pod"
    log = subprocess.run(
        ["kubectl", "-n", NAMESPACE, "logs", pods[-1]],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    counts = [m.group(1) for line in log.splitlines() if (m := ISSUES_IN_REPORT.search(line))]
    assert counts, "no load report line with an issue count"
    return int(counts[-1])


def _release_count() -> int:
    """`Issues: N` from the body of the pinned snapshot's Release."""
    pin = snapshot_pin()
    match = re.search(r"github\.com/([^/]+/[^/]+)/releases/download", pin["baseUrl"])
    assert match, pin["baseUrl"]
    headers = {"Accept": "application/vnd.github+json"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    response = httpx2.get(
        f"https://api.github.com/repos/{match.group(1)}/releases/tags/snapshot-{pin['version']}",
        headers=headers,
        timeout=30,
    )
    assert response.status_code == 200, response.text[:500]
    found = ISSUES_IN_RELEASE.search(str(response.json().get("body", "")))
    assert found, "the Release body has no `Issues:` line"
    return int(found.group(1))


@pytest.mark.criterion("ticketscope--e5-s3--AC-1")
def test_the_loaded_issue_count_equals_the_pinned_releases_count() -> None:
    loaded, published = _load_report_count(), _release_count()
    assert loaded == published, f"loaded {loaded} issues, the Release publishes {published}"
