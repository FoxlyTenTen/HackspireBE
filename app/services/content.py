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
    TeamMember,
    TimelineItem,
    Winner,
)
from app.schemas.event import (
    EventInfoResponse,
    FinalistRead,
    FinalistsPut,
    TimelineItemWrite,
    WinnerRead,
    WinnersPut,
)
from app.services.audit import log_admin_action
from app.services.notifications import all_participant_ids, create_notifications
from app.services.storage import get_materials_storage
from app.services.submissions import get_event_settings, invalidate_event_settings_cache


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
        countdown_description=settings_row.countdown_description,
        submission_deadline_at=settings_row.submission_deadline_at,
        round2_submission_deadline_at=settings_row.round2_submission_deadline_at,
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


async def set_countdown(
    db: AsyncSession,
    admin: Profile,
    countdown_at: datetime,
    countdown_description: str | None = None,
):
    settings_row = await get_event_settings(db)
    settings_row.countdown_at = countdown_at
    settings_row.countdown_description = countdown_description
    settings_row.updated_at = datetime.now(timezone.utc)
    log_admin_action(
        db, admin.id, "countdown_updated", target_table="event_settings", target_id=None
    )
    await db.commit()
    invalidate_event_settings_cache()
    return settings_row


async def set_submission_deadline(
    db: AsyncSession, admin: Profile, round: int, deadline_at: datetime
):
    settings_row = await get_event_settings(db)
    if round == 1:
        settings_row.submission_deadline_at = deadline_at
    else:
        settings_row.round2_submission_deadline_at = deadline_at
    settings_row.updated_at = datetime.now(timezone.utc)
    log_admin_action(
        db, admin.id, f"round{round}_submission_deadline_updated", target_table="event_settings"
    )
    await db.commit()
    invalidate_event_settings_cache()
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
            zoom_link=item.zoom_link,
            material_file_url=item.material_file_url,
            material_file_name=item.material_file_name,
            hide_zoom_link=item.hide_zoom_link,
            recording_url=item.recording_url,
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


async def get_timeline_item_or_404(db: AsyncSession, item_id: uuid.UUID) -> TimelineItem:
    item = await db.get(TimelineItem, item_id)
    if item is None:
        raise ApiError(404, "Timeline item not found")
    return item


async def update_timeline_item(
    db: AsyncSession,
    admin: Profile,
    item_id: uuid.UUID,
    *,
    bootcamp_name: str | None = None,
    date_label: str | None = None,
    time_session: str | None = None,
    session_type: str | None = None,
    speaker_name: str | None = None,
    speaker_bio: str | None = None,
    organization: str | None = None,
    session_description: str | None = None,
    speaker_photo_url: str | None = None,
    status: str | None = None,
    remarks: str | None = None,
    order_index: int | None = None,
    zoom_link: str | None = None,
    hide_zoom_link: bool | None = None,
    recording_url: str | None = None,
    material_file: tuple[str, str] | None = None,
    remove_material: bool = False,
) -> TimelineItem:
    item = await get_timeline_item_or_404(db, item_id)
    if bootcamp_name is not None:
        item.bootcamp_name = bootcamp_name
    if date_label is not None:
        item.date_label = date_label
    if time_session is not None:
        item.time_session = time_session
    if session_type is not None:
        item.session_type = session_type
    if speaker_name is not None:
        item.speaker_name = speaker_name
    if speaker_bio is not None:
        item.speaker_bio = speaker_bio
    if organization is not None:
        item.organization = organization
    if session_description is not None:
        item.session_description = session_description
    if speaker_photo_url is not None:
        item.speaker_photo_url = speaker_photo_url
    if status is not None:
        item.status = status
    if remarks is not None:
        item.remarks = remarks
    if order_index is not None:
        item.order_index = order_index
    if zoom_link is not None:
        item.zoom_link = zoom_link
    if hide_zoom_link is not None:
        item.hide_zoom_link = hide_zoom_link
    if recording_url is not None:
        item.recording_url = recording_url.strip() or None

    if material_file is not None:
        old_url = item.material_file_url
        file_name, file_url = material_file
        item.material_file_name = file_name
        item.material_file_url = file_url
        if old_url:
            await get_materials_storage().delete(old_url)
    elif remove_material and item.material_file_url:
        await get_materials_storage().delete(item.material_file_url)
        item.material_file_url = None
        item.material_file_name = None

    log_admin_action(
        db, admin.id, "timeline_item_updated", target_table="timeline_items", target_id=item.id
    )
    await db.commit()
    return item


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
    was_published = bool(
        await db.scalar(select(Finalist.id).where(Finalist.published.is_(True)).limit(1))
    )
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
    if data.published and not was_published:
        recipient_ids = (
            await db.scalars(
                select(TeamMember.participant_id).where(TeamMember.team_id.in_(data.team_ids))
            )
        ).all()
        create_notifications(
            db,
            recipient_ids,
            "round2_open",
            "Your team has been selected as a finalist — round 2 submission is now open!",
        )
        # Also post a public announcement so non-finalist participants see the
        # list was published too — staged on the same session/commit as the
        # finalist replace above, so it's atomic with it.
        await _stage_announcement(
            db,
            admin,
            "Finalists Announced",
            "The Round 2 finalist list has been updated — check the Results page for the full list.",
            image_url=None,
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


async def _stage_announcement(
    db: AsyncSession, admin: Profile, title: str, body: str, image_url: str | None
) -> Announcement:
    """Insert an Announcement row and notify every participant, without
    committing — lets a caller fold this into a larger transaction (e.g.
    put_finalists) or commit it immediately on its own (create_announcement).
    """
    announcement = Announcement(
        title=title, body=body, image_url=image_url, posted_by=admin.id
    )
    db.add(announcement)
    await db.flush()
    recipients = await all_participant_ids(db)
    create_notifications(
        db,
        recipients,
        "announcement",
        f"{title}: {body}",
        reference_id=announcement.id,
    )
    log_admin_action(
        db, admin.id, "announcement_posted", target_table="announcements", target_id=announcement.id
    )
    return announcement


async def create_announcement(
    db: AsyncSession, admin: Profile, title: str, body: str, image_url: str | None
) -> Announcement:
    announcement = await _stage_announcement(db, admin, title, body, image_url)
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
    db: AsyncSession,
    admin: Profile,
    announcement_id: uuid.UUID,
    title: str | None,
    body: str | None,
    image_url: str | None,
) -> Announcement:
    announcement = await get_announcement_or_404(db, announcement_id)
    if title is not None:
        announcement.title = title
    if body is not None:
        announcement.body = body
    if image_url is not None:
        announcement.image_url = image_url
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
