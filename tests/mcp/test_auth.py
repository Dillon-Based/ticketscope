"""`mcp` as an OAuth 2.1 resource server, against a stub issuer (epic-mcp-oauth, story 2).

In process: the app on `ASGITransport`, the issuer and `/v1` on mock transports.
"""

import asyncio
import base64
import json
import time
from collections.abc import Callable, MutableMapping
from typing import Any

import httpx2
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from tests.mcp.stub_issuer import AUDIENCE, ISSUER, StubIssuer
from ticketscope.apiclient import ApiClient
from ticketscope.mcp import auth as mcp_auth
from ticketscope.mcp import main as mcp_main
from ticketscope.mcp.auth import AuthConfig
from ticketscope.mcp.server import build_app
from ticketscope.settings import Settings

HOST = "mcp.stub.test"
HEADERS = {
    "content-type": "application/json",
    "accept": "application/json, text/event-stream",
}
METADATA_URL = "https://mcp.stub.test/.well-known/oauth-protected-resource"
SEARCH_BODY: dict[str, Any] = {
    "mode": "hybrid",
    "score_kind": "rrf",
    "corpus_version": "v1",
    "results": [],
}
ISSUE_BODY: dict[str, Any] = {
    "issue": {
        "number": 6629,
        "title": "crash",
        "url": "https://bugs.mojang.com/browse/MCL-6629",
        "kind": "short",
        "state": "open",
        "key": "MCL-6629",
        "body": None,
    },
    "outcome": {"status": "unknown", "summary": None, "source": None, "ref": None},
}
CONFIG = AuthConfig(issuer=ISSUER, audience=AUDIENCE)


def _rpc(method: str, params: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}


SEARCH_CALL = _rpc("tools/call", {"name": "search_similar_issues", "arguments": {"query": "q"}})
ISSUE_CALL = _rpc("tools/call", {"name": "get_issue", "arguments": {"key": "MCL-6629"}})


def _result(response: httpx2.Response) -> dict[str, Any]:
    data = next(line for line in response.text.splitlines() if line.startswith("data: "))
    return json.loads(data.removeprefix("data: "))["result"]


def _fake_api(request: httpx2.Request) -> httpx2.Response:
    if request.url.path.startswith("/v1/issues/by-key/"):
        return httpx2.Response(200, json=ISSUE_BODY)
    return httpx2.Response(200, json=SEARCH_BODY)


def _run(
    scenario: Callable[[httpx2.AsyncClient], Any],
    issuer: StubIssuer,
    auth: AuthConfig | None = CONFIG,
) -> Any:
    client = ApiClient("http://api", 5, transport=httpx2.MockTransport(_fake_api))
    settings = Settings(mcp_allowed_hosts=HOST, api_base_url="http://api")  # pyright: ignore[reportArgumentType]
    app = build_app(settings, client, auth, key_client=issuer.client())

    async def main() -> Any:
        async with app.router.lifespan_context(app):
            transport = httpx2.ASGITransport(app=app)
            async with httpx2.AsyncClient(transport=transport, base_url=f"http://{HOST}") as http:
                return await scenario(http)

    return asyncio.run(main())


def _bearer(token: str) -> dict[str, str]:
    return {**HEADERS, "authorization": f"Bearer {token}"}


@pytest.mark.criterion("ticketscope--e6-s2--AC-1")
def test_a_call_without_a_token_is_401_naming_the_metadata_url() -> None:
    async def scenario(http: httpx2.AsyncClient) -> httpx2.Response:
        return await http.post("/mcp", headers=HEADERS, json=SEARCH_CALL)

    response = _run(scenario, StubIssuer())
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == f'Bearer resource_metadata="{METADATA_URL}"'
    assert "error=" not in response.headers["www-authenticate"]


@pytest.mark.criterion("ticketscope--e6-s2--AC-1")
@pytest.mark.parametrize("header", ["Bearer abc", "Basic x", "Bearer", "Bearer a b", "abc"])
def test_a_malformed_or_non_bearer_header_is_401_invalid_token(header: str) -> None:
    async def scenario(http: httpx2.AsyncClient) -> httpx2.Response:
        return await http.post(
            "/mcp", headers={**HEADERS, "authorization": header}, json=SEARCH_CALL
        )

    response = _run(scenario, StubIssuer())
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == (
        f'Bearer resource_metadata="{METADATA_URL}", error="invalid_token"'
    )


