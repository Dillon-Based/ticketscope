"""A stub authorisation server for the resource-server tests (epic-mcp-oauth, story 2).

It generates RSA keys, serves the discovery document and the JWKS through an
`httpx2.MockTransport`, and mints tokens with the claims the spike recorded. No real `sub`.
"""

import base64
import time
import uuid
from typing import Any

import httpx2
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

ISSUER = "https://auth.stub.test"
AUDIENCE = "https://mcp.stub.test/mcp"
CLIENT_ID = "https://client.stub.test/client.json"
SCOPE = "email offline_access openid profile"
LIFETIME_SECONDS = 300


def _b64(number: int) -> str:
    raw = number.to_bytes((number.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


class StubIssuer:
    def __init__(self, issuer: str = ISSUER, audience: str = AUDIENCE) -> None:
        self.issuer = issuer
        self.audience = audience
        self.requests: list[str] = []
        self.down = False
        self._keys: dict[str, rsa.RSAPrivateKey] = {}
        self.current_kid = ""
        self.rotate()

    def rotate(self, *, keep_old: bool = True) -> str:
        """Issue a new signing key; the JWKS then lists it (and the old ones if `keep_old`)."""
        if not keep_old:
            self._keys.clear()
        kid = uuid.uuid4().hex[:8]
        self._keys[kid] = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.current_kid = kid
        return kid

    def private_key(self, kid: str | None = None) -> rsa.RSAPrivateKey:
        return self._keys[kid or self.current_kid]

    def mint(
        self, *, kid: str | None = None, key: Any = None, alg: str = "RS256", **overrides: Any
    ) -> str:
        now = int(time.time())
        claims: dict[str, Any] = {
            "iss": self.issuer,
            "aud": self.audience,
            "iat": now,
            "exp": now + LIFETIME_SECONDS,
            "auth_time": now,
            "jti": uuid.uuid4().hex,
            "sid": uuid.uuid4().hex,
            "scope": SCOPE,
            "client_id": CLIENT_ID,
        }
        claims.update(overrides)
        claims = {k: v for k, v in claims.items() if v is not None}
        use_kid = kid or self.current_kid
        return jwt.encode(
            claims, key if key is not None else self.private_key(use_kid), alg, {"kid": use_kid}
        )

    def jwks(self) -> dict[str, Any]:
        keys = []
        for kid, private in self._keys.items():
            numbers = private.public_key().public_numbers()
            keys.append(
                {
                    "kty": "RSA",
                    "kid": kid,
                    "use": "sig",
                    "alg": "RS256",
                    "n": _b64(numbers.n),
                    "e": _b64(numbers.e),
                }
            )
        return {"keys": keys}

    def handle(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request.url.path)
        if self.down:
            raise httpx2.ConnectError("issuer down")
        if request.url.path == "/.well-known/oauth-authorization-server":
            return httpx2.Response(
                200, json={"issuer": self.issuer, "jwks_uri": f"{self.issuer}/jwks"}
            )
        if request.url.path == "/jwks":
            return httpx2.Response(200, json=self.jwks())
        return httpx2.Response(404)

    def client(self) -> httpx2.AsyncClient:
        return httpx2.AsyncClient(transport=httpx2.MockTransport(self.handle))

    @property
    def jwks_fetches(self) -> int:
        return self.requests.count("/jwks")
