from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Profile, Team
from app.db.session import get_db
from app.dependencies import get_current_user, require_team_member
from app.schemas.common import error_responses
from app.schemas.submission import SubmissionRead, SubmissionWrite
from app.services import submissions as submission_service

router = APIRouter(prefix="/teams/{team_id}/submission/{round}", tags=["Submission"])

RoundPath = Annotated[int, Path(ge=1, le=2)]


@router.get(
    "",
    response_model=SubmissionRead,
    summary="View the team's submission link for a round",
    description="Any team member can view, create, or edit it.",
    responses=error_responses(401, 403, 404),
)
async def get_submission(
    round: RoundPath,
    team: Team = Depends(require_team_member),
    db: AsyncSession = Depends(get_db),
) -> SubmissionRead:
    return await submission_service.get_submission(db, team.id, round)


@router.post(
    "",
    response_model=SubmissionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit the project links for a round (any team member)",
    description=(
        "github_url, infographic_url, and/or pitch_deck_url — at least one is required. "
        "Requires the team to be admin-approved. Round 2 additionally requires the team "
        "to be a published finalist. Blocked once that round's submission deadline has passed."
    ),
    responses=error_responses(400, 401, 403, 404, 409, 422),
)
async def create_submission(
    round: RoundPath,
    body: SubmissionWrite,
    team: Team = Depends(require_team_member),
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubmissionRead:
    return await submission_service.create_submission(
        db, team, round, user.id, body.github_url, body.infographic_url, body.pitch_deck_url
    )


@router.patch(
    "",
    response_model=SubmissionRead,
    summary="Edit the submission links for a round (any team member)",
    description="Same validation as submitting; blocked after that round's deadline.",
    responses=error_responses(400, 401, 403, 404, 409, 422),
)
async def update_submission(
    round: RoundPath,
    body: SubmissionWrite,
    team: Team = Depends(require_team_member),
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubmissionRead:
    return await submission_service.update_submission(
        db, team, round, user.id, body.github_url, body.infographic_url, body.pitch_deck_url
    )