def _unsigned(kid: str) -> str:
    def part(value: dict[str, Any]) -> str:
        return base64.urlsafe_b64encode(json.dumps(value).encode()).rstrip(b"=").decode()

    header = part({"alg": "none", "typ": "JWT", "kid": kid})
    return f"{header}.{part({'iss': ISSUER, 'aud': AUDIENCE, 'exp': 4102444800})}."


def _bad_tokens(issuer: StubIssuer) -> dict[str, str]:
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return {
        "expired": issuer.mint(exp=1),
        "wrong_iss": issuer.mint(iss="https://evil.test"),
        "wrong_aud": issuer.mint(aud="https://mcp.stub.test/other"),
        "wrong_aud_list": issuer.mint(aud=["https://x.test", "https://y.test"]),
        "no_exp": issuer.mint(exp=None),
        "no_iss": issuer.mint(iss=None),
        "no_aud": issuer.mint(aud=None),
        "wrong_key": issuer.mint(key=other_key),
        "alg_none": _unsigned(issuer.current_kid),
        "hs256": jwt.encode(
            {"iss": ISSUER, "aud": AUDIENCE, "exp": 4102444800},
            "x" * 64,
            "HS256",
            {"kid": issuer.current_kid},
        ),
        "no_kid": jwt.encode(
            {"iss": ISSUER, "aud": AUDIENCE, "exp": 4102444800},
            issuer.private_key(),
            "RS256",
        ),
    }


@pytest.mark.criterion("ticketscope--e6-s2--AC-1")
def test_every_kind_of_bad_token_is_401_without_a_reason() -> None:
    issuer = StubIssuer()

    async def scenario(http: httpx2.AsyncClient) -> dict[str, httpx2.Response]:
        return {
            name: await http.post("/mcp", headers=_bearer(token), json=SEARCH_CALL)
            for name, token in _bad_tokens(issuer).items()
        }

    for name, response in _run(scenario, issuer).items():
        assert response.status_code == 401, name
        assert response.headers["www-authenticate"].endswith('error="invalid_token"'), name
        assert response.content == b"", name


@pytest.mark.criterion("ticketscope--e6-s2--AC-1")
def test_the_refusal_is_logged_as_a_reason_code_never_the_token(
    caplog: pytest.LogCaptureFixture,
) -> None:
    issuer = StubIssuer()
    token = issuer.mint(exp=1)

    async def scenario(http: httpx2.AsyncClient) -> None:
        await http.post("/mcp", headers=_bearer(token), json=SEARCH_CALL)

    with caplog.at_level("INFO", logger="ticketscope.mcp.auth"):
        _run(scenario, issuer)
    assert "reason=expired" in caplog.text
    assert token not in caplog.text


@pytest.mark.criterion("ticketscope--e6-s2--AC-2")
def test_a_valid_token_gets_the_same_bodies_as_auth_off() -> None:
    issuer = StubIssuer()

    async def with_token(http: httpx2.AsyncClient) -> list[dict[str, Any]]:
        headers = _bearer(issuer.mint())
        return [
            _result(await http.post("/mcp", headers=headers, json=call))
            for call in (SEARCH_CALL, ISSUE_CALL)
        ]

    async def without(http: httpx2.AsyncClient) -> list[dict[str, Any]]:
        return [
            _result(await http.post("/mcp", headers=HEADERS, json=call))
            for call in (SEARCH_CALL, ISSUE_CALL)
        ]

    on = _run(with_token, issuer)
    off = _run(without, issuer, auth=None)
    assert on == off
    assert on[0]["structuredContent"] == SEARCH_BODY
    assert on[1]["structuredContent"]["issue"]["key"] == "MCL-6629"


@pytest.mark.criterion("ticketscope--e6-s2--AC-2")
def test_an_audience_list_containing_the_resource_is_accepted() -> None:
    issuer = StubIssuer()

    async def scenario(http: httpx2.AsyncClient) -> httpx2.Response:
        token = issuer.mint(aud=["https://other.test", AUDIENCE])
        return await http.post("/mcp", headers=_bearer(token), json=SEARCH_CALL)

    assert _run(scenario, issuer).status_code == 200


@pytest.mark.criterion("ticketscope--e6-s2--AC-3")
def test_the_metadata_is_served_without_a_token() -> None:
    async def scenario(http: httpx2.AsyncClient) -> httpx2.Response:
        return await http.get("/.well-known/oauth-protected-resource")

    response = _run(scenario, StubIssuer())
    assert response.status_code == 200
    assert response.json() == {
        "resource": AUDIENCE,
        "authorization_servers": [ISSUER],
        "bearer_methods_supported": ["header"],
    }


