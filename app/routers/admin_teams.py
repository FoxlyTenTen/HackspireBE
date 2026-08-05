import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ApiError
from app.db.models import Profile, Submission, Team, TeamMember
from app.db.session import get_db
from app.dependencies import require_admin
from app.schemas.admin import AdminRejectRequest, AdminTeamRead, AdminTeamUpdate
from app.schemas.common import error_responses
from app.services import teams as team_service

router = APIRouter(prefix="/admin/teams", tags=["Admin — Teams"])


def _to_admin_read(team: Team, has_submission: bool) -> AdminTeamRead:
    return AdminTeamRead(
        id=team.id,
        name=team.name,
        leader_id=team.leader_id,
        leader_name=team.leader.name,
        member_count=len(team.members),
        capacity=team.capacity,
        status=team.status,
        approval_status=team.approval_status,
        admin_note=team.admin_note,
        locked=team.locked,
        has_submission=has_submission,
        created_at=team.created_at,
    )


async def _admin_read(db: AsyncSession, team_id: uuid.UUID) -> AdminTeamRead:
    team = await db.scalar(
        select(Team)
        .where(Team.id == team_id)
        .options(
            selectinload(Team.members),
            selectinload(Team.leader),
            selectinload(Team.submission),
        )
    )
    return _to_admin_read(team, team.submission is not None)


@router.get(
    "",
    response_model=list[AdminTeamRead],
    summary="All teams, any size or completeness",
    responses=error_responses(401, 403),
)
async def list_all_teams(
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminTeamRead]:
    teams = (
        await db.scalars(
            select(Team)
            .options(
                selectinload(Team.members),
                selectinload(Team.leader),
                selectinload(Team.submission),
            )
            .order_by(Team.created_at)
        )
    ).all()
    return [_to_admin_read(t, t.submission is not None) for t in teams]


@router.post(
    "/{team_id}/approve",
    response_model=AdminTeamRead,
    summary="Approve a team and lock it",
    description=(
        "Sets `approval_status=approved` and `locked=true`, blocking all further "
        "member/team writes until an admin explicitly reverts the approval "
        "(PATCH with `locked=false`)."
    ),
    responses=error_responses(401, 403, 404, 409),
)
async def approve_team(
    team_id: uuid.UUID,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminTeamRead:
    # Row lock so approval and a concurrent last-slot join serialize
    team = await team_service.get_team_or_404(db, team_id, for_update=True)
    if team.approval_status == "approved":
        raise ApiError(409, "Team is already approved")
    team.approval_status = "approved"
    team.locked = True
    team.status = "closed"
    await db.commit()
    return await _admin_read(db, team_id)


@router.post(
    "/{team_id}/reject",
    response_model=AdminTeamRead,
    summary="Reject a team (stays open and editable)",
    description="Optionally stores an admin note explaining the rejection.",
    responses=error_responses(401, 403, 404, 422),
)
async def reject_team(
    team_id: uuid.UUID,
    body: AdminRejectRequest,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminTeamRead:
    team = await team_service.get_team_or_404(db, team_id, for_update=True)
    team.approval_status = "rejected"
    team.locked = False
    if body.note is not None:
        team.admin_note = body.note
    await db.commit()
    return await _admin_read(db, team_id)


@router.patch(
    "/{team_id}",
    response_model=AdminTeamRead,
    summary="Manually edit a team, including reassigning leadership",
    description=(
        "Admin override: edit name/capacity/status, reassign `leader_id` to any "
        "current member, or set `locked`. Setting `locked=false` on an approved "
        "team reverts the approval back to `pending`."
    ),
    responses=error_responses(400, 401, 403, 404, 409, 422),
)
async def admin_update_team(
    team_id: uuid.UUID,
    body: AdminTeamUpdate,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminTeamRead:
    team = await team_service.get_team_or_404(db, team_id, for_update=True)
    count = await team_service.member_count(db, team.id)
    if body.name is not None and body.name != team.name:
        existing = await db.scalar(select(Team).where(Team.name == body.name))
        if existing is not None:
            raise ApiError(409, "A team with this name already exists")
        team.name = body.name
    if body.capacity is not None:
        if body.capacity < count:
            raise ApiError(400, "Capacity cannot be lower than the current member count")
        team.capacity = body.capacity
    if body.leader_id is not None and body.leader_id != team.leader_id:
        membership = await db.scalar(
            select(TeamMember).where(
                TeamMember.team_id == team.id,
                TeamMember.participant_id == body.leader_id,
            )
        )
        if membership is None:
            raise ApiError(400, "New leader must be a current member of the team")
        team.leader_id = body.leader_id
    if body.status is not None:
        team.status = body.status
    if body.locked is not None:
        if not body.locked and team.approval_status == "approved":
            team.approval_status = "pending"  # explicit revert of the approval
        team.locked = body.locked
    await db.commit()
    return await _admin_read(db, team_id)


@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Force-delete a broken or abandoned team",
    description="Works regardless of lock state; members become unassigned again.",
    responses=error_responses(401, 403, 404),
)
async def force_delete_team(
    team_id: uuid.UUID,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    team = await team_service.get_team_or_404(db, team_id)
    await team_service._delete_team_row(db, team)
    await db.commit()
