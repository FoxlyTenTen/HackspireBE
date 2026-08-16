"""Thin async wrappers over Supabase Auth (GoTrue).

Each function is named after — and calls the exact endpoint behind — the
official Supabase SDK method it replaces (supabase.auth.sign_in_with_password,
auth.update_user, auth.reset_password_for_email, auth.admin.invite_user_by_email,
auth.admin.update_user_by_id, ...). We call the REST API directly with httpx
because this backend is stateless: the SDK client stores a session per client
instance, which races when concurrent requests sign in through one shared
client, and its update_user() cannot act on an arbitrary caller's token.
"""

from typing import Any

import httpx

from app.core.config import settings
from app.core.errors import ApiError

_client: httpx.AsyncClient | None = None


def _http() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(base_url=f"{settings.supabase_url}/auth/v1", timeout=15.0)
    return _client


def require_configured() -> None:
    if not (settings.supabase_url and settings.supabase_anon_key):
        raise ApiError(503, "Supabase Auth is not configured — set SUPABASE_URL and keys in .env")


def _require_service_role() -> None:
    require_configured()
    if not settings.supabase_service_role_key:
        raise ApiError(503, "SUPABASE_SERVICE_ROLE_KEY is not configured in .env")


def _anon_headers(bearer: str | None = None) -> dict[str, str]:
    return {
        "apikey": settings.supabase_anon_key,
        "Authorization": f"Bearer {bearer or settings.supabase_anon_key}",
    }


def _service_headers() -> dict[str, str]:
    return {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
    }


def _error_message(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text or f"Supabase Auth error {response.status_code}"
    return (
        data.get("error_description")
        or data.get("msg")
        or data.get("message")
        or data.get("error")
        or f"Supabase Auth error {response.status_code}"
    )


def _raise_for_status(response: httpx.Response, status_override: int | None = None) -> None:
    if response.is_success:
        return
    raise ApiError(status_override or response.status_code, _error_message(response))


async def sign_in_with_password(email: str, password: str) -> dict[str, Any]:
    """POST /token?grant_type=password — returns the session (access + refresh token)."""
    require_configured()
    response = await _http().post(
        "/token",
        params={"grant_type": "password"},
        headers=_anon_headers(),
        json={"email": email, "password": password},
    )
    if response.status_code in (400, 401, 403):
        # Normalize every credential-ish failure to the same message the old
        # custom auth used, so nothing about accounts is leaked.
        raise ApiError(401, "Invalid username or password")
    _raise_for_status(response)
    return response.json()


async def verify_otp(token_hash: str, type_: str) -> dict[str, Any]:
    """POST /verify — exchanges the token_hash from a PKCE-flow email link for a
    session. Newer Supabase projects redirect email links with
    `?token_hash=...&type=...` (server-verifiable) instead of putting the
    session directly in the URL fragment; this completes that exchange.
    """
    require_configured()
    response = await _http().post(
        "/verify",
        headers=_anon_headers(),
        json={"type": type_, "token_hash": token_hash},
    )
    if not response.is_success:
        raise ApiError(400, "This link is invalid or has expired")
    return response.json()


async def refresh_session(refresh_token: str) -> dict[str, Any]:
    """POST /token?grant_type=refresh_token — exchanges a refresh token for a new session."""
    require_configured()
    response = await _http().post(
        "/token",
        params={"grant_type": "refresh_token"},
        headers=_anon_headers(),
        json={"refresh_token": refresh_token},
    )
    if not response.is_success:
        raise ApiError(401, "Session expired — please log in again")
    return response.json()


async def reset_password_for_email(email: str) -> None:
    """POST /recover — sends Supabase's built-in password-reset email."""
    require_configured()
    response = await _http().post(
        "/recover",
        params={"redirect_to": f"{settings.frontend_url}/accept-invite"},
        headers=_anon_headers(),
        json={"email": email},
    )
    _raise_for_status(response)


async def update_user(
    access_token: str, *, password: str | None = None, email: str | None = None
) -> dict[str, Any]:
    """PUT /user — acts as the calling user (their own token).

    Changing `email` triggers Supabase's built-in email-change verification:
    the new address only becomes active after its confirmation link is clicked.
    """
    require_configured()
    body: dict[str, Any] = {}
    if password is not None:
        body["password"] = password
    if email is not None:
        body["email"] = email
    response = await _http().put(
        "/user",
        params={"redirect_to": f"{settings.frontend_url}/accept-invite"},
        headers=_anon_headers(bearer=access_token),
        json=body,
    )
    _raise_for_status(response, status_override=400 if response.status_code >= 500 else None)
    return response.json()


async def invite_user_by_email(email: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    """POST /invite — sends Supabase's invite email; returns the created auth user."""
    _require_service_role()
    response = await _http().post(
        "/invite",
        params={"redirect_to": f"{settings.frontend_url}/accept-invite"},
        headers=_service_headers(),
        json={"email": email, "data": data or {}},
    )
    _raise_for_status(response)
    return response.json()


async def admin_create_user(
    email: str, password: str, *, email_confirm: bool = True
) -> dict[str, Any]:
    """POST /admin/users — creates a user directly, no email sent."""
    _require_service_role()
    response = await _http().post(
        "/admin/users",
        headers=_service_headers(),
        json={"email": email, "password": password, "email_confirm": email_confirm},
    )
    _raise_for_status(response)
    return response.json()


async def admin_update_user_by_id(
    user_id: str,
    *,
    password: str | None = None,
    email: str | None = None,
    email_confirm: bool | None = None,
) -> dict[str, Any]:
    """PUT /admin/users/{id} — set a password/email or force-confirm the email.

    Unlike the user-context update_user, an admin email change here is applied
    immediately with no confirmation link — intended for correcting typos in
    imported addresses.
    """
    _require_service_role()
    body: dict[str, Any] = {}
    if password is not None:
        body["password"] = password
    if email is not None:
        body["email"] = email
    if email_confirm is not None:
        body["email_confirm"] = email_confirm
    response = await _http().put(
        f"/admin/users/{user_id}", headers=_service_headers(), json=body
    )
    _raise_for_status(response)
    return response.json()


async def admin_get_user_by_email(email: str) -> dict[str, Any] | None:
    """Page through GET /admin/users to find a user by email (no direct lookup exists)."""
    _require_service_role()
    page = 1
    target = email.lower()
    while True:
        response = await _http().get(
            "/admin/users",
            headers=_service_headers(),
            params={"page": page, "per_page": 100},
        )
        _raise_for_status(response)
        users = response.json().get("users", [])
        for user in users:
            if (user.get("email") or "").lower() == target:
                return user
        if len(users) < 100:
            return None
        page += 1
