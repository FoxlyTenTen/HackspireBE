from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.db.models import Profile
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LoginResponse
from app.schemas.common import MessageResponse, error_responses
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Log in with username and password",
    description=(
        "The only route that does not require a bearer token. `username` may be "
        "either the account email or the student/staff ID. Returns a JWT plus the "
        "`first_login` flag — if it is `true`, the client MUST call "
        "`/auth/change-password` before using any other endpoint."
    ),
    responses=error_responses(401, 422),
)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    profile = await auth_service.authenticate(db, body.username, body.password)
    token = create_access_token(profile.id, profile.role)
    return LoginResponse(jwt=token, first_login=profile.first_login, role=profile.role)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change the current user's password",
    description=(
        "Clears the `first_login` flag. After a first-login password change the "
        "client is expected to force a fresh login."
    ),
    responses=error_responses(401, 422),
)
async def change_password(
    body: ChangePasswordRequest,
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await auth_service.change_password(db, user, body.new_password)
    return MessageResponse(message="Password changed successfully — please log in again")
