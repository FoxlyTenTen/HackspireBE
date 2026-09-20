import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Profile, Team
from app.db.session import get_db
from app.dependencies import get_current_user, require_team_leader
from app.schemas.common import error_responses
from app.schemas.join_request import InviteCreate, JoinRequestRead
from app.schemas.team import (
    TeamCreate,
    TeamListItem,
    TeamRead,
    TeamUpdate,
)
from app.services import join_requests as join_request_service
from app.services import teams as team_service

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get(
    "",
    response_model=list[TeamListItem],
    summary="Searchable team list",
    description="Every team with its name, member count, capacity and status.",
    responses=error_responses(401, 403),
)
async def list_teams(
    search: str | None = Query(default=None, description="Filter by team name"),
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TeamListItem]:
    return await team_service.list_teams(db, search)


@router.post(
    "",
    response_model=TeamRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a team",
    description=(
        "Any participant who is not yet in a team can create one; the creator "
        "automatically becomes the team leader and its first member."
    ),
    responses=error_responses(401, 403, 409, 422),
)
async def create_team(
    body: TeamCreate,
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeamRead:
    team = await team_service.create_team(db, user, body)
    return await team_service.team_detail(db, team.id)


@router.get(
    "/{team_id}",
    response_model=TeamRead,
    summary="Team detail",
    description="Full team info including its member list.",
    responses=error_responses(401, 403, 404),
)
async def get_team(
    team_id: uuid.UUID,
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeamRead:
    return await team_service.team_detail(db, team_id)


@router.patch(
    "/{team_id}",
    response_model=TeamRead,
    summary="Edit team (leader only)",
    description=(
        "Update name, capacity (max 5, never below the current member count) or "
        "status. Status flips to `full` automatically when the team fills up. "
        "Blocked once the team is locked by admin approval."
    ),
    responses=error_responses(400, 401, 403, 404, 409, 422),
)
async def update_team(
    body: TeamUpdate,
    team: Team = Depends(require_team_leader),
    db: AsyncSession = Depends(get_db),
) -> TeamRead:
    await team_service.update_team(db, team, body)
    return await team_service.team_detail(db, team.id)


@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete team (leader only)",
    description=(
        "Deleting the team is how a leader leaves — leadership never transfers. "
        "Members, join requests and the submission are removed with it."
    ),
    responses=error_responses(401, 403, 404, 409),
)
async def delete_team(
    team: Team = Depends(require_team_leader),
    db: AsyncSession = Depends(get_db),
) -> None:
    await team_service.delete_team(db, team)


@router.post(
    "/{team_id}/invite",
    response_model=JoinRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Invite an unassigned participant (leader only)",
    description=(
        "Creates a pending invite — the participant must accept it from their "
        "Notifications page before they become a member. Team membership does "
        "not change until then."
    ),
    responses=error_responses(401, 403, 404, 409, 422),
)
async def invite_member(
    body: InviteCreate,
    team: Team = Depends(require_team_leader),
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JoinRequestRead:
    request = await join_request_service.create_invite(db, user, team.id, body.participant_id)
    return JoinRequestRead(
        id=request.id,
        team_id=team.id,
        team_name=team.name,
        participant_id=request.participant_id,
        participant_name=request.participant.name,
        status=request.status,
        initiated_by=request.initiated_by,
        created_at=request.created_at,
        responded_at=request.responded_at,
    )


@router.delete(
    "/{team_id}/members/{participant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member (leader only)",
    description="The leader cannot remove themselves — delete the team instead.",
    responses=error_responses(400, 401, 403, 404, 409),
)
async def remove_member(
    participant_id: uuid.UUID,
    team: Team = Depends(require_team_leader),
    db: AsyncSession = Depends(get_db),
) -> None:
    await team_service.remove_member(db, team, participant_id)


@router.post(
    "/{team_id}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Leave the team (non-leader member)",
    description=(
        "A non-leader member leaves individually — the slot reopens and the team "
        "is otherwise unaffected. Leaders must delete the team instead."
    ),
    responses=error_responses(400, 401, 403, 404, 409),
)
async def leave_team(
    team_id: uuid.UUID,
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    team = await team_service.get_team_or_404(db, team_id)
    await team_service.leave_team(db, team, user)


@router.post(
    "/{team_id}/join-requests",
    response_model=JoinRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Request to join a team",
    description=(
        "For participants without a team. Only one pending request is allowed at a "
        "time. The team leader is notified and must approve or reject it."
    ),
    responses=error_responses(401, 403, 404, 409),
)
async def request_to_join(
    team_id: uuid.UUID,
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JoinRequestRead:
    request = await join_request_service.create_request(db, user, team_id)
    team = await team_service.get_team_or_404(db, team_id)
    return JoinRequestRead(
        id=request.id,
        team_id=team.id,
        team_name=team.name,
        participant_id=user.id,
        participant_name=user.name,
        status=request.status,
        initiated_by=request.initiated_by,
        created_at=request.created_at,
        responded_at=request.responded_at,
    )
