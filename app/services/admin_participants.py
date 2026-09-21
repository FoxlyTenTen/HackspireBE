import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import JoinRequest, Notification, Profile, Submission, Team, TeamMember
from app.services import supabase_auth
from app.services.audit import log_admin_action
from app.services.notifications import create_notifications
from app.services.teams import sync_full_status


async def _get_participant(db: AsyncSession, participant_id: uuid.UUID) -> Profile:
    profile = await db.get(Profile, participant_id)
    if profile is None or profile.role != "participant":
        raise ApiError(404, "Participant not found")
    return profile


async def resend_invite(db: AsyncSession, admin: Profile, participant_id: uuid.UUID) -> Profile:
    """Send a fresh invite link to a participant who never accepted (or whose link expired)."""
    profile = await _get_participant(db, participant_id)
    if profile.invite_status == "active":
        raise ApiError(
            409,
            "This participant already activated their account — use Reset PW if they are locked out",
        )
    try:
        auth_user = await supabase_auth.invite_user_by_email(
            profile.email, data={"name": profile.name, "student_staff_id": profile.student_staff_id}
        )
    except ApiError as exc:
        raise ApiError(409, f"Could not resend the invite: {exc.message}")
    if auth_user.get("id") != str(profile.id):
        # The sign-in record was missing, so Supabase created a different one.
        # Remove that stray record instead of leaving two accounts for one email.
        await supabase_auth.admin_delete_user(auth_user["id"])
        raise ApiError(
            409,
            "This participant's sign-in record doesn't match their profile — delete them and add them again",
        )
    profile.invite_status = "invited"
    log_admin_action(
        db, admin.id, "participant_invite_resent", target_table="profiles", target_id=profile.id
    )
    await db.commit()
    return profile


async def delete_participant(db: AsyncSession, admin: Profile, participant_id: uuid.UUID) -> None:
    """Remove a participant from Supabase Auth and the database together."""
    profile = await _get_participant(db, participant_id)
    led_team = await db.scalar(select(Team).where(Team.leader_id == profile.id))
    if led_team is not None:
        raise ApiError(
            409,
            f"{profile.name} leads team {led_team.name} — delete the team or reassign "
            "leadership in Admin > Teams first",
        )

    # Auth first: if this fails nothing has changed, and a retry after a later
    # database failure is safe because an already-deleted auth user is not an error.
    if not await supabase_auth.admin_delete_user(str(profile.id)):
        legacy = await supabase_auth.admin_get_user_by_email(profile.email)
        if legacy is not None:
            await supabase_auth.admin_delete_user(legacy["id"])

    request_ids = list(
        await db.scalars(select(JoinRequest.id).where(JoinRequest.participant_id == profile.id))
    )
    if request_ids:
        # Leaders' Approve/Reject notifications for this person's requests would dangle.
        await db.execute(
            delete(Notification).where(
                Notification.reference_id.in_(request_ids),
                Notification.type.in_(("join_request", "team_invite")),
            )
        )
    await db.execute(delete(Notification).where(Notification.participant_id == profile.id))
    await db.execute(delete(JoinRequest).where(JoinRequest.participant_id == profile.id))

    membership = await db.scalar(select(TeamMember).where(TeamMember.participant_id == profile.id))
    if membership is not None:
        team = await db.get(Team, membership.team_id)
        others = [
            m
            for m in (
                await db.scalars(select(TeamMember).where(TeamMember.team_id == membership.team_id))
            ).all()
            if m.participant_id != profile.id
        ]
        await db.delete(membership)
        if team is not None:
            sync_full_status(team, len(others))
            create_notifications(
                db,
                [m.participant_id for m in others],
                "team_update",
                f"{profile.name} was removed from your team {team.name}",
                reference_id=team.id,
            )

    await db.execute(
        update(Submission).where(Submission.submitted_by == profile.id).values(submitted_by=None)
    )
    email = profile.email
    await db.delete(profile)
    log_admin_action(
        db, admin.id, "participant_deleted", target_table="profiles", target_id=participant_id, details=email
    )
    await db.commit()
