import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ApiError
from app.db.models import JoinRequest, Notification, Profile, Team, TeamMember
from app.schemas.join_request import JoinRequestRead
from app.services.notifications import create_notification, create_notifications
from app.services.teams import (
    ensure_unlocked,
    get_membership,
    get_team_or_404,
    member_ids,
    sync_full_status,
)


def _to_read(req: JoinRequest) -> JoinRequestRead:
    return JoinRequestRead(
        id=req.id,
        team_id=req.team_id,
        team_name=req.team.name,
        participant_id=req.participant_id,
        participant_name=req.participant.name,
        status=req.status,
        initiated_by=req.initiated_by,
        created_at=req.created_at,
        responded_at=req.responded_at,
    )


async def create_request(
    db: AsyncSession, user: Profile, team_id: uuid.UUID
) -> JoinRequest:
    if user.role != "participant":
        raise ApiError(403, "Only participants can request to join a team")
    if await get_membership(db, user.id) is not None:
        raise ApiError(409, "You already belong to a team")
    team = await get_team_or_404(db, team_id, for_update=True)
    ensure_unlocked(team)
    if len(await member_ids(db, team.id)) >= team.capacity:
        raise ApiError(409, "Team is already full")
    # A participant may ask several teams at once; only one open ask per team.
    # The team row is locked above, so this check can't race a duplicate.
    existing = await db.scalar(
        select(JoinRequest).where(
            JoinRequest.team_id == team.id,
            JoinRequest.participant_id == user.id,
            JoinRequest.status == "pending",
        )
    )
    if existing is not None:
        raise ApiError(
            409,
            "This team already invited you — respond from your Notifications"
            if existing.initiated_by == "leader"
            else "You already requested to join this team",
        )
    request = JoinRequest(team_id=team.id, participant_id=user.id, initiated_by="participant")
    db.add(request)
    await db.flush()
    create_notification(
        db,
        team.leader_id,
        "join_request",
        f"{user.name} requested to join your team {team.name}",
        reference_id=request.id,
    )
    await db.commit()
    return request


async def create_invite(
    db: AsyncSession, leader: Profile, team_id: uuid.UUID, participant_id: uuid.UUID
) -> JoinRequest:
    """Leader invites an unassigned participant; the participant must accept."""
    team = await get_team_or_404(db, team_id, for_update=True)
    ensure_unlocked(team)
    target = await db.get(Profile, participant_id)
    if target is None or target.role != "participant":
        raise ApiError(404, "Participant not found")
    if await get_membership(db, participant_id) is not None:
        raise ApiError(409, "Participant already belongs to a team")
    existing = await db.scalar(
        select(JoinRequest).where(
            JoinRequest.team_id == team.id,
            JoinRequest.participant_id == participant_id,
            JoinRequest.status == "pending",
        )
    )
    if existing is not None:
        raise ApiError(
            409,
            "This participant already asked to join your team — approve it from Pending join requests"
            if existing.initiated_by == "participant"
            else "You already invited this participant",
        )
    if len(await member_ids(db, team.id)) >= team.capacity:
        raise ApiError(409, "Team is already full")
    request = JoinRequest(team_id=team.id, participant_id=participant_id, initiated_by="leader")
    db.add(request)
    await db.flush()
    request.participant = target
    request.team = team
    create_notification(
        db,
        participant_id,
        "team_invite",
        f"You were invited to join {team.name}",
        reference_id=request.id,
    )
    await db.commit()
    return request


async def list_pending_for_leader(
    db: AsyncSession, user: Profile
) -> list[JoinRequestRead]:
    team = await db.scalar(select(Team).where(Team.leader_id == user.id))
    if team is None:
        raise ApiError(403, "You are not a team leader")
    requests = (
        await db.scalars(
            select(JoinRequest)
            .where(JoinRequest.team_id == team.id, JoinRequest.status == "pending")
            .options(selectinload(JoinRequest.participant), selectinload(JoinRequest.team))
            .order_by(JoinRequest.created_at)
        )
    ).all()
    return [_to_read(r) for r in requests]


async def list_pending_for_participant(
    db: AsyncSession, user: Profile
) -> list[JoinRequestRead]:
    requests = (
        await db.scalars(
            select(JoinRequest)
            .where(
                JoinRequest.participant_id == user.id,
                JoinRequest.initiated_by == "leader",
                JoinRequest.status == "pending",
            )
            .options(selectinload(JoinRequest.participant), selectinload(JoinRequest.team))
            .order_by(JoinRequest.created_at)
        )
    ).all()
    return [_to_read(r) for r in requests]


async def list_sent_by_participant(
    db: AsyncSession, user: Profile
) -> list[JoinRequestRead]:
    requests = (
        await db.scalars(
            select(JoinRequest)
            .where(
                JoinRequest.participant_id == user.id,
                JoinRequest.initiated_by == "participant",
                JoinRequest.status == "pending",
            )
            .options(selectinload(JoinRequest.participant), selectinload(JoinRequest.team))
            .order_by(JoinRequest.created_at)
        )
    ).all()
    return [_to_read(r) for r in requests]


