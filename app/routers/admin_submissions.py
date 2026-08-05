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
from app.schemas.admin import AdminSubmissionRow, DeadlineUpdate, EventSettingsRead
from app.schemas.common import error_responses
from app.services import content as content_service

router = APIRouter(prefix="/admin/submissions", tags=["Admin — Submissions"])


@router.get(
    "",
    response_model=list[AdminSubmissionRow],
    summary="Export all team submission links for judges",
    description="Set `format=csv` to download as CSV instead of JSON.",
    responses=error_responses(401, 403),
)
async def list_submissions(
    format: Literal["json", "csv"] = Query(default="json"),
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    submissions = (
        await db.scalars(
            select(Submission)
            .options(selectinload(Submission.team))
            .order_by(Submission.submitted_at)
        )
    ).all()
    rows = [
        AdminSubmissionRow(
            team_id=s.team_id,
            team_name=s.team.name,
            url=s.url,
            submitted_at=s.submitted_at,
            updated_at=s.updated_at,
        )
        for s in submissions
    ]
    if format == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["team_id", "team_name", "url", "submitted_at", "updated_at"])
        for r in rows:
            writer.writerow([r.team_id, r.team_name, r.url, r.submitted_at, r.updated_at])
        return Response(
            content=buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=submissions.csv"},
        )
    return rows


@router.patch(
    "/deadline",
    response_model=EventSettingsRead,
    summary="Set or update the submission deadline",
    description="After this moment, leaders can no longer create or edit submissions.",
    responses=error_responses(401, 403, 422),
)
async def update_deadline(
    body: DeadlineUpdate,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> EventSettingsRead:
    row = await content_service.set_submission_deadline(db, body.submission_deadline_at)
    return EventSettingsRead(
        countdown_at=row.countdown_at,
        submission_deadline_at=row.submission_deadline_at,
        updated_at=row.updated_at,
    )
