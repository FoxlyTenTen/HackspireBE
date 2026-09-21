from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import JoinRequest, Profile, Team, TeamMember
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.common import error_responses
from app.schemas.profile import ParticipantListItem

router = APIRouter(tags=["Participants"])


@router.get(
    "/participants",
    response_model=list[ParticipantListItem],
    summary="Searchable participant list",
    description=(
        "Participants who have activated their account (`invite_status = active`), "
        "with their team status (`no_team` or `in_team`) so leaders can find people "
        "to recruit. Accounts still sitting on an unopened invite are excluded — "
        "recruiting someone who can't log in yet isn't useful. Filter with the "
        "`search` query parameter (matches name, username, or student/staff ID). "
        "`has_pending_invite` is true while the viewer's own team has an unanswered invite out to that participant."
    ),
    responses=error_responses(401, 403),
)
async def list_participants(
    search: str | None = Query(default=None, description="Filter by name or ID"),
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ParticipantListItem]:
    stmt = (
        select(Profile)
        .where(Profile.role == "participant", Profile.invite_status == "active")
        .options(
            selectinload(Profile.membership).selectinload(TeamMember.team)
        )
        .order_by(Profile.name)
    )
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            Profile.name.ilike(pattern)
            | Profile.username.ilike(pattern)
            | Profile.student_staff_id.ilike(pattern)
        )
    profiles = (await db.scalars(stmt)).all()
    # "Invited" is relative to the viewer: only their own team's open invites.
    my_team_id = await db.scalar(select(Team.id).where(Team.leader_id == user.id))
    invited_ids: set = set()
    if my_team_id is not None:
        invited_ids = set(
            await db.scalars(
                select(JoinRequest.participant_id).where(
                    JoinRequest.team_id == my_team_id,
                    JoinRequest.status == "pending",
                    JoinRequest.initiated_by == "leader",
                )
            )
        )
    return [
        ParticipantListItem(
            id=p.id,
            name=p.name,
            username=p.username,
            reference_id=p.reference_id,
            technical_skills=p.technical_skills,
            preferred_role=p.preferred_role,
            status="in_team" if p.membership else "no_team",
            team_name=p.membership.team.name if p.membership else None,
            has_pending_invite=p.id in invited_ids,
        )
        for p in profiles
    ]
