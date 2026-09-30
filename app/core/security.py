"""Supabase access-token verification.

The app no longer mints its own JWTs — Supabase Auth issues every token. We
verify them locally: legacy projects sign with a shared HS256 secret
(SUPABASE_JWT_SECRET), newer projects use asymmetric keys published at the
project's JWKS endpoint, which we fetch and cache.
"""

import time

import httpx
from jose import JWTError, jwt

from app.core.config import settings

_JWKS_TTL_SECONDS = 3600
_jwks_cache: dict | None = None
_jwks_fetched_at: float = 0.0


async def _get_jwks() -> dict:
    global _jwks_cache, _jwks_fetched_at
    now = time.monotonic()
    if _jwks_cache is None or now - _jwks_fetched_at > _JWKS_TTL_SECONDS:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.supabase_url}/auth/v1/.well-known/jwks.json",
                headers={"apikey": settings.supabase_anon_key},
            )
            response.raise_for_status()
            _jwks_cache = response.json()
            _jwks_fetched_at = now
    return _jwks_cache


async def decode_supabase_token(token: str) -> dict | None:
    """Verify signature + expiry and return the claims, or None if invalid."""
    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        return None
    alg = header.get("alg", "")
    if alg not in {"HS256", "RS256", "ES256"}:
        # Explicit allow-list — without this, an attacker-chosen alg (e.g.
        # "none") is passed straight into jwt.decode's algorithms=[alg]
        # below. Real Supabase tokens only ever use HS256 or RS256.
        return None
    try:
        if alg == "HS256":
            if not settings.supabase_jwt_secret:
                return None
            return jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        jwks = await _get_jwks()
        kid = header.get("kid")
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if key is None:
            return None
        return jwt.decode(token, key, algorithms=[alg], audience="authenticated")
    except (JWTError, httpx.HTTPError):
        return None
