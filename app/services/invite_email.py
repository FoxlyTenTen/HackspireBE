"""How an invite email actually gets delivered — one switch, two paths:

- Default (settings.use_brevo_transactional_email = False): unchanged
  behavior, Supabase's own /invite endpoint creates the user AND sends the
  email itself via whatever mailer is configured in Supabase's dashboard
  (currently Brevo SMTP relay).
- Opt-in (True): we call Supabase's /admin/generate_link instead (creates
  the same kind of user + link, but sends nothing), then send the email
  ourselves via Brevo's Transactional API using a template built in Brevo's
  dashboard. Flipping the flag back off instantly reverts to the default
  path with no code change/redeploy — see .env's USE_BREVO_TRANSACTIONAL_EMAIL.

Either path returns the same shape callers already rely on: a dict with at
least {"id": <auth user id>} (admin_import.py does uuid.UUID(auth_user["id"])).
"""

from typing import Any

from app.core.config import settings
from app.core.errors import ApiError
from app.services import brevo_email, supabase_auth


async def send_invite(email: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    if not settings.use_brevo_transactional_email:
        return await supabase_auth.invite_user_by_email(email, data=data)

    link = await supabase_auth.generate_link(
        "invite", email, data=data, redirect_to=f"{settings.frontend_url}/accept-invite"
    )
    user_id = link.get("id") or (link.get("user") or {}).get("id")
    action_link = link.get("action_link")
    if not user_id or not action_link:
        raise ApiError(502, "Supabase did not return a usable invite link")

    name = (data or {}).get("name") or "Participant"
    await brevo_email.send_template_email(
        settings.brevo_invite_template_id,
        to_email=email,
        to_name=name,
        params={"NAME": name, "EMAIL": email, "CONFIRMATION_URL": action_link},
    )
    return {"id": user_id}
