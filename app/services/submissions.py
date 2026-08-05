import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import EventSettings, Submission

GITHUB_RE = re.compile(r"^https://(www\.)?github\.com/[\w.-]+/[\w.-]+(/.*)?$")
DRIVE_RE = re.compile(r"^https://(drive|docs)\.google\.com/[^\s]+$")


def validate_url(url: str) -> None:
    if not (GITHUB_RE.match(url) or DRIVE_RE.match(url)):
        raise ApiError(400, "URL must be a well-formed GitHub or Google Drive link")


async def get_event_settings(db: AsyncSession) -> EventSettings:
    settings_row = await db.get(EventSettings, 1)
    if settings_row is None:
        settings_row = EventSettings(id=1)
        db.add(settings_row)
        await db.flush()
    return settings_row


def _as_utc(dt: datetime) -> datetime:
    # SQLite returns naive datetimes even for timezone-aware columns
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


async def ensure_deadline_open(db: AsyncSession) -> None:
    settings_row = await get_event_settings(db)
    deadline = settings_row.submission_deadline_at
    if deadline is not None and datetime.now(timezone.utc) > _as_utc(deadline):
        raise ApiError(409, "The submission deadline has passed")


async def get_submission(db: AsyncSession, team_id: uuid.UUID) -> Submission:
    submission = await db.scalar(
        select(Submission).where(Submission.team_id == team_id)
    )
    if submission is None:
        raise ApiError(404, "This team has no submission yet")
    return submission


async def create_submission(db: AsyncSession, team_id: uuid.UUID, url: str) -> Submission:
    validate_url(url)
    await ensure_deadline_open(db)
    existing = await db.scalar(select(Submission).where(Submission.team_id == team_id))
    if existing is not None:
        raise ApiError(409, "This team already has a submission — use PATCH to edit it")
    submission = Submission(team_id=team_id, url=url)
    db.add(submission)
    await db.commit()
    return submission


async def update_submission(db: AsyncSession, team_id: uuid.UUID, url: str) -> Submission:
    validate_url(url)
    await ensure_deadline_open(db)
    submission = await get_submission(db, team_id)
    submission.url = url
    submission.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return submission