@pytest.mark.criterion("ticketscope--e6-s2--AC-3")
@pytest.mark.parametrize("path", ["/", "/v1/search", "/nope", "/.well-known/other", "/mcp"])
def test_every_other_tokenless_path_is_401(path: str) -> None:
    async def scenario(http: httpx2.AsyncClient) -> httpx2.Response:
        return await http.get(path)

    assert _run(scenario, StubIssuer()).status_code == 401


@pytest.mark.criterion("ticketscope--e6-s2--AC-3")
def test_healthz_stays_open() -> None:
    async def scenario(http: httpx2.AsyncClient) -> httpx2.Response:
        return await http.get("/healthz")

    response = _run(scenario, StubIssuer())
    assert (response.status_code, response.text) == (200, "ok")


@pytest.mark.criterion("ticketscope--e6-s2--AC-4")
def test_auth_off_serves_no_metadata_and_asks_for_no_token() -> None:
    async def scenario(http: httpx2.AsyncClient) -> tuple[int, int]:
        metadata = await http.get("/.well-known/oauth-protected-resource")
        call = await http.post("/mcp", headers=HEADERS, json=SEARCH_CALL)
        return metadata.status_code, call.status_code

    issuer = StubIssuer()
    assert _run(scenario, issuer, auth=None) == (404, 200)
    assert issuer.requests == []


def test_a_key_issued_after_the_cache_fill_is_found_by_one_refetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    issuer = StubIssuer()
    clock = [0.0]
    monkeypatch.setattr(mcp_auth, "_now", lambda: clock[0])

    async def scenario(http: httpx2.AsyncClient) -> list[int]:
        first = await http.post("/mcp", headers=_bearer(issuer.mint()), json=SEARCH_CALL)
        issuer.rotate()
        clock[0] += mcp_auth.MIN_REFETCH_SECONDS + 1
        second = await http.post("/mcp", headers=_bearer(issuer.mint()), json=SEARCH_CALL)
        return [first.status_code, second.status_code]

    assert _run(scenario, issuer) == [200, 200]
    assert issuer.jwks_fetches == 2


def test_a_new_key_inside_the_refetch_interval_is_refused_not_refetched() -> None:
    issuer = StubIssuer()

    async def scenario(http: httpx2.AsyncClient) -> list[int]:
        first = await http.post("/mcp", headers=_bearer(issuer.mint()), json=SEARCH_CALL)
        issuer.rotate()
        second = await http.post("/mcp", headers=_bearer(issuer.mint()), json=SEARCH_CALL)
        return [first.status_code, second.status_code]

    assert _run(scenario, issuer) == [200, 401]
    assert issuer.jwks_fetches == 1


def test_unknown_kids_refetch_at_most_once_per_interval() -> None:
    issuer = StubIssuer()
    stranger = StubIssuer()

    async def scenario(http: httpx2.AsyncClient) -> list[int]:
        codes = [
            (
                await http.post("/mcp", headers=_bearer(stranger.mint()), json=SEARCH_CALL)
            ).status_code
            for _ in range(5)
        ]
        return codes

    assert _run(scenario, issuer) == [401] * 5
    assert issuer.jwks_fetches == 1


def test_keys_are_cached_across_requests() -> None:
    issuer = StubIssuer()

    async def scenario(http: httpx2.AsyncClient) -> None:
        for _ in range(4):
            await http.post("/mcp", headers=_bearer(issuer.mint()), json=SEARCH_CALL)

    _run(scenario, issuer)
    assert issuer.jwks_fetches == 1


def test_keys_expire_after_their_lifetime(monkeypatch: pytest.MonkeyPatch) -> None:
    issuer = StubIssuer()
    clock = [0.0]
    monkeypatch.setattr(mcp_auth, "_now", lambda: clock[0])

    async def scenario(http: httpx2.AsyncClient) -> None:
        await http.post("/mcp", headers=_bearer(issuer.mint()), json=SEARCH_CALL)
        clock[0] += mcp_auth.KEY_LIFETIME_SECONDS + 1
        await http.post("/mcp", headers=_bearer(issuer.mint()), json=SEARCH_CALL)

    _run(scenario, issuer)
    assert issuer.jwks_fetches == 2


