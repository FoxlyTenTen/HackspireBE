"""Thin async wrapper over Supabase Storage's REST API.

Mirrors app/services/supabase_auth.py's pattern (raw httpx, not the SDK — the
SDK client is stateful and races under concurrent requests). Buckets are
public, so uploaded objects are reachable at a stable
/storage/v1/object/public/<bucket>/<path> URL with no signing required.
"""

import httpx

from app.core.config import settings
from app.core.errors import ApiError

_client: httpx.AsyncClient | None = None


def _http() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(base_url=f"{settings.supabase_url}/storage/v1", timeout=30.0)
    return _client


def _require_service_role() -> None:
    if not (settings.supabase_url and settings.supabase_service_role_key):
        raise ApiError(
            503, "Supabase Storage is not configured — set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env"
        )


def _service_headers() -> dict[str, str]:
    return {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
    }


def _error_message(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text or f"Supabase Storage error {response.status_code}"
    return data.get("message") or data.get("error") or f"Supabase Storage error {response.status_code}"


def public_url(bucket: str, object_path: str) -> str:
    return f"{settings.supabase_url}/storage/v1/object/public/{bucket}/{object_path}"


async def upload_object(
    bucket: str, object_path: str, content: bytes, content_type: str | None = None
) -> str:
    """POST /object/{bucket}/{path} — uploads the file and returns its public URL."""
    _require_service_role()
    headers = _service_headers()
    headers["Content-Type"] = content_type or "application/octet-stream"
    response = await _http().post(f"/object/{bucket}/{object_path}", headers=headers, content=content)
    if not response.is_success:
        raise ApiError(response.status_code, _error_message(response))
    return public_url(bucket, object_path)


async def delete_object(bucket: str, object_path: str) -> None:
    """DELETE /object/{bucket}/{path} — missing objects are treated as already-deleted."""
    _require_service_role()
    response = await _http().delete(f"/object/{bucket}/{object_path}", headers=_service_headers())
    if not response.is_success and response.status_code != 404:
        raise ApiError(response.status_code, _error_message(response))
