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
    EventInfoResponse,
    FinalistRead,
    FinalistsPut,
    TimelineItemWrite,
    WinnerRead,
    WinnersPut,
)
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


async def set_countdown(db: AsyncSession, countdown_at: datetime):
    settings_row = await get_event_settings(db)
    settings_row.countdown_at = countdown_at
    settings_row.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return settings_row


async def set_submission_deadline(db: AsyncSession, deadline_at: datetime):
    settings_row = await get_event_settings(db)
    settings_row.submission_deadline_at = deadline_at
    settings_row.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return settings_row


async def replace_timeline(
    db: AsyncSession, items: list[TimelineItemWrite]
) -> list[TimelineItem]:
    await db.execute(sa_delete(TimelineItem))
    new_items = [
        TimelineItem(
            time_label=item.time_label,
            title=item.title,
            description=item.description,
            order_index=item.order_index,
        )
        for item in items
    ]
    db.add_all(new_items)
    await db.commit()
    return sorted(new_items, key=lambda i: i.order_index)


async def _ensure_teams_exist(db: AsyncSession, team_ids: list[uuid.UUID]) -> None:
    existing = set(
        (await db.scalars(select(Team.id).where(Team.id.in_(team_ids)))).all()
    )
    missing = [str(tid) for tid in team_ids if tid not in existing]
    if missing:
        raise ApiError(404, f"Team(s) not found: {', '.join(missing)}")


async def put_finalists(db: AsyncSession, data: FinalistsPut) -> list[FinalistRead]:
    await _ensure_teams_exist(db, data.team_ids)
    await db.execute(sa_delete(Finalist))
    published_at = datetime.now(timezone.utc) if data.published else None
    db.add_all(
        Finalist(team_id=tid, published=data.published, published_at=published_at)
        for tid in data.team_ids
    )
    await db.commit()
    return await list_finalists(db, published_only=False)


async def put_winners(db: AsyncSession, data: WinnersPut) -> list[WinnerRead]:
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
    await db.commit()
    return await list_winners(db, published_only=False)


async def create_announcement(
    db: AsyncSession, admin: Profile, data: AnnouncementCreate
) -> Announcement:
    announcement = Announcement(title=data.title, body=data.body, posted_by=admin.id)
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
    await db.commit()
    return announcement
