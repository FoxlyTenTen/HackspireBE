"""Unauthenticated, public routes — safe to call from any origin (the
marketing landing page at hackspirelumina.com has no login). Keep this
router intentionally tiny: every response shape here is exposed with zero
auth, so never reuse an authenticated schema/route here without checking
it's safe to expose publicly.
"""

from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.session import get_db
from app.schemas.public import PublicLandingCountdownRead
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
