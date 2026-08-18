import re
import uuid
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import EventSettings, Finalist, Submission, Team

GITHUB_RE = re.compile(r"^https://(www\.)?github\.com/[\w.-]+/[\w.-]+(/.*)?$")
URL_RE = re.compile(r"^https://\S+$")

Round = Literal[1, 2]


def validate_github_url(url: str) -> None:
    if not GITHUB_RE.match(url):
        raise ApiError(400, "github_url must be a well-formed GitHub link")


def validate_infographic_url(url: str) -> None:
    if not URL_RE.match(url):
        raise ApiError(400, "infographic_url must be a well-formed https link")


def validate_pitch_deck_url(url: str) -> None:
    if not URL_RE.match(url):
        raise ApiError(400, "pitch_deck_url must be a well-formed https link")


def validate_links(
    github_url: str | None,
    infographic_url: str | None,
    pitch_deck_url: str | None,
) -> None:
    if github_url:
        validate_github_url(github_url)
    if infographic_url:
        validate_infographic_url(infographic_url)
    if pitch_deck_url:
        validate_pitch_deck_url(pitch_deck_url)


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


async def ensure_deadline_open(db: AsyncSession, round: Round) -> None:
    settings_row = await get_event_settings(db)
    deadline = (
        settings_row.submission_deadline_at
        if round == 1
        else settings_row.round2_submission_deadline_at
    )
    if deadline is not None and datetime.now(timezone.utc) > _as_utc(deadline):
        raise ApiError(409, f"The round {round} submission deadline has passed")


async def get_submission(db: AsyncSession, team_id: uuid.UUID, round: Round) -> Submission:
    submission = await db.scalar(
        select(Submission).where(Submission.team_id == team_id, Submission.round == round)
    )
    if submission is None:
        raise ApiError(404, f"This team has no round {round} submission yet")
    return submission


def ensure_team_approved(team: Team) -> None:
    if team.approval_status != "approved":
        raise ApiError(403, "Your team must be approved by an admin before submitting")


async def ensure_finalist_for_round2(db: AsyncSession, team_id: uuid.UUID) -> None:
    is_finalist = await db.scalar(
        select(Finalist.id).where(Finalist.team_id == team_id, Finalist.published.is_(True))
    )
    if is_finalist is None:
        raise ApiError(403, "Only published finalist teams can submit round 2 links")


async def create_submission(
    db: AsyncSession,
    team: Team,
    round: Round,
    user_id: uuid.UUID,
    github_url: str | None,
    infographic_url: str | None,
    pitch_deck_url: str | None,
) -> Submission:
    team_id = team.id
    ensure_team_approved(team)
    if round == 2:
        await ensure_finalist_for_round2(db, team_id)
    validate_links(github_url, infographic_url, pitch_deck_url)
    await ensure_deadline_open(db, round)
    existing = await db.scalar(
        select(Submission).where(Submission.team_id == team_id, Submission.round == round)
    )
    if existing is not None:
        raise ApiError(409, "This team already has a submission — use PATCH to edit it")
    submission = Submission(
        team_id=team_id,
        round=round,
        github_url=github_url,
        infographic_url=infographic_url,
        pitch_deck_url=pitch_deck_url,
        submitted_by=user_id,
    )
    db.add(submission)
    await db.commit()
    return submission


async def update_submission(
    db: AsyncSession,
    team: Team,
    round: Round,
    user_id: uuid.UUID,
    github_url: str | None,
    infographic_url: str | None,
    pitch_deck_url: str | None,
) -> Submission:
    ensure_team_approved(team)
    if round == 2:
        await ensure_finalist_for_round2(db, team.id)
    validate_links(github_url, infographic_url, pitch_deck_url)
    await ensure_deadline_open(db, round)
    submission = await get_submission(db, team.id, round)
    submission.github_url = github_url
    submission.infographic_url = infographic_url
    submission.pitch_deck_url = pitch_deck_url
    submission.submitted_by = user_id
    submission.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return submission
