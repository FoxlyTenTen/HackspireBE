import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ApiError
from app.db.models import Finalist, JoinRequest, Profile, Team, TeamMember, Winner
from app.schemas.team import (
    TeamCreate,
    TeamListItem,
    TeamMemberRead,
    TeamRead,
    TeamUpdate,
)
from app.services.notifications import create_notification, create_notifications

MAX_CAPACITY = 5


async def get_membership(db: AsyncSession, participant_id: uuid.UUID) -> TeamMember | None:
    return await db.scalar(
        select(TeamMember).where(TeamMember.participant_id == participant_id)
    )


async def get_team_or_404(
    db: AsyncSession, team_id: uuid.UUID, *, for_update: bool = False
) -> Team:
    stmt = select(Team).where(Team.id == team_id)
    if for_update:
        # Row-level lock on Postgres; no-op on SQLite (writes serialize anyway)
        stmt = stmt.with_for_update()
    team = await db.scalar(stmt)
    if team is None:
        raise ApiError(404, "Team not found")
    return team


async def member_count(db: AsyncSession, team_id: uuid.UUID) -> int:
    return (
        await db.scalar(
            select(func.count()).select_from(TeamMember).where(TeamMember.team_id == team_id)
        )
    ) or 0


def sync_full_status(team: Team, count: int) -> None:
    """Auto-flip status to 'full' at capacity; reopen when a slot frees up."""
    if count >= team.capacity:
        team.status = "full"
    elif team.status == "full":
        team.status = "open"


def ensure_unlocked(team: Team) -> None:
    if team.locked:
        raise ApiError(409, "Team is locked by admin approval and cannot be modified")


async def member_ids(db: AsyncSession, team_id: uuid.UUID) -> list[uuid.UUID]:
    result = await db.scalars(
        select(TeamMember.participant_id).where(TeamMember.team_id == team_id)
    )
    return list(result)


async def list_teams(db: AsyncSession, search: str | None) -> list[TeamListItem]:
    stmt = select(Team).options(selectinload(Team.members)).order_by(Team.created_at)
    if search:
        stmt = stmt.where(Team.name.ilike(f"%{search}%"))
    teams = (await db.scalars(stmt)).all()
    return [
        TeamListItem(
            id=t.id,
            name=t.name,
            reference_id=t.reference_id,
            member_count=len(t.members),
            capacity=t.capacity,
            status=t.status,
            project_title=t.project_title,
            preferred_roles=t.preferred_roles or [],
            remarks=t.remarks,
        )
        for t in teams
    ]


async def team_detail(db: AsyncSession, team_id: uuid.UUID) -> TeamRead:
    team = await db.scalar(
        select(Team)
        .where(Team.id == team_id)
        .options(selectinload(Team.members).selectinload(TeamMember.participant))
    )
    if team is None:
        raise ApiError(404, "Team not found")
    members = [
        TeamMemberRead(
            participant_id=m.participant_id,
            name=m.participant.name,
            student_staff_id=m.participant.student_staff_id,
            is_leader=m.participant_id == team.leader_id,
            joined_at=m.joined_at,
        )
        for m in team.members
    ]
    return TeamRead(
        id=team.id,
        name=team.name,
        reference_id=team.reference_id,
        leader_id=team.leader_id,
        capacity=team.capacity,
        status=team.status,
        approval_status=team.approval_status,
        admin_note=team.admin_note,
        locked=team.locked,
        project_title=team.project_title,
        preferred_roles=team.preferred_roles or [],
        remarks=team.remarks,
        created_at=team.created_at,
        member_count=len(members),
        members=members,
    )


async def create_team(db: AsyncSession, user: Profile, data: TeamCreate) -> Team:
    if await get_membership(db, user.id) is not None:
        raise ApiError(409, "You already belong to a team")
    existing = await db.scalar(select(Team).where(Team.name == data.name))
    if existing is not None:
        raise ApiError(409, "A team with this name already exists")
    team = Team(name=data.name, leader_id=user.id)
    db.add(team)
    await db.flush()
    db.add(TeamMember(team_id=team.id, participant_id=user.id))
    await db.commit()
    # reference_id is set by a DB trigger on INSERT — reload to pick it up
    await db.refresh(team)
    return team


