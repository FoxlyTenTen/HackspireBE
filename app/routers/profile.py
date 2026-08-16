from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import Profile
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.common import error_responses
from app.schemas.profile import ProfileRead, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get(
    "",
    response_model=ProfileRead,
    summary="Get the current user's profile",
    responses=error_responses(401, 403),
)
async def get_profile(user: Profile = Depends(get_current_user)) -> ProfileRead:
    return user


@router.patch(
    "",
    response_model=ProfileRead,
    summary="Edit the current user's editable profile fields",
    description="Update username, technical_skills, or preferred_role.",
    responses=error_responses(400, 401, 403, 409, 422),
)
async def update_profile(
    body: ProfileUpdate,
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileRead:
    if body.username is not None and body.username != user.username:
        existing = await db.scalar(select(Profile).where(Profile.username == body.username))
        if existing is not None:
            raise ApiError(409, "Username is already taken")
        user.username = body.username
    if body.technical_skills is not None:
        user.technical_skills = body.technical_skills
    if body.preferred_role is not None:
        user.preferred_role = body.preferred_role
    await db.commit()
    return user


# No self-service email change: participants who need their email corrected
# go through an admin (POST /admin/participants/{id}/change-email), which
# updates both Supabase Auth and this profile row in one step, no
# confirmation email required.
