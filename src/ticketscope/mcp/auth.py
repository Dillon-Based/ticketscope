"""OAuth 2.1 resource-server checks for `mcp` (epic-mcp-oauth, story 2).

A pure-ASGI middleware refuses any request without a valid RS256 bearer token. A token is valid
when its signature verifies against a key the issuer publishes, `iss` and `aud` match, and `exp`
is in the future. There is no scope check: the audience, the `/mcp` URL, is the gate. The reason
a token failed is logged as a code and never sent to the caller; the token is never logged.
"""

import asyncio
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import httpx2
import jwt
from jwt.algorithms import RSAAlgorithm
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("ticketscope.mcp.auth")

ALGORITHM = "RS256"
METADATA_PATH = "/.well-known/oauth-protected-resource"
HEALTH_PATH = "/healthz"
OPEN_PATHS = frozenset({METADATA_PATH, HEALTH_PATH})
DISCOVERY_PATH = "/.well-known/oauth-authorization-server"
KEY_LIFETIME_SECONDS = 600.0
MIN_REFETCH_SECONDS = 30.0
FETCH_TIMEOUT_SECONDS = 5.0


@dataclass(frozen=True)
class AuthConfig:
    issuer: str
    audience: str


def metadata_url(audience: str) -> str:
    """The protected-resource metadata URL, on the origin of the audience."""
    parts = urlsplit(audience)
    return f"{parts.scheme}://{parts.netloc}{METADATA_PATH}"


def metadata_body(config: AuthConfig) -> dict[str, Any]:
    return {
        "resource": config.audience,
        "authorization_servers": [config.issuer],
        "bearer_methods_supported": ["header"],
    }


def _now() -> float:
    return time.monotonic()


class KeysUnavailableError(Exception):
    """The issuer's signing keys could not be fetched and no cached key can answer."""


