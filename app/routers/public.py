"""Unauthenticated, public routes — safe to call from any origin (the
marketing landing page at hackspirelumina.com has no login). Keep this
router intentionally tiny: every response shape here is exposed with zero
auth, so never reuse an authenticated schema/route here without checking
it's safe to expose publicly.
"""

import html

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import ApiError
from app.core.limiter import limiter
from app.db.session import get_db
from app.schemas.common import MessageResponse, error_responses
from app.schemas.public import PublicContactRequest, PublicLandingCountdownRead
from app.services import brevo_email
from app.services.submissions import get_event_settings

router = APIRouter(prefix="/public", tags=["Public"])


@router.get(
    "/landing-countdown",
    response_model=PublicLandingCountdownRead,
    summary="Countdown target for the public marketing landing page",
    description=(
        "No authentication required — read by the standalone marketing site at "
        "the apex domain, which has no login. Returns null fields if an admin "
        "hasn't set this yet (see PATCH /admin/event/landing-countdown)."
    ),
)
async def get_landing_countdown(db: AsyncSession = Depends(get_db)) -> PublicLandingCountdownRead:
    settings_row = await get_event_settings(db)
    return PublicLandingCountdownRead(
        landing_countdown_at=settings_row.landing_countdown_at,
        landing_countdown_label=settings_row.landing_countdown_label,
    )


@router.post(
    "/contact",
    response_model=MessageResponse,
    summary="Send a message from the landing page's Help Desk contact form",
    description=(
        "No authentication required — called by the standalone marketing site. "
        "Rate-limited per IP. Emails the submission to the event's contact "
        "inbox with the sender's address set as reply-to."
    ),
    responses=error_responses(422, 429, 502, 503),
)
@limiter.limit("3/minute")
async def submit_contact(request: Request, body: PublicContactRequest) -> MessageResponse:
    safe_name = html.escape(body.name)
    safe_message = html.escape(body.message).replace("\n", "<br>")
    html_content = (
        f"<p><strong>From:</strong> {safe_name} ({html.escape(body.email)})</p>"
        f"<p><strong>Message:</strong></p>"
        f"<p>{safe_message}</p>"
    )
    try:
        await brevo_email.send_raw_email(
            to_email=settings.contact_recipient_email,
            to_name="Hackspire: Lumina Help Desk",
            subject=f"[Hackspire: Lumina] New message from {safe_name}",
            html_content=html_content,
            reply_to_email=body.email,
            reply_to_name=body.name,
        )
    except ApiError as exc:
        # Don't leak Brevo's raw error text (sender config, API detail, etc.)
        # to an unauthenticated public caller — log it server-side instead.
        print(f"public.submit_contact: Brevo send failed: {exc.message}")
        raise ApiError(502, "Failed to send your message. Please try again shortly or email us directly.")
    return MessageResponse(message="Message sent.")
