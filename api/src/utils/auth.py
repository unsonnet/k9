from __future__ import annotations

import time
from typing import Any, Dict, Optional

from jose import jwt, JWTError

from config import settings
from utils.http import Unauthorized
from utils.cognito import verify_cognito_jwt


def parse_bearer(auth_header: Optional[str]) -> str:
    if not auth_header or not auth_header.startswith("Bearer "):
        raise Unauthorized("Missing or invalid Authorization header")
    return auth_header.split(" ", 1)[1]


def create_token(sub: str, ttl: int, token_type: str = "access", extra: Optional[Dict[str, Any]] = None) -> str:
    now = int(time.time())
    payload: Dict[str, Any] = {
        "iss": settings().jwt_issuer,
        "aud": settings().jwt_audience,
        "iat": now,
        "nbf": now,
        "exp": now + ttl,
        "sub": sub,
        "typ": token_type,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings().jwt_secret, algorithm="HS256")


def verify_token(token: str, expected_typ: Optional[str] = None) -> Dict[str, Any]:
    cfg = settings()
    if cfg.auth_mode == "cognito":
        # In Cognito mode, verify RS256 using JWKS and validate token_use according to expected_typ mapping
        token_use = "access" if expected_typ in (None, "access") else "id"
        claims = verify_cognito_jwt(token, token_use=token_use)
        return claims
    # Local mode (HS256, used for dev/tests)
    try:
        claims = jwt.decode(
            token,
            cfg.jwt_secret,
            algorithms=["HS256"],
            audience=cfg.jwt_audience,
            options={"verify_aud": True},
        )
    except JWTError as e:
        raise Unauthorized(str(e))
    if expected_typ and claims.get("typ") != expected_typ:
        raise Unauthorized("Invalid token type")
    return claims


def get_auth_claims(event: Dict[str, Any], expected_typ: Optional[str] = None) -> Dict[str, Any]:
    """Extract and verify auth claims from an API Gateway HTTP API event.

    Prefers the JWT already validated by API Gateway (requestContext.authorizer.jwt.claims) when present.
    Falls back to Authorization header Bearer token.
    """
    # API Gateway HTTP API v2 with JWT authorizer provides claims
    ctx = event.get("requestContext", {})
    authz = ctx.get("authorizer", {})
    jwt_ctx = authz.get("jwt", {})
    claims = jwt_ctx.get("claims")
    if isinstance(claims, dict) and claims:
        return claims  # already verified by API Gateway
    # Fallback: parse Authorization header and verify
    headers = event.get("headers") or {}
    token = parse_bearer(headers.get("Authorization") or headers.get("authorization"))
    return verify_token(token, expected_typ=expected_typ)
