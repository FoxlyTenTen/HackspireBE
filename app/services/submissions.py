import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import EventSettings, Submission, Team

GITHUB_RE = re.compile(r"^https://(www\.)?github\.com/[\w.-]+/[\w.-]+(/.*)?$")
DRIVE_RE = re.compile(r"^https://(drive|docs)\.google\.com/[^\s]+$")


def validate_github_url(url: str) -> None:
    if not GITHUB_RE.match(url):
        raise ApiError(400, "github_url must be a well-formed GitHub link")


def validate_gdrive_url(url: str) -> None:
    if not DRIVE_RE.match(url):
        raise ApiError(400, "gdrive_url must be a well-formed Google Drive link")


def validate_links(github_url: str | None, gdrive_url: str | None) -> None:
    if github_url:
        validate_github_url(github_url)
    if gdrive_url:
        validate_gdrive_url(gdrive_url)


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


def ensure_team_approved(team: Team) -> None:
    if team.approval_status != "approved":
        raise ApiError(403, "Your team must be approved by an admin before submitting")


async def create_submission(
    db: AsyncSession,
    team: Team,
    user_id: uuid.UUID,
    github_url: str | None,
    gdrive_url: str | None,
) -> Submission:
    team_id = team.id
    ensure_team_approved(team)
    validate_links(github_url, gdrive_url)
    await ensure_deadline_open(db)
    existing = await db.scalar(select(Submission).where(Submission.team_id == team_id))
    if existing is not None:
        raise ApiError(409, "This team already has a submission — use PATCH to edit it")
    submission = Submission(
        team_id=team_id,
        github_url=github_url,
        gdrive_url=gdrive_url,
        submitted_by=user_id,
    )
    db.add(submission)
    await db.commit()
    return submission


async def update_submission(
    db: AsyncSession,
    team: Team,
    user_id: uuid.UUID,
    github_url: str | None,
    gdrive_url: str | None,
) -> Submission:
    ensure_team_approved(team)
    validate_links(github_url, gdrive_url)
    await ensure_deadline_open(db)
    submission = await get_submission(db, team.id)
    submission.github_url = github_url
    submission.gdrive_url = gdrive_url
    submission.submitted_by = user_id
    submission.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return submission
