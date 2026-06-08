## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import time
from typing import Any

import httpx
from fastmcp.server.auth import AccessToken, TokenVerifier


class JWKSBearerVerifier(TokenVerifier):
    """JWT Bearer token verifier using JWKS for key discovery.

    Validates RS256-signed JWTs against a remote JWKS endpoint,
    with optional issuer and audience enforcement.
    """

    def __init__(
        self,
        jwks_uri: str,
        issuer: str | None = None,
        audience: str | None = None,
        required_scopes: list[str] | None = None,
    ):
        super().__init__(required_scopes=required_scopes)
        self.jwks_uri = jwks_uri
        self.issuer = issuer
        self.audience = audience
        self._jwks_cache: dict[str, Any] | None = None
        self._jwks_fetched_at: float = 0
        self._jwks_ttl: float = 300

    async def _get_jwks(self) -> dict[str, Any]:
        if self._jwks_cache and (time.time() - self._jwks_fetched_at) < self._jwks_ttl:
            return self._jwks_cache
        async with httpx.AsyncClient() as client:
            resp = await client.get(self.jwks_uri)
            resp.raise_for_status()
            self._jwks_cache = resp.json()
            self._jwks_fetched_at = time.time()
        return self._jwks_cache

    def _invalidate_cache(self) -> None:
        self._jwks_cache = None
        self._jwks_fetched_at = 0

    async def verify_token(self, token: str) -> AccessToken | None:
        import logging

        from authlib.jose import JsonWebKey, jwt as authlib_jwt
        from authlib.jose.errors import JoseError

        logger = logging.getLogger(__name__)

        try:
            return await self._attempt_verify(token, authlib_jwt, JsonWebKey)
        except JoseError as e:
            logger.debug("Auth verification failed, retrying with refreshed JWKS: %s", e)
            self._invalidate_cache()
            try:
                return await self._attempt_verify(token, authlib_jwt, JsonWebKey)
            except JoseError as e2:
                logger.debug("Auth rejected after JWKS refresh: %s", e2)
                return None
        except (httpx.HTTPError, KeyError, ValueError) as e:
            logger.debug("Auth rejected: %s", e)
            return None

    async def _attempt_verify(self, token: str, authlib_jwt: Any, JsonWebKey: Any) -> AccessToken | None:
        import logging

        logger = logging.getLogger(__name__)

        jwks_data = await self._get_jwks()
        keyset = JsonWebKey.import_key_set(jwks_data)

        claims = authlib_jwt.decode(token, keyset)
        claims.validate()

        if self.issuer and claims.get("iss") != self.issuer:
            logger.debug("Auth rejected: issuer mismatch (expected=%s, got=%s)", self.issuer, claims.get("iss"))
            return None
        if self.audience:
            aud = claims.get("aud")
            if isinstance(aud, list):
                if self.audience not in aud:
                    logger.debug("Auth rejected: audience %s not in %s", self.audience, aud)
                    return None
            elif aud != self.audience:
                logger.debug("Auth rejected: audience mismatch (expected=%s, got=%s)", self.audience, aud)
                return None

        token_scopes = claims.get("scope", "").split() if claims.get("scope") else []
        if self.required_scopes:
            if not all(s in token_scopes for s in self.required_scopes):
                logger.debug("Auth rejected: missing scopes (required=%s, got=%s)", self.required_scopes, token_scopes)
                return None

        return AccessToken(
            token=token,
            client_id=claims.get("client_id", claims.get("sub", "unknown")),
            scopes=token_scopes,
            claims=dict(claims),
        )
