import uuid

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.core.security import decode_access_token
from app.db.models import Profile, Team, TeamMember
from app.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Profile:
    """Participant guard: any logged-in user with a valid bearer token."""
    if credentials is None:
        raise ApiError(401, "Missing bearer token")
    payload = decode_access_token(credentials.credentials)
    if payload is None or "sub" not in payload:
        raise ApiError(401, "Invalid or expired token")
    try:
        profile_id = uuid.UUID(payload["sub"])
    except ValueError:
        raise ApiError(401, "Invalid or expired token")
    profile = await db.get(Profile, profile_id)
    if profile is None:
        raise ApiError(401, "Account no longer exists")
    if profile.first_login and not request.url.path.endswith("/auth/change-password"):
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
