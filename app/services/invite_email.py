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


def _already_registered(message: str) -> bool:
    message = message.lower()
    return "already registered" in message or "already been registered" in message


async def send_invite(email: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    if not settings.use_brevo_transactional_email:
        return await supabase_auth.invite_user_by_email(email, data=data)

    try:
        link = await supabase_auth.generate_link(
            "invite", email, data=data, redirect_to=f"{settings.frontend_url}/accept-invite"
        )
    except ApiError as exc:
        if not _already_registered(exc.message):
            raise
        # generate_link(type="invite") refuses to touch an email that already
        # has an auth user — which is exactly the normal case for "Resend
        # invite" on someone who was invited before but never finished
        # setting a password (their auth user already exists, just
        # unconfirmed). A "recovery" link is the same set-a-new-password
        # flow and works fine against an existing, even unconfirmed, user —
        # reset_password_for_email()/`/recover` already relies on the same
        # thing elsewhere in this codebase.
        link = await supabase_auth.generate_link(
            "recovery", email, redirect_to=f"{settings.frontend_url}/accept-invite"
        )
    action_link = link.get("action_link")
    if not action_link:
        print(f"invite_email.send_invite: unexpected generate_link response: {link!r}")
        raise ApiError(502, "Supabase did not return a usable invite link")

    # Don't trust generate_link's own response shape for the id (it's
    # undocumented here and got this wrong once already — every other admin
    # flow in this codebase, e.g. change-email/reset-password, already looks
    # the account up by email afterward instead of trusting a returned id).
    # This guarantees the profile row we create is keyed by the SAME id
    # Supabase itself considers canonical for this email — a mismatch here
    # is exactly what would make the account created but unable to sign in.
    auth_user = await supabase_auth.admin_get_user_by_email(email)
    if auth_user is None or not auth_user.get("id"):
        print(f"invite_email.send_invite: generate_link succeeded but admin_get_user_by_email found nothing for {email}")
        raise ApiError(502, "Supabase did not return a usable invite link")
    user_id = auth_user["id"]

    name = (data or {}).get("name") or "Participant"
    await brevo_email.send_template_email(
        settings.brevo_invite_template_id,
        to_email=email,
        to_name=name,
        params={"NAME": name, "EMAIL": email, "CONFIRMATION_URL": action_link},
    )
    return {"id": user_id}
