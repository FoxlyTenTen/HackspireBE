from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Profile
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.common import error_responses
from app.schemas.notification import NotificationRead
from app.services import notifications as notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=list[NotificationRead],
    summary="Poll the current user's notifications",
    description=(
        "Polling-based (no websockets): join-request outcomes, team updates and "
        "announcements, newest first."
    ),
    responses=error_responses(401, 403),
)
async def list_notifications(
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationRead]:
    return await notification_service.list_for_user(db, user.id)
