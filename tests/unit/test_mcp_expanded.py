"""Extra coverage for story 4.1: k bounds on the tool, error shapes, host checks, entrypoint."""

import asyncio
from collections.abc import Callable
from typing import Any

import httpx2
import pytest

from tests.unit.test_apiclient import recorded_problems
from tests.unit.test_mcp_server import HEADERS, _call, _result, _run
from ticketscope.apiclient import ApiClient
from ticketscope.contract.search import K_MAX, K_MIN
from ticketscope.mcp import main as mcp_main
from ticketscope.mcp.server import check_allowed_hosts
from ticketscope.settings import Settings


def _post_call(arguments: dict[str, Any]) -> Callable[[httpx2.AsyncClient], Any]:
    async def scenario(http: httpx2.AsyncClient) -> dict[str, Any]:
        return _result(await http.post("/mcp", headers=HEADERS, json=_call(arguments)))

    return scenario


@pytest.mark.parametrize("k", [K_MIN - 1, K_MAX + 1, -5])
def test_k_outside_the_contract_bounds_is_rejected_before_calling_api(k: int) -> None:
    seen: list[dict[str, Any]] = []
    result = _run(_post_call({"query": "q", "k": k}), seen)
    assert result["isError"] is True
    assert seen == []


@pytest.mark.parametrize("k", [K_MIN, K_MAX])
def test_k_at_the_bounds_reaches_api_unchanged(k: int) -> None:
    seen: list[dict[str, Any]] = []
    result = _run(_post_call({"query": "q", "k": k}), seen)
    assert not result.get("isError")
    assert seen == [{"query": "q", "k": k}]


def test_a_call_without_query_is_a_tool_error_and_never_reaches_api() -> None:
    seen: list[dict[str, Any]] = []
    result = _run(_post_call({}), seen)
    assert result["isError"] is True
    assert seen == []


def _text(result: dict[str, Any]) -> str:
    [block] = result["content"]
    return block["text"]


def test_a_non_integer_k_is_a_tool_error_and_never_reaches_api() -> None:
    seen: list[dict[str, Any]] = []
    result = _run(_post_call({"query": "q", "k": "many"}), seen)
    assert result["isError"] is True
    assert seen == []


@pytest.mark.parametrize("status", [422, 404, 500, 503])
def test_a_recorded_problem_reaches_the_client_as_its_detail(status: int) -> None:
    recorded = recorded_problems()[status]

    def api(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            recorded.status_code,
            headers={"content-type": recorded.headers["content-type"]},
            content=recorded.content,
        )

    result = _run(_post_call({"query": "q"}), [], api)
    assert result["isError"] is True
    assert _text(result) == recorded.json()["detail"]
    assert "structuredContent" not in result or not result["structuredContent"]


@pytest.mark.parametrize(
    ("failure", "text"),
    [
        (httpx2.ConnectError("x"), "ticketscope API unreachable: connection refused"),
        (httpx2.ReadTimeout("x"), "ticketscope API unreachable: timed out after 5s"),
        (httpx2.ReadError("x"), "ticketscope API unreachable: connection lost"),
    ],
)
def test_an_unreachable_api_is_a_named_tool_error(failure: Exception, text: str) -> None:
    def api(request: httpx2.Request) -> httpx2.Response:
        raise failure

    result = _run(_post_call({"query": "q"}), [], api)
    assert result["isError"] is True
    assert _text(result) == text


@pytest.mark.parametrize(
    ("response", "text"),
    [
        (
            httpx2.Response(502, text="<html>bad</html>", headers={"content-type": "text/html"}),
            "ticketscope API returned HTTP 502: the API did not return a problem detail",
        ),
        (
            httpx2.Response(500, content=b'{"detail": "tru'),
            "ticketscope API returned HTTP 500: the API did not return a problem detail",
        ),
        (
            httpx2.Response(200, json={"nope": 1}),
            "ticketscope API returned HTTP 200: response did not match the contract",
        ),
        (
            httpx2.Response(200, text="not json"),
            "ticketscope API returned HTTP 200: response did not match the contract",
        ),
    ],
)
def test_a_bad_api_answer_is_a_generic_tool_error(response: httpx2.Response, text: str) -> None:
    result = _run(_post_call({"query": "q"}), [], lambda r: response)
    assert result["isError"] is True
    assert _text(result) == text


def test_the_client_posts_to_v1_search_under_the_base_url_and_closes() -> None:
    paths: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        paths.append(request.url.path)
        body = {"mode": "keyword", "score_kind": "bm25", "corpus_version": "v1", "results": []}
        return httpx2.Response(200, json=body)

    client = ApiClient("http://api/prefix/", 5, transport=httpx2.MockTransport(handler))

    async def go() -> None:
        await client.search("q", None, None)
        await client.aclose()

    asyncio.run(go())
    assert paths == ["/prefix/v1/search"]


def test_allowed_hosts_are_trimmed_and_blanks_dropped() -> None:
    assert check_allowed_hosts([" a.test ", "", "b.test:8443"]) == ["a.test", "b.test:8443"]


@pytest.mark.parametrize("host", ["*", "*.test", "a*.test", "*:8080", "*.test:8080"])
def test_a_wildcard_in_the_host_part_is_refused(host: str) -> None:
    with pytest.raises(ValueError, match="wildcard"):
        check_allowed_hosts(["ok.test", host])


@pytest.mark.parametrize("hosts", [[], [""], ["  "]])
def test_no_usable_host_is_refused(hosts: list[str]) -> None:
    with pytest.raises(ValueError, match="at least one host"):
        check_allowed_hosts(hosts)


def test_an_empty_allowed_hosts_env_var_reads_as_no_hosts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TICKETSCOPE_MCP_ALLOWED_HOSTS", "")
    assert Settings().mcp_allowed_hosts == []


def test_main_serves_the_app_on_the_configured_host_and_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TICKETSCOPE_API_BASE_URL", "http://api")
    monkeypatch.setenv("TICKETSCOPE_MCP_ALLOWED_HOSTS", "a.test")
    monkeypatch.setenv("TICKETSCOPE_HTTP_HOST", "127.0.0.1")
    monkeypatch.setenv("TICKETSCOPE_HTTP_PORT", "9123")
    monkeypatch.setattr(mcp_main.telemetry, "configure_logging", lambda: None)
    calls: list[tuple[Any, dict[str, Any]]] = []
    monkeypatch.setattr(mcp_main.uvicorn, "run", lambda app, **kw: calls.append((app, kw)))
    mcp_main.main()
    [(app, kwargs)] = calls
    assert app is not None
    assert kwargs == {"host": "127.0.0.1", "port": 9123, "log_config": None}


def test_main_refuses_a_wildcard_host_before_serving(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TICKETSCOPE_API_BASE_URL", "http://api")
    monkeypatch.setenv("TICKETSCOPE_MCP_ALLOWED_HOSTS", "*")
    monkeypatch.setattr(mcp_main.telemetry, "configure_logging", lambda: None)
    served: list[Any] = []
    monkeypatch.setattr(mcp_main.uvicorn, "run", lambda *a, **k: served.append(a))
    with pytest.raises(ValueError, match="wildcard"):
        mcp_main.main()
    assert served == []
