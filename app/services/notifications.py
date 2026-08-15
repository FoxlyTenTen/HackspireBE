import uuid
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import Notification, Profile


def create_notification(
    db: AsyncSession,
    participant_id: uuid.UUID,
    type: str,
    message: str,
    reference_id: uuid.UUID | None = None,
) -> Notification:
    """Stage a notification row on the session (committed with the caller's transaction)."""
    notification = Notification(
        participant_id=participant_id,
        type=type,
        message=message,
        reference_id=reference_id,
    )
    db.add(notification)
    return notification


def create_notifications(
    db: AsyncSession,
    participant_ids: Iterable[uuid.UUID],
    type: str,
    message: str,
    reference_id: uuid.UUID | None = None,
) -> None:
    for pid in participant_ids:
        create_notification(db, pid, type, message, reference_id)


async def list_for_user(db: AsyncSession, participant_id: uuid.UUID) -> list[Notification]:
    result = await db.scalars(
        select(Notification)
        .where(Notification.participant_id == participant_id)
        .order_by(Notification.created_at.desc())
    )
    return list(result)


async def all_participant_ids(db: AsyncSession) -> list[uuid.UUID]:
    result = await db.scalars(select(Profile.id).where(Profile.role == "participant"))
    return list(result)


async def mark_read(
    db: AsyncSession, participant_id: uuid.UUID, notification_id: uuid.UUID
) -> Notification:
    notification = await db.get(Notification, notification_id)
    if notification is None or notification.participant_id != participant_id:
        raise ApiError(404, "Notification not found")
    notification.read = True
    await db.commit()
    return notification