async def update_team(db: AsyncSession, team: Team, data: TeamUpdate) -> Team:
    # Project title / roles / remarks are descriptive, so the leader can keep
    # editing them after approval locks the team; name/capacity/status can't.
    if data.project_title is not None:
        team.project_title = data.project_title.strip() or None
    if data.preferred_roles is not None:
        team.preferred_roles = list(dict.fromkeys(data.preferred_roles))
    if data.remarks is not None:
        team.remarks = data.remarks.strip() or None
    if data.name is None and data.capacity is None and data.status is None:
        await db.commit()
        return team

    ensure_unlocked(team)
    count = await member_count(db, team.id)
    if data.name is not None and data.name != team.name:
        existing = await db.scalar(select(Team).where(Team.name == data.name))
        if existing is not None:
            raise ApiError(409, "A team with this name already exists")
        team.name = data.name
    if data.capacity is not None:
        if data.capacity > MAX_CAPACITY:
            raise ApiError(400, f"Capacity cannot exceed {MAX_CAPACITY}")
        if data.capacity < count:
            raise ApiError(400, "Capacity cannot be lower than the current member count")
        team.capacity = data.capacity
    if data.status is not None:
        team.status = data.status
    sync_full_status(team, count)
    await db.commit()
    return team


async def delete_team(db: AsyncSession, team: Team) -> None:
    """Leader's way of leaving — leadership never transfers."""
    ensure_unlocked(team)
    await _delete_team_row(db, team)
    await db.commit()


async def _delete_team_row(db: AsyncSession, team: Team) -> None:
    # Clear finalist/winner rows referencing this team (FKs without CASCADE);
    # members / join requests / submission cascade via ORM relationships.
    for finalist in await db.scalars(select(Finalist).where(Finalist.team_id == team.id)):
        await db.delete(finalist)
    for winner in await db.scalars(select(Winner).where(Winner.team_id == team.id)):
        await db.delete(winner)
    await db.delete(team)


async def remove_member(
    db: AsyncSession, team: Team, participant_id: uuid.UUID
) -> None:
    ensure_unlocked(team)
    if participant_id == team.leader_id:
        raise ApiError(400, "The leader cannot be removed — delete the team instead")
    membership = await db.scalar(
        select(TeamMember).where(
            TeamMember.team_id == team.id, TeamMember.participant_id == participant_id
        )
    )
    if membership is None:
        raise ApiError(404, "Participant is not a member of this team")
    await db.delete(membership)
    count = await member_count(db, team.id) - 1
    sync_full_status(team, count)
    create_notification(
        db,
        participant_id,
        "team_update",
        f"You were removed from team {team.name}",
        reference_id=team.id,
    )
    await db.commit()


async def leave_team(db: AsyncSession, team: Team, user: Profile) -> None:
    """Non-leader member leaves individually — slot reopens, team unaffected."""
    ensure_unlocked(team)
    if team.leader_id == user.id:
        raise ApiError(400, "The leader cannot leave — delete the team instead")
    # Single query for both "is this user a member" and "who else is on the
    # team" instead of a membership lookup followed by a separate member_ids call.
    members = (
        await db.scalars(select(TeamMember).where(TeamMember.team_id == team.id))
    ).all()
    membership = next((m for m in members if m.participant_id == user.id), None)
    if membership is None:
        raise ApiError(403, "You are not a member of this team")
    await db.delete(membership)
    remaining = [m.participant_id for m in members if m.participant_id != user.id]
    sync_full_status(team, len(remaining))
    create_notifications(
        db,
        remaining,
        "team_update",
        f"{user.name} left team {team.name}",
        reference_id=team.id,
    )
    await db.commit()
