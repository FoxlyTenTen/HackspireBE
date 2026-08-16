from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import Profile
from app.db.session import get_db
from app.dependencies import bearer_scheme, get_current_user
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    VerifyOtpRequest,
    VerifyOtpResponse,
)
from app.schemas.common import MessageResponse, error_responses
from app.services import auth as auth_service
from app.services import supabase_auth

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Log in with username and password",
    description=(
        "`username` may be either the account email or the student/staff ID. "
        "Credentials are checked by Supabase Auth; the returned `jwt` is "
        "Supabase's access token (expires ~1 hour — use /auth/refresh)."
    ),
    responses=error_responses(401, 422),
)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    profile, session = await auth_service.authenticate(db, body.username, body.password)
    return LoginResponse(
        jwt=session["access_token"],
        refresh_token=session["refresh_token"],
        first_login=profile.first_login,
        role=profile.role,
    )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Exchange a refresh token for a new session",
    responses=error_responses(401, 422),
)
async def refresh(body: RefreshRequest) -> RefreshResponse:
    session = await supabase_auth.refresh_session(body.refresh_token)
    return RefreshResponse(
        jwt=session["access_token"], refresh_token=session["refresh_token"]
    )


@router.post(
    "/verify-otp",
    response_model=VerifyOtpResponse,
    summary="Exchange an email link's token_hash for a session",
    description=(
        "Newer Supabase projects redirect invite/recovery/email-change links "
        "with `?token_hash=...&type=...` instead of a session in the URL "
        "fragment — the frontend calls this to complete that exchange."
    ),
    responses=error_responses(400, 422),
)
async def verify_otp(body: VerifyOtpRequest) -> VerifyOtpResponse:
    session = await supabase_auth.verify_otp(body.token_hash, body.type)
    return VerifyOtpResponse(
        jwt=session["access_token"], refresh_token=session["refresh_token"], type=body.type
    )


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Send a password-reset email (self-service)",
    description=(
        "Sends Supabase Auth's built-in reset email. Always answers with the "
        "same message so account existence is never leaked."
    ),
    responses=error_responses(422),
)
async def forgot_password(body: ForgotPasswordRequest) -> MessageResponse:
    try:
        await supabase_auth.reset_password_for_email(body.email)
    except ApiError:
        pass  # generic response regardless — no account enumeration
    return MessageResponse(
        message="If an account exists for that email, a reset link has been sent."
    )


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change the current user's password",
    description=(
        "Delegates to Supabase Auth update_user() with the caller's token and "
        "clears the `first_login` flag."
    ),
    responses=error_responses(401, 422),
)
async def change_password(
    body: ChangePasswordRequest,
    user: Profile = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await auth_service.change_password(db, user, credentials.credentials, body.new_password)
    return MessageResponse(message="Password changed successfully — please log in again")
