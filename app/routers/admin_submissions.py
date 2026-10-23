import csv
import io
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Profile, Submission
from app.db.session import get_db
from app.dependencies import require_admin
from app.schemas.admin import AdminSubmissionRow, DeadlineUpdate, EventSettingsRead, OpensAtUpdate
from app.schemas.common import error_responses
from app.services import content as content_service
from app.services.audit import log_admin_action

router = APIRouter(prefix="/admin/submissions", tags=["Admin — Submissions"])


@router.get(
    "",
    response_model=list[AdminSubmissionRow],
    summary="Export team submission links for judges",
    description=(
        "Set `format=csv` to download as CSV instead of JSON. Omit `round` to get both "
        "rounds combined; pass `round=1` or `round=2` to filter to one round."
    ),
    responses=error_responses(401, 403),
)
async def list_submissions(
    format: Literal["json", "csv"] = Query(default="json"),
    round: int | None = Query(default=None, ge=1, le=2),
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Submission)
        .options(selectinload(Submission.team))
        .order_by(Submission.round, Submission.submitted_at)
    )
    if round is not None:
        stmt = stmt.where(Submission.round == round)
    submissions = (await db.scalars(stmt)).all()
    rows = [
        AdminSubmissionRow(
            team_id=s.team_id,
            team_reference_id=s.team.reference_id,
            team_name=s.team.name,
            round=s.round,
            github_url=s.github_url,
            infographic_url=s.infographic_url,
            pitch_deck_url=s.pitch_deck_url,
            domain=s.domain,
            submitted_at=s.submitted_at,
            updated_at=s.updated_at,
        )
        for s in submissions
    ]
    if format == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "team_reference_id",
                "team_name",
                "domain",
                "round",
                "infographic_url",  # Canvas link — the mandatory one, right after round
                "github_url",
                "pitch_deck_url",
                "submitted_at",
                "updated_at",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r.team_reference_id,
                    r.team_name,
                    r.domain,
                    r.round,
                    r.infographic_url,
                    r.github_url,
                    r.pitch_deck_url,
                    r.submitted_at,
                    r.updated_at,
                ]
            )
        return Response(
            content=buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=submissions.csv"},
        )
    return rows


@router.patch(
    "/deadline",
    response_model=EventSettingsRead,
    summary="Set or update a round's submission deadline",
    description="After this moment, leaders can no longer create or edit that round's submission.",
    responses=error_responses(401, 403, 422),
)
async def update_deadline(
    body: DeadlineUpdate,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> EventSettingsRead:
    row = await content_service.set_submission_deadline(
        db, admin, body.round, body.submission_deadline_at
    )
    return _to_event_settings_read(row)


@router.patch(
    "/opens-at",
    response_model=EventSettingsRead,
    summary="Set or clear a round's submission opening time",
    description=(
        "Before this moment, approved teams see a locked message instead of the "
        "submission form — see ensure_round_open in services/submissions.py. "
        "Omit/null submission_opens_at to clear it, making the form open "
        "immediately on approval again."
    ),
    responses=error_responses(401, 403, 422),
)
async def update_opens_at(
    body: OpensAtUpdate,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> EventSettingsRead:
    row = await content_service.set_submission_opens_at(
        db, admin, body.round, body.submission_opens_at
    )
    return _to_event_settings_read(row)


def _to_event_settings_read(row) -> EventSettingsRead:
    return EventSettingsRead(
        countdown_at=row.countdown_at,
        countdown_description=row.countdown_description,
        landing_countdown_at=row.landing_countdown_at,
        landing_countdown_label=row.landing_countdown_label,
        submission_deadline_at=row.submission_deadline_at,
        round2_submission_deadline_at=row.round2_submission_deadline_at,
        submission_opens_at=row.submission_opens_at,
        round2_submission_opens_at=row.round2_submission_opens_at,
        team_formation_deadline_at=row.team_formation_deadline_at,
        updated_at=row.updated_at,
    )
