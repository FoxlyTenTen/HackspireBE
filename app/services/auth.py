from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import ApiError
from app.core.security import hash_password, hash_password_async, verify_password_async
from app.db.models import Profile


async def authenticate(db: AsyncSession, username: str, password: str) -> Profile:
    """Username matches either email or student/staff ID."""
    profile = await db.scalar(
        select(Profile).where(
            or_(Profile.email == username, Profile.student_staff_id == username)
        )
    )
    if (
        profile is None
        or profile.hashed_password is None
        or not await verify_password_async(password, profile.hashed_password)
    ):
        raise ApiError(401, "Invalid username or password")
    return profile


async def change_password(db: AsyncSession, user: Profile, new_password: str) -> None:
    user.hashed_password = await hash_password_async(new_password)
    user.first_login = False
    await db.commit()


async def seed_admin(db: AsyncSession) -> None:
    """Create the bootstrap admin account on startup if no admin exists."""
    existing = await db.scalar(select(Profile).where(Profile.role == "admin"))
    if existing is not None:
        return
    db.add(
        Profile(
            name=settings.admin_name,
            email=settings.admin_email,
            student_staff_id=settings.admin_student_staff_id,
            role="admin",
            first_login=False,
            hashed_password=hash_password(settings.admin_password),
        )
    )
    await db.commit()