def test_an_unreachable_issuer_with_no_cached_keys_is_503_without_a_challenge() -> None:
    issuer = StubIssuer()
    issuer.down = True

    async def scenario(http: httpx2.AsyncClient) -> httpx2.Response:
        return await http.post("/mcp", headers=_bearer(issuer.mint()), json=SEARCH_CALL)

    response = _run(scenario, issuer)
    assert response.status_code == 503
    assert "www-authenticate" not in response.headers


def test_cached_keys_still_serve_when_the_issuer_goes_down(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    issuer = StubIssuer()
    clock = [0.0]
    monkeypatch.setattr(mcp_auth, "_now", lambda: clock[0])
    token = issuer.mint()

    async def scenario(http: httpx2.AsyncClient) -> list[int]:
        first = await http.post("/mcp", headers=_bearer(token), json=SEARCH_CALL)
        issuer.down = True
        clock[0] += mcp_auth.KEY_LIFETIME_SECONDS + 1
        before = len(issuer.requests)
        second = await http.post("/mcp", headers=_bearer(token), json=SEARCH_CALL)
        assert len(issuer.requests) > before  # the refetch was tried, and failed
        return [first.status_code, second.status_code]

    assert _run(scenario, issuer) == [200, 200]


def test_two_authorization_headers_are_401_invalid_token() -> None:
    issuer = StubIssuer()

    async def scenario(http: httpx2.AsyncClient) -> httpx2.Response:
        headers = [(k, v) for k, v in HEADERS.items()]
        headers += [("authorization", f"Bearer {issuer.mint()}")] * 2
        return await http.post("/mcp", headers=headers, json=SEARCH_CALL)

    response = _run(scenario, issuer)
    assert response.status_code == 401
    assert response.headers["www-authenticate"].endswith('error="invalid_token"')


def test_a_lowercase_bearer_scheme_is_accepted() -> None:
    issuer = StubIssuer()

    async def scenario(http: httpx2.AsyncClient) -> httpx2.Response:
        headers = {**HEADERS, "authorization": f"bearer {issuer.mint()}"}
        return await http.post("/mcp", headers=headers, json=SEARCH_CALL)

    assert _run(scenario, issuer).status_code == 200


def test_the_no_token_refusal_is_logged_as_no_token(caplog: pytest.LogCaptureFixture) -> None:
    async def scenario(http: httpx2.AsyncClient) -> None:
        await http.post("/mcp", headers=HEADERS, json=SEARCH_CALL)

    with caplog.at_level("INFO", logger="ticketscope.mcp.auth"):
        _run(scenario, StubIssuer())
    assert "reason=no_token" in caplog.text
    assert "Bearer" not in caplog.text


def test_lifespan_reaches_the_app_and_websocket_is_closed_with_1008() -> None:
    reached: list[str] = []
    sent: list[Any] = []

    async def inner(scope: Any, receive: Any, send: Any) -> None:
        reached.append(scope["type"])

    async def send(message: MutableMapping[str, Any]) -> None:
        sent.append(message)

    async def receive() -> MutableMapping[str, Any]:
        return {}

    issuer = StubIssuer()
    verifier = mcp_auth.TokenVerifier(CONFIG, mcp_auth.KeyCache(ISSUER, issuer.client()))
    middleware = mcp_auth.AuthMiddleware(inner, config=CONFIG, verifier=verifier)

    async def main() -> None:
        await middleware({"type": "lifespan"}, receive, send)
        await middleware({"type": "websocket", "path": "/mcp", "headers": []}, receive, send)

    asyncio.run(main())
    assert reached == ["lifespan"]
    assert sent == [{"type": "websocket.close", "code": 1008}]


def _main_env(monkeypatch: pytest.MonkeyPatch, **env: str) -> list[Any]:
    monkeypatch.setenv("TICKETSCOPE_API_BASE_URL", "http://api")
    monkeypatch.setenv("TICKETSCOPE_MCP_ALLOWED_HOSTS", HOST)
    for name in ("ENABLED", "ISSUER", "AUDIENCE"):
        monkeypatch.delenv(f"TICKETSCOPE_MCP_AUTH_{name}", raising=False)
    for name, value in env.items():
        monkeypatch.setenv(f"TICKETSCOPE_MCP_AUTH_{name}", value)
    monkeypatch.setattr(mcp_main.telemetry, "setup", lambda *a, **k: None)
    served: list[Any] = []
    monkeypatch.setattr(mcp_main.uvicorn, "run", lambda app, **kw: served.append(app))
    return served


@pytest.mark.parametrize(
    "env",
    [
        {"ENABLED": "true"},
        {"ENABLED": "true", "ISSUER": ISSUER},
        {"ENABLED": "true", "AUDIENCE": AUDIENCE},
        {"ENABLED": "true", "ISSUER": "  ", "AUDIENCE": AUDIENCE},
        {"ENABLED": "true", "ISSUER": ISSUER, "AUDIENCE": "not-a-url"},
        {"ENABLED": "true", "ISSUER": "foo", "AUDIENCE": AUDIENCE},
        {"ENABLED": "true", "ISSUER": "//auth.stub.test", "AUDIENCE": AUDIENCE},
        {"ENABLED": "true", "ISSUER": "ftp://auth.stub.test", "AUDIENCE": AUDIENCE},
        {"ENABLED": "true", "ISSUER": ISSUER + "/", "AUDIENCE": AUDIENCE},
        {"ENABLED": "true", "ISSUER": ISSUER, "AUDIENCE": "//mcp.stub.test/mcp"},
    ],
)
def test_main_refuses_auth_on_with_a_missing_issuer_or_audience(
    monkeypatch: pytest.MonkeyPatch, env: dict[str, str]
) -> None:
    served = _main_env(monkeypatch, **env)
    with pytest.raises(SystemExit):
        mcp_main.main()
    assert served == []


def test_main_serves_with_auth_off_by_default_and_on_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    served = _main_env(monkeypatch, ISSUER=ISSUER, AUDIENCE=AUDIENCE)
    mcp_main.main()
    assert [m.cls for m in served[0].user_middleware if m.cls is mcp_auth.AuthMiddleware] == []
    served = _main_env(monkeypatch, ENABLED="true", ISSUER=ISSUER, AUDIENCE=AUDIENCE)
    mcp_main.main()
    assert any(m.cls is mcp_auth.AuthMiddleware for m in served[0].user_middleware)


def test_a_token_whose_iat_is_ahead_of_the_pod_clock_is_accepted() -> None:
    # The issuer's clock runs ahead of the pod's; `exp` alone bounds the token.
    issuer = StubIssuer()
    token = issuer.mint(iat=int(time.time()) + 5)

    async def scenario(http: httpx2.AsyncClient) -> int:
        return (await http.post("/mcp", headers=_bearer(token), json=SEARCH_CALL)).status_code

    assert _run(scenario, issuer) == 200


def test_a_cached_kid_does_not_wait_behind_a_stalled_refetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    issuer = StubIssuer()
    clock = [0.0]
    monkeypatch.setattr(mcp_auth, "_now", lambda: clock[0])
    stall = asyncio.Event()

    async def handle(request: httpx2.Request) -> httpx2.Response:
        if stall.is_set():
            await asyncio.sleep(3600)
        return issuer.handle(request)

    async def main() -> tuple[Any, bool]:
        cache = mcp_auth.KeyCache(
            ISSUER, httpx2.AsyncClient(transport=httpx2.MockTransport(handle))
        )
        await cache.get(issuer.current_kid)
        clock[0] += mcp_auth.KEY_LIFETIME_SECONDS + 1
        stall.set()
        refetch = asyncio.create_task(cache.get(issuer.current_kid))
        await asyncio.sleep(0)  # the refetch takes the lock and stalls on the issuer
        key = await asyncio.wait_for(cache.get(issuer.current_kid), timeout=1)
        pending = not refetch.done()
        refetch.cancel()
        return key, pending

    key, pending = asyncio.run(main())
    assert key is not None
    assert pending


def test_a_hung_issuer_is_bounded_by_one_timeout_for_the_whole_fetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mcp_auth, "FETCH_TIMEOUT_SECONDS", 0.05)

    async def hang(request: httpx2.Request) -> httpx2.Response:
        await asyncio.sleep(3600)
        return httpx2.Response(500)

    async def main() -> None:
        cache = mcp_auth.KeyCache(ISSUER, httpx2.AsyncClient(transport=httpx2.MockTransport(hang)))
        await asyncio.wait_for(cache.get("any"), timeout=2)

    with pytest.raises(mcp_auth.KeysUnavailableError):
        asyncio.run(main())


def test_build_app_with_auth_needs_a_key_client() -> None:
    client = ApiClient("http://api", 5, transport=httpx2.MockTransport(_fake_api))
    settings = Settings(mcp_allowed_hosts=HOST, api_base_url="http://api")  # pyright: ignore[reportArgumentType]
    with pytest.raises(ValueError, match="key_client"):
        build_app(settings, client, CONFIG)
