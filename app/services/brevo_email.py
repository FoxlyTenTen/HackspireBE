"""Brevo Transactional Email API — a thin wrapper, used only when
settings.use_brevo_transactional_email is on (see services/invite_email.py).

This is deliberately separate from Supabase's own SMTP-relay-via-Brevo setup
(Supabase Dashboard → Authentication → SMTP Settings): that path uses a
Brevo *SMTP key* and Supabase's own mailer/templates. This module uses
Brevo's *API key* (a different credential — settings.brevo_api_key, env var
SMTP_API) and a template built directly in Brevo's dashboard
(Transactional → Templates), called via Brevo's HTTP API instead of SMTP.
"""

import httpx

from app.core.config import settings
from app.core.errors import ApiError

BREVO_API_BASE = "https://api.brevo.com/v3"


async def send_template_email(
    template_id: int, *, to_email: str, to_name: str, params: dict[str, str]
) -> None:
    if not settings.brevo_api_key:
        raise ApiError(503, "Brevo API key is not configured (SMTP_API)")
    if not template_id:
        raise ApiError(503, "Brevo template id is not configured")
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{BREVO_API_BASE}/smtp/email",
            headers={
                "api-key": settings.brevo_api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "templateId": template_id,
                "to": [{"email": to_email, "name": to_name}],
                "params": params,
            },
        )
    if not response.is_success:
        try:
            detail = response.json().get("message", response.text)
        except ValueError:
            detail = response.text
        raise ApiError(502, f"Brevo send failed: {detail}")