class InvalidTokenError(Exception):
    """A token that is refused; `reason` is a short code for the log."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class KeyCache:
    """The issuer's signing keys, by `kid`.

    Keys live `KEY_LIFETIME_SECONDS`. An unknown `kid` triggers one refetch, and no fetch (good
    or failed) happens more often than every `MIN_REFETCH_SECONDS`, so a stream of bad `kid`s
    cannot hammer the issuer. When a refetch fails, keys already cached still answer.
    """

    def __init__(
        self,
        issuer: str,
        http: httpx2.AsyncClient,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._issuer = issuer.rstrip("/")
        self._http = http
        self._clock = clock or (lambda: _now())
        self._keys: dict[str, Any] = {}
        self._filled_at: float | None = None
        self._attempted_at: float | None = None
        self._lock = asyncio.Lock()

    async def get(self, kid: str) -> Any | None:
        """The key for `kid`, or None when the issuer does not publish it.

        A cached `kid` never waits behind another request's fetch: while one is in flight, the
        cached key answers even when it is past its lifetime.
        """
        if kid in self._keys and (self._is_fresh(self._clock()) or self._lock.locked()):
            return self._keys[kid]
        async with self._lock:
            now = self._clock()
            fresh = self._is_fresh(now)
            if fresh and kid in self._keys:
                return self._keys[kid]
            if self._attempted_at is not None and now - self._attempted_at < MIN_REFETCH_SECONDS:
                return self._known_or_raise(kid, fresh)
            self._attempted_at = now
            try:
                self._keys = await self._fetch()
                self._filled_at = now
            except KeysUnavailableError:
                if kid in self._keys:
                    return self._keys[kid]
                raise
            return self._keys.get(kid)

    def _is_fresh(self, now: float) -> bool:
        return self._filled_at is not None and now - self._filled_at < KEY_LIFETIME_SECONDS

    def _known_or_raise(self, kid: str, fresh: bool) -> Any | None:
        if kid in self._keys:
            return self._keys[kid]
        if self._filled_at is None or not fresh:
            raise KeysUnavailableError("no signing keys")
        return None

    async def _fetch(self) -> dict[str, Any]:
        """Both hops, bounded together by `FETCH_TIMEOUT_SECONDS`, the longest the lock is held."""
        try:
            async with asyncio.timeout(FETCH_TIMEOUT_SECONDS):
                discovery = await self._http.get(self._issuer + DISCOVERY_PATH)
                discovery.raise_for_status()
                jwks_uri = discovery.json()["jwks_uri"]
                if not isinstance(jwks_uri, str):
                    raise KeysUnavailableError("bad jwks_uri")
                response = await self._http.get(jwks_uri)
                response.raise_for_status()
                entries = response.json()["keys"]
            keys: dict[str, Any] = {}
            for entry in entries:
                if entry.get("kty") == "RSA" and isinstance(entry.get("kid"), str):
                    keys[entry["kid"]] = RSAAlgorithm.from_jwk(json.dumps(entry))
        except KeysUnavailableError:
            raise
        except Exception as error:
            raise KeysUnavailableError(type(error).__name__) from error
        return keys


class TokenVerifier:
    def __init__(self, config: AuthConfig, keys: KeyCache) -> None:
        self._config = config
        self._keys = keys

    async def verify(self, token: str) -> None:
        """Return when the token is valid; raise `InvalidTokenError` or `KeysUnavailableError`."""
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as error:
            raise InvalidTokenError("malformed") from error
        if header.get("alg") != ALGORITHM:
            raise InvalidTokenError("bad_alg")
        kid = header.get("kid")
        if not isinstance(kid, str):
            raise InvalidTokenError("no_kid")
        key = await self._keys.get(kid)
        if key is None:
            raise InvalidTokenError("unknown_kid")
        try:
            jwt.decode(
                token,
                key,
                algorithms=[ALGORITHM],
                audience=self._config.audience,
                issuer=self._config.issuer,
                # `exp` is strict (leeway 0). `iat` is not checked: a pod clock a fraction of a
                # second behind the issuer's would refuse a token used straight after minting,
                # and `exp` alone bounds a token's life.
                options={"require": ["iss", "aud", "exp"], "verify_iat": False},
                leeway=0,
            )
        except jwt.ExpiredSignatureError as error:
            raise InvalidTokenError("expired") from error
        except jwt.InvalidIssuerError as error:
            raise InvalidTokenError("bad_issuer") from error
        except jwt.InvalidAudienceError as error:
            raise InvalidTokenError("bad_audience") from error
        except jwt.InvalidSignatureError as error:
            raise InvalidTokenError("bad_signature") from error
        except jwt.PyJWTError as error:
            raise InvalidTokenError("invalid") from error


def _bearer(scope: Scope) -> str | InvalidTokenError | None:
    """The token; None when no Authorization header; an error for a header that is not bearer."""
    values = [v for k, v in scope["headers"] if k == b"authorization"]
    if not values:
        return None
    if len(values) > 1:
        return InvalidTokenError("malformed")
    scheme, _, token = values[0].decode("latin-1").partition(" ")
    if scheme.lower() != "bearer" or not token or " " in token:
        return InvalidTokenError("malformed")
    return token


class AuthMiddleware:
    def __init__(self, app: ASGIApp, *, config: AuthConfig, verifier: TokenVerifier) -> None:
        self.app = app
        self._verifier = verifier
        self._challenge = f'Bearer resource_metadata="{metadata_url(config.audience)}"'

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            await self.app(scope, receive, send)
            return
        if scope["type"] != "http":
            await send({"type": "websocket.close", "code": 1008})
            return
        if scope["path"] in OPEN_PATHS:
            await self.app(scope, receive, send)
            return
        found = _bearer(scope)
        if found is None:
            logger.info("auth refused reason=no_token")
            await self._reply(send, 401, self._challenge)
            return
        if isinstance(found, InvalidTokenError):
            await self._refuse(send, found.reason)
            return
        try:
            await self._verifier.verify(found)
        except InvalidTokenError as error:
            await self._refuse(send, error.reason)
            return
        except KeysUnavailableError:
            logger.warning("auth keys unavailable")
            await self._reply(send, 503, None)
            return
        await self.app(scope, receive, send)

    async def _refuse(self, send: Send, reason: str) -> None:
        logger.info("auth refused reason=%s", reason)
        await self._reply(send, 401, f'{self._challenge}, error="invalid_token"')

    @staticmethod
    async def _reply(send: Send, status: int, challenge: str | None) -> None:
        headers = [(b"content-length", b"0")]
        if challenge is not None:
            headers.append((b"www-authenticate", challenge.encode("latin-1")))
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": b""})