async def respond(
    db: AsyncSession, user: Profile, request_id: uuid.UUID, decision: str
) -> JoinRequestRead:
    request = await db.scalar(
        select(JoinRequest)
        .where(JoinRequest.id == request_id)
        .options(selectinload(JoinRequest.participant))
    )
    if request is None:
        raise ApiError(404, "Join request not found")
    # Lock the team row so approval races (last open slot / concurrent admin
    # approval) serialize on Postgres
    team = await get_team_or_404(db, request.team_id, for_update=True)
    request.team = team
    if request.initiated_by == "leader":
        if request.participant_id != user.id:
            raise ApiError(403, "Only the invited participant can respond to this invite")
    elif team.leader_id != user.id:
        raise ApiError(403, "Only the team leader can respond to this request")
    if request.status != "pending":
        raise ApiError(409, "This request has already been responded to")
    ensure_unlocked(team)

    request.responded_at = datetime.now(timezone.utc)

    if decision == "approve":
        # One query covers both "does this participant already belong to a
        # team" and "who's already on this team" instead of two round trips.
        related_memberships = (
            await db.scalars(
                select(TeamMember).where(
                    or_(
                        TeamMember.participant_id == request.participant_id,
                        TeamMember.team_id == team.id,
                    )
                )
            )
        ).all()
        if any(m.participant_id == request.participant_id for m in related_memberships):
            request.status = "rejected"
            await db.commit()
            raise ApiError(409, "Participant already joined another team")
        existing_ids = [m.participant_id for m in related_memberships if m.team_id == team.id]
        if len(existing_ids) >= team.capacity:
            raise ApiError(409, "Team is already full")
        request.status = "approved"
        db.add(TeamMember(team_id=team.id, participant_id=request.participant_id))
        sync_full_status(team, len(existing_ids) + 1)
        # The participant may have asked (or been invited by) several teams.
        # The first approval wins: close every other pending row and tell
        # those teams' leaders, and clear the matching action-required
        # notifications so no stale Approve/Reject buttons are left behind.
        others = (
            await db.scalars(
                select(JoinRequest)
                .where(
                    JoinRequest.participant_id == request.participant_id,
                    JoinRequest.status == "pending",
                    JoinRequest.id != request.id,
                )
                .options(selectinload(JoinRequest.team))
            )
        ).all()
        closed_at = datetime.now(timezone.utc)
        joiner = request.participant.name
        for other in others:
            other.status = "rejected"
            other.responded_at = closed_at
            if other.initiated_by == "participant":
                note = f"{joiner} joined another team, so their request to join {other.team.name} was closed"
            else:
                note = f"{joiner} joined another team, so your invite to {other.team.name} was closed"
            create_notification(db, other.team.leader_id, "team_update", note, reference_id=other.team_id)
        if others:
            await db.execute(
                update(Notification)
                .where(
                    Notification.reference_id.in_([o.id for o in others]),
                    Notification.type.in_(("join_request", "team_invite")),
                )
                .values(read=True)
            )
        if request.initiated_by == "leader":
            create_notification(
                db,
                team.leader_id,
                "invite_response",
                f"{request.participant.name} accepted your invite to {team.name}",
                reference_id=request.id,
            )
        else:
            create_notification(
                db,
                request.participant_id,
                "join_response",
                f"Your request to join {team.name} was approved",
                reference_id=request.id,
            )
        create_notifications(
            db,
            existing_ids,
            "team_update",
            f"{request.participant.name} joined your team {team.name}",
            reference_id=team.id,
        )
    else:
        request.status = "rejected"
        if request.initiated_by == "leader":
            create_notification(
                db,
                team.leader_id,
                "invite_response",
                f"{request.participant.name} declined your invite to {team.name}",
                reference_id=request.id,
            )
        else:
            create_notification(
                db,
                request.participant_id,
                "join_response",
                f"Your request to join {team.name} was rejected",
                reference_id=request.id,
            )

    await db.commit()
    return _to_read(request)


async def cancel(db: AsyncSession, user: Profile, request_id: uuid.UUID) -> None:
    """Undo a pending request/invite. Only whoever created it can cancel it:
    the participant for their own request, the team's leader for an invite."""
    request = await db.get(JoinRequest, request_id)
    if request is None:
        raise ApiError(404, "Join request not found")
    if request.initiated_by == "participant":
        if request.participant_id != user.id:
            raise ApiError(403, "Only the participant who sent this request can cancel it")
    else:
        team = await db.get(Team, request.team_id)
        if team is None or team.leader_id != user.id:
            raise ApiError(403, "Only the team leader who sent this invite can cancel it")
    if request.status != "pending":
        raise ApiError(409, "This request has already been responded to")
    # Remove the other side's now-meaningless notification too, so no
    # Approve/Reject buttons are left pointing at a cancelled request.
    await db.execute(
        delete(Notification).where(
            Notification.reference_id == request.id,
            Notification.type.in_(("join_request", "team_invite")),
        )
    )
    await db.delete(request)
    await db.commit()
