import uuid
from datetime import datetime, timezone

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import EVENT_INFO
from app.core.errors import ApiError
from app.db.models import (
    Announcement,
    Finalist,
    Material,
    Profile,
    Team,
    TimelineItem,
    Winner,
)
from app.schemas.event import (
    AnnouncementCreate,
    AnnouncementUpdate,
    EventInfoResponse,
    FinalistRead,
    FinalistsPut,
    TimelineItemWrite,
    WinnerRead,
    WinnersPut,
)
from app.services.audit import log_admin_action
from app.services.notifications import all_participant_ids, create_notifications
from app.services.submissions import get_event_settings


async def event_info(db: AsyncSession) -> EventInfoResponse:
    settings_row = await get_event_settings(db)
    timeline = (
        await db.scalars(select(TimelineItem).order_by(TimelineItem.order_index))
    ).all()
    return EventInfoResponse(
        name=EVENT_INFO["name"],
        tagline=EVENT_INFO["tagline"],
        venue=EVENT_INFO["venue"],
        countdown_at=settings_row.countdown_at,
        submission_deadline_at=settings_row.submission_deadline_at,
        timeline=timeline,
        sponsors=EVENT_INFO["sponsors"],
        prize_pool=EVENT_INFO["prize_pool"],
        contact=EVENT_INFO["contact"],
    )


async def list_materials(db: AsyncSession) -> list[Material]:
    return list(
        (await db.scalars(select(Material).order_by(Material.uploaded_at.desc()))).all()
    )


async def list_finalists(
    db: AsyncSession, *, published_only: bool
) -> list[FinalistRead]:
    stmt = select(Finalist).options(selectinload(Finalist.team))
    if published_only:
        stmt = stmt.where(Finalist.published.is_(True))
    finalists = (await db.scalars(stmt)).all()
    return [
        FinalistRead(
            id=f.id,
            team_id=f.team_id,
            team_name=f.team.name,
            published=f.published,
            published_at=f.published_at,
        )
        for f in finalists
    ]


async def list_winners(db: AsyncSession, *, published_only: bool) -> list[WinnerRead]:
    stmt = select(Winner).options(selectinload(Winner.team))
    if published_only:
        stmt = stmt.where(Winner.published.is_(True))
    winners = (await db.scalars(stmt)).all()
    return [
        WinnerRead(
            id=w.id,
            team_id=w.team_id,
            team_name=w.team.name,
            placement=w.placement,
            published=w.published,
            published_at=w.published_at,
        )
        for w in winners
    ]


async def set_countdown(db: AsyncSession, admin: Profile, countdown_at: datetime):
    settings_row = await get_event_settings(db)
    settings_row.countdown_at = countdown_at
    settings_row.updated_at = datetime.now(timezone.utc)
    log_admin_action(
        db, admin.id, "countdown_updated", target_table="event_settings", target_id=None
    )
    await db.commit()
    return settings_row


async def set_submission_deadline(db: AsyncSession, admin: Profile, deadline_at: datetime):
    settings_row = await get_event_settings(db)
    settings_row.submission_deadline_at = deadline_at
    settings_row.updated_at = datetime.now(timezone.utc)
    log_admin_action(
        db, admin.id, "submission_deadline_updated", target_table="event_settings"
    )
    await db.commit()
    return settings_row


async def replace_timeline(
    db: AsyncSession, admin: Profile, items: list[TimelineItemWrite]
) -> list[TimelineItem]:
    await db.execute(sa_delete(TimelineItem))
    new_items = [
        TimelineItem(
            bootcamp_name=item.bootcamp_name,
            date_label=item.date_label,
            time_session=item.time_session,
            session_type=item.session_type,
            speaker_name=item.speaker_name,
            speaker_bio=item.speaker_bio,
            organization=item.organization,
            session_description=item.session_description,
            speaker_photo_url=item.speaker_photo_url,
            status=item.status,
            remarks=item.remarks,
            order_index=item.order_index,
        )
        for item in items
    ]
    db.add_all(new_items)
    log_admin_action(
        db,
        admin.id,
        "timeline_replaced",
        target_table="timeline_items",
        details=f"{len(new_items)} item(s)",
    )
    await db.commit()
    return sorted(new_items, key=lambda i: i.order_index)


