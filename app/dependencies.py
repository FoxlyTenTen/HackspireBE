import uuid

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.core.security import decode_supabase_token
from app.db.models import Profile, Team, TeamMember
from app.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Profile:
    """Participant guard: any logged-in user with a valid Supabase access token."""
    if credentials is None:
        raise ApiError(401, "Missing bearer token")
    payload = await decode_supabase_token(credentials.credentials)
    if payload is None or "sub" not in payload:
        raise ApiError(401, "Invalid or expired token")
    try:
        profile_id = uuid.UUID(payload["sub"])
    except ValueError:
        raise ApiError(401, "Invalid or expired token")
    token_email = payload.get("email") or None
    profile = await db.get(Profile, profile_id)
    if profile is None and token_email:
        # Legacy accounts created before the Supabase Auth migration have a
        # profile id that doesn't match auth.users.id — link them by email.
        profile = await db.scalar(select(Profile).where(Profile.email == token_email))
    if profile is None:
        raise ApiError(401, "Account no longer exists")
    if token_email and profile.email != token_email:
        # Supabase confirmed an email change (the token carries the new
        # address) — sync our mirror column, unless another row owns it.
        taken = await db.scalar(select(Profile).where(Profile.email == token_email))
        if taken is None:
            profile.email = token_email
            await db.commit()
    # While a password change is forced, only the change itself and reading your
    # own profile are allowed — the frontend needs GET /profile to see
    # first_login and redirect to the change-password screen.
    path = request.url.path
    forced_change_allowed = path.endswith("/auth/change-password") or (
        request.method == "GET" and path.endswith("/profile")
    )
    if profile.first_login and not forced_change_allowed:
        raise ApiError(403, "Password change required before using the API")
    return profile


async def require_admin(user: Profile = Depends(get_current_user)) -> Profile:
    if user.role != "admin":
        raise ApiError(403, "Admin access required")
    return user


async def require_team_leader(
    team_id: uuid.UUID,
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Team:
    """Guard for leader-only routes on /teams/{team_id}/... — returns the team."""
    team = await db.get(Team, team_id)
    if team is None:
        raise ApiError(404, "Team not found")
    if team.leader_id != user.id:
        raise ApiError(403, "Only the team leader can perform this action")
    return team


async def require_team_member(
    team_id: uuid.UUID,
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Team:
    """Guard for team-member routes — leader, member, or admin. Returns the team."""
    team = await db.get(Team, team_id)
    if team is None:
        raise ApiError(404, "Team not found")
    if user.role == "admin" or team.leader_id == user.id:
        return team
    membership = await db.scalar(
        select(TeamMember).where(
            TeamMember.team_id == team_id, TeamMember.participant_id == user.id
        )
    )
    if membership is None:
        raise ApiError(403, "You are not a member of this team")
    return team
