## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import time
from typing import Any

import httpx
from mcp.server.auth.provider import AccessToken, TokenVerifier


class JWKSBearerVerifier:
    """JWT Bearer token verifier using JWKS for key discovery.

    Validates RS256-signed JWTs against a remote JWKS endpoint,
    with optional issuer and audience enforcement.
    Implements the mcp.server.auth.provider.TokenVerifier protocol.
    """

    def __init__(
        self,
        jwks_uri: str,
        issuer: str | None = None,
        audience: str | None = None,
        required_scopes: list[str] | None = None,
        jwks_ttl: float = 300,
    ):
        if not jwks_uri.startswith("https://"):
            raise ValueError("jwks_uri must use HTTPS")
        self.jwks_uri = jwks_uri
        self.issuer = issuer
        self.audience = audience
        self.required_scopes = required_scopes
        self._jwks_cache: dict[str, Any] | None = None
        self._jwks_fetched_at: float = 0
        self._jwks_ttl: float = jwks_ttl
        self._jwks_last_error_at: float = 0

    async def _get_jwks(self) -> dict[str, Any] | None:
        if self._jwks_cache and (time.time() - self._jwks_fetched_at) < self._jwks_ttl:
            return self._jwks_cache
        if time.time() - self._jwks_last_error_at < 30:
            return None
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.jwks_uri)
                resp.raise_for_status()
                self._jwks_cache = resp.json()
                self._jwks_fetched_at = time.time()
        except httpx.HTTPError:
            self._jwks_last_error_at = time.time()
            return None
        return self._jwks_cache

    async def verify_token(self, token: str) -> AccessToken | None:
        from authlib.jose import JsonWebKey, jwt as authlib_jwt
        from authlib.jose.errors import JoseError

        try:
            jwks_data = await self._get_jwks()
            if jwks_data is None:
                return None
            keyset = JsonWebKey.import_key_set(jwks_data)

            claims = authlib_jwt.decode(token, keyset)
            claims.validate()

            if self.issuer and claims.get("iss") != self.issuer:
                return None
            if self.audience:
                aud = claims.get("aud")
                if isinstance(aud, list):
                    if self.audience not in aud:
                        return None
                elif aud != self.audience:
                    return None

            token_scopes = claims.get("scope", "").split() if claims.get("scope") else []
            if self.required_scopes:
                if not all(s in token_scopes for s in self.required_scopes):
                    return None

            return AccessToken(
                token=token,
                client_id=claims.get("client_id", claims.get("sub", "unknown")),
                scopes=token_scopes,
                claims=dict(claims),
            )
        except (JoseError, httpx.HTTPError, KeyError, ValueError):
            return None
