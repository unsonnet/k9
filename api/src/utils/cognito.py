from __future__ import annotations

import json
import time
from functools import lru_cache
from typing import Any, Dict, Optional

import requests
from jose import jwt

from config import settings
from utils.http import Unauthorized


def _jwks_url(user_pool_id: str) -> str:
    region = settings().aws_region
    return f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"


@lru_cache(maxsize=8)
def _cached_jwks(user_pool_id: str) -> Dict[str, Any]:
    url = _jwks_url(user_pool_id)
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    return resp.json()


def verify_cognito_jwt(token: str, token_use: str = "access") -> Dict[str, Any]:
    """
    Verify a Cognito JWT (access or id token) using the User Pool JWKS.

    - Validates signature, issuer, audience, token_use, expiration.
    - Returns claims on success; raises Unauthorized on failure.
    """
    cfg = settings()
    user_pool_id = cfg.cognito_user_pool_id
    client_id = cfg.cognito_client_id
    if not (user_pool_id and client_id):
        raise Unauthorized("Cognito is not configured")

    try:
        # First do an unverified header parse to get kid
        headers = jwt.get_unverified_header(token)
        jwks = _cached_jwks(user_pool_id)
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == headers.get("kid")), None)
        if not key:
            raise Unauthorized("Key not found for token")

        issuer = f"https://cognito-idp.{cfg.aws_region}.amazonaws.com/{user_pool_id}"
        options = {"verify_aud": True, "verify_iat": True}
        claims = jwt.decode(
            token,
            key,
            algorithms=[key.get("alg", "RS256")],
            audience=client_id,
            issuer=issuer,
            options=options,
        )
    except Exception as e:  # noqa: BLE001
        raise Unauthorized(str(e))

    # Token use check (access or id)
    if token_use and claims.get("token_use") != token_use:
        raise Unauthorized("Invalid token_use")

    # Basic time checks (jose already validates exp/iat/nbf)
    now = int(time.time())
    if claims.get("exp") and now > int(claims["exp"]):
        raise Unauthorized("Token expired")

    return claims
