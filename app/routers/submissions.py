from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Team
from app.db.session import get_db
from app.dependencies import require_team_leader, require_team_member
from app.schemas.common import error_responses
from app.schemas.submission import SubmissionRead, SubmissionWrite
from app.services import submissions as submission_service

router = APIRouter(prefix="/teams/{team_id}/submission", tags=["Submission"])


@router.get(
    "",
    response_model=SubmissionRead,
    summary="View the team's submission link",
    description="Any team member can view; only the leader can create or edit it.",
    responses=error_responses(401, 403, 404),
)
async def get_submission(
    team: Team = Depends(require_team_member),
    db: AsyncSession = Depends(get_db),
) -> SubmissionRead:
    return await submission_service.get_submission(db, team.id)


@router.post(
    "",
    response_model=SubmissionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit the project link (leader only)",
    description=(
        "The URL must be a well-formed GitHub or Google Drive link. Blocked once "
        "the submission deadline has passed."
    ),
    responses=error_responses(400, 401, 403, 404, 409, 422),
)
async def create_submission(
    body: SubmissionWrite,
    team: Team = Depends(require_team_leader),
    db: AsyncSession = Depends(get_db),
) -> SubmissionRead:
    return await submission_service.create_submission(db, team.id, body.url)


@router.patch(
    "",
    response_model=SubmissionRead,
    summary="Edit the submission link (leader only)",
    description="Same validation as submitting; blocked after the deadline.",
    responses=error_responses(400, 401, 403, 404, 409, 422),
)
async def update_submission(
    body: SubmissionWrite,
    team: Team = Depends(require_team_leader),
    db: AsyncSession = Depends(get_db),
) -> SubmissionRead:
    return await submission_service.update_submission(db, team.id, body.url)
