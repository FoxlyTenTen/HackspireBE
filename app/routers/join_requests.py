import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Profile
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.common import error_responses
from app.schemas.join_request import JoinRequestRead, JoinRequestRespond
from app.services import join_requests as join_request_service

router = APIRouter(prefix="/join-requests", tags=["Join Requests"])


@router.get(
    "",
    response_model=list[JoinRequestRead],
    summary="Pending join requests for the leader's team",
    description="Only accessible to team leaders; lists pending requests for their own team.",
    responses=error_responses(401, 403),
)
async def list_pending(
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[JoinRequestRead]:
    return await join_request_service.list_pending_for_leader(db, user)


@router.get(
    "/invitations",
    response_model=list[JoinRequestRead],
    summary="Pending invitations for the current participant",
    description="Leader-initiated invites awaiting this participant's decision.",
    responses=error_responses(401, 403),
)
async def list_invitations(
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[JoinRequestRead]:
    return await join_request_service.list_pending_for_participant(db, user)


@router.get(
    "/sent",
    response_model=list[JoinRequestRead],
    summary="Join requests the current participant sent that are still pending",
    description="Lets Team Formation show which teams were already asked, so a request is only sent once per team.",
    responses=error_responses(401, 403),
)
async def list_sent(
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[JoinRequestRead]:
    return await join_request_service.list_sent_by_participant(db, user)


@router.post(
    "/{request_id}/respond",
    response_model=JoinRequestRead,
    summary="Approve or reject a join request (leader only)",
    description=(
        "Approving re-checks capacity under a row lock, adds the requester as a "
        "member, and notifies both the requester (`join_response`) and the "
        "existing members (`team_update`). Approving also closes the participant's "
        "other pending requests/invites and notifies those teams' leaders. "
        "Rejecting only notifies the requester."
    ),
    responses=error_responses(401, 403, 404, 409, 422),
)
async def respond(
    request_id: uuid.UUID,
    body: JoinRequestRespond,
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JoinRequestRead:
    return await join_request_service.respond(db, user, request_id, body.decision)


@router.delete(
    "/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel a pending request or invite you sent",
    description=(
        "A participant can cancel their own pending join request; a team leader can "
        "cancel a pending invite their team sent. The other side's notification is "
        "removed. Already-answered requests can't be cancelled."
    ),
    responses=error_responses(401, 403, 404, 409),
)
async def cancel(
    request_id: uuid.UUID,
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await join_request_service.cancel(db, user, request_id)
