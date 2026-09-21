import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import ApiError
from app.db.models import Profile
from app.services import supabase_auth


async def authenticate(
    db: AsyncSession, username: str, password: str
) -> tuple[Profile, dict]:
    """Username matches either email or student/staff ID.

    Resolves the account locally, then delegates the actual credential check to
    Supabase Auth's sign_in_with_password. Returns (profile, supabase session).
    """
    profile = await db.scalar(
        select(Profile).where(
            or_(
                # Supabase lowercases emails, so match case-insensitively — an
                # Excel row like "Ali@Student.edu.my" must still log in.
                func.lower(Profile.email) == username.strip().lower(),
                Profile.student_staff_id == username.strip(),
            )
        )
    )
    if profile is None:
        raise ApiError(401, "Invalid username or password")
    session = await supabase_auth.sign_in_with_password(profile.email, password)
    # A successful sign-in proves the invite was accepted (a password exists),
    # so this is the exact moment 'invited' becomes 'active'.
    if profile.invite_status == "invited":
        profile.invite_status = "active"
        await db.commit()
    return profile, session


async def change_password(
    db: AsyncSession, user: Profile, access_token: str, new_password: str
) -> None:
    """Supabase Auth update_user() with the caller's own token."""
    await supabase_auth.update_user(access_token, password=new_password)
    changed = False
    if user.first_login:
        user.first_login = False
        changed = True
    # Setting a password from the invite link proves the invite was accepted —
    # the frontend keeps that session (no separate login), so mark it active here
    # instead of waiting for a later password login.
    if user.invite_status == "invited":
        user.invite_status = "active"
        changed = True
    if changed:
        await db.commit()


async def _ensure_admin_auth_user() -> uuid.UUID | None:
    """Create the admin's Supabase auth user if missing; returns its id or None."""
    if not (settings.supabase_url and settings.supabase_service_role_key):
        print("seed_admin: Supabase Auth not configured — admin login will not work yet")
        return None
    try:
        auth_user = await supabase_auth.admin_create_user(
            settings.admin_email, settings.admin_password, email_confirm=True
        )
        return uuid.UUID(auth_user["id"])
    except ApiError as exc:
        # "already registered" → auth user exists from a previous run; the
        # email-claim fallback in get_current_user links it to the profile.
        print(f"seed_admin: Supabase user not created ({exc.message})")
    except Exception as exc:  # network failure must not block startup
        print(f"seed_admin: Supabase unreachable ({exc})")
    return None


async def seed_admin(db: AsyncSession) -> None:
    """Bootstrap the admin on startup: the Supabase auth user (always ensured,
    so pre-migration DBs self-heal) and the profile row if it doesn't exist.
    Credentials come from ADMIN_EMAIL / ADMIN_PASSWORD in .env, same as before.
    """
    auth_id = await _ensure_admin_auth_user()
    existing = await db.scalar(select(Profile).where(Profile.role == "admin"))
    if existing is not None:
        return
    db.add(
        Profile(
            id=auth_id or uuid.uuid4(),
            name=settings.admin_name,
            email=settings.admin_email,
            student_staff_id=settings.admin_student_staff_id,
            role="admin",
            first_login=False,
            invite_status="active",
        )
    )
    await db.commit()