async def _ensure_teams_exist(db: AsyncSession, team_ids: list[uuid.UUID]) -> None:
    existing = set(
        (await db.scalars(select(Team.id).where(Team.id.in_(team_ids)))).all()
    )
    missing = [str(tid) for tid in team_ids if tid not in existing]
    if missing:
        raise ApiError(404, f"Team(s) not found: {', '.join(missing)}")


async def put_finalists(
    db: AsyncSession, admin: Profile, data: FinalistsPut
) -> list[FinalistRead]:
    await _ensure_teams_exist(db, data.team_ids)
    await db.execute(sa_delete(Finalist))
    published_at = datetime.now(timezone.utc) if data.published else None
    db.add_all(
        Finalist(team_id=tid, published=data.published, published_at=published_at)
        for tid in data.team_ids
    )
    log_admin_action(
        db,
        admin.id,
        "finalists_published" if data.published else "finalists_updated",
        target_table="finalists",
        details=f"{len(data.team_ids)} team(s)",
    )
    await db.commit()
    return await list_finalists(db, published_only=False)


async def put_winners(db: AsyncSession, admin: Profile, data: WinnersPut) -> list[WinnerRead]:
    await _ensure_teams_exist(db, [w.team_id for w in data.winners])
    await db.execute(sa_delete(Winner))
    published_at = datetime.now(timezone.utc) if data.published else None
    db.add_all(
        Winner(
            team_id=w.team_id,
            placement=w.placement,
            published=data.published,
            published_at=published_at,
        )
        for w in data.winners
    )
    log_admin_action(
        db,
        admin.id,
        "winners_published" if data.published else "winners_updated",
        target_table="winners",
        details=f"{len(data.winners)} team(s)",
    )
    await db.commit()
    return await list_winners(db, published_only=False)


async def create_announcement(
    db: AsyncSession, admin: Profile, data: AnnouncementCreate
) -> Announcement:
    announcement = Announcement(
        title=data.title, body=data.body, image_url=data.image_url, posted_by=admin.id
    )
    db.add(announcement)
    await db.flush()
    recipients = await all_participant_ids(db)
    create_notifications(
        db,
        recipients,
        "announcement",
        f"{data.title}: {data.body}",
        reference_id=announcement.id,
    )
    log_admin_action(
        db, admin.id, "announcement_posted", target_table="announcements", target_id=announcement.id
    )
    await db.commit()
    return announcement


async def get_announcement_or_404(db: AsyncSession, announcement_id: uuid.UUID) -> Announcement:
    announcement = await db.get(Announcement, announcement_id)
    if announcement is None:
        raise ApiError(404, "Announcement not found")
    return announcement


async def list_announcements(db: AsyncSession) -> list[Announcement]:
    return list(
        (
            await db.scalars(select(Announcement).order_by(Announcement.posted_at.desc()))
        ).all()
    )


async def update_announcement(
    db: AsyncSession, admin: Profile, announcement_id: uuid.UUID, data: AnnouncementUpdate
) -> Announcement:
    announcement = await get_announcement_or_404(db, announcement_id)
    if data.title is not None:
        announcement.title = data.title
    if data.body is not None:
        announcement.body = data.body
    if data.image_url is not None:
        announcement.image_url = data.image_url
    announcement.updated_at = datetime.now(timezone.utc)
    log_admin_action(
        db,
        admin.id,
        "announcement_updated",
        target_table="announcements",
        target_id=announcement.id,
    )
    await db.commit()
    return announcement


async def delete_announcement(db: AsyncSession, admin: Profile, announcement_id: uuid.UUID) -> None:
    announcement = await get_announcement_or_404(db, announcement_id)
    log_admin_action(
        db,
        admin.id,
        "announcement_deleted",
        target_table="announcements",
        target_id=announcement.id,
    )
    await db.delete(announcement)
    await db.commit()
