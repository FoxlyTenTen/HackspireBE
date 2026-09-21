import csv
import io
import secrets
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import ApiError
from app.db.models import Profile
from app.db.session import get_db
from app.dependencies import require_admin
from app.schemas.admin import (
    AdminChangeEmailRequest,
    AdminParticipantCreate,
    AdminParticipantsResponse,
    ImportConfirmRequest,
    ImportConfirmResponse,
    ImportPreviewResponse,
    ResetPasswordResponse,
)
from app.schemas.common import MessageResponse, error_responses
from app.schemas.profile import ProfileRead
from app.services import admin_import, supabase_auth
from app.services import admin_participants as admin_participant_service
from app.services.audit import log_admin_action

router = APIRouter(prefix="/admin/participants", tags=["Admin — Participants"])


@router.post(
    "/import",
    response_model=ImportPreviewResponse,
    summary="Upload the participant Excel file for preview",
    description=(
        "Step 1 of 2: parses the uploaded `.xlsx` and returns a per-row preview "
        "WITHOUT writing anything. Rows with duplicate emails/IDs or missing "
        "required fields are flagged individually — one bad row never rejects the "
        "whole file. Required header columns: `name`, `email`, `student_staff_id`. "
        "Optional columns: `reference_id`, `university_name`, `technical_skills`, "
        "`preferred_role`."
    ),
    responses=error_responses(400, 401, 403, 422),
)
async def import_preview(
    file: UploadFile = File(description="Excel .xlsx file of participants"),
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ImportPreviewResponse:
    content = await file.read()
    return await admin_import.preview(db, content)


@router.post(
    "/import/confirm",
    response_model=ImportConfirmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Confirm the import and send invite emails",
    description=(
        "Step 2 of 2: send back the `ok` rows from the preview. Each row is "
        "re-validated, then invited via Supabase Auth — a real invite email is "
        "sent and the participant sets their own password from its link. Rows "
        "that fail re-validation or whose invite email cannot be sent are "
        "skipped and reported, not fatal."
    ),
    responses=error_responses(400, 401, 403, 422),
)
async def import_confirm(
    body: ImportConfirmRequest,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ImportConfirmResponse:
    return await admin_import.confirm(db, admin, body.rows)


@router.post(
    "",
    response_model=ProfileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a single participant manually",
    description=(
        "Same validation and invite email as one Excel row: a duplicate email or "
        "student/staff ID is rejected with 409, otherwise the Supabase auth user and "
        "the profile are created together with `invite_status = invited`."
    ),
    responses=error_responses(401, 403, 409, 422, 503),
)
async def create_participant(
    body: AdminParticipantCreate,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Profile:
    return await admin_import.create_one(db, admin, **body.model_dump())


@router.post(
    "/{participant_id}/resend-invite",
    response_model=MessageResponse,
    summary="Resend the invite email (expired or ignored invite)",
    description=(
        "Only for participants who haven't activated their account. Sends a fresh "
        "invite link through Supabase Auth; an already-active participant gets 409 "
        "(use reset-password instead)."
    ),
    responses=error_responses(401, 403, 404, 409),
)
async def resend_invite(
    participant_id: uuid.UUID,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    profile = await admin_participant_service.resend_invite(db, admin, participant_id)
    return MessageResponse(message=f"A new invite email was sent to {profile.email}.")


@router.delete(
    "/{participant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a participant (auth user + profile)",
    description=(
        "Removes the Supabase auth user and the profile together, plus the "
        "participant's notifications, join requests and team membership (the team is "
        "notified). A team leader can't be deleted — delete the team or reassign "
        "leadership first (409)."
    ),
    responses=error_responses(401, 403, 404, 409),
)
async def delete_participant(
    participant_id: uuid.UUID,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    await admin_participant_service.delete_participant(db, admin, participant_id)


@router.get(
    "",
    response_model=AdminParticipantsResponse,
    summary="Full participant list with count vs the 150 cap",
    description=(
        "Set `format=csv` to download the list as a CSV export instead of JSON."
    ),
    responses=error_responses(401, 403),
)
async def list_participants(
    format: Literal["json", "csv"] = Query(default="json"),
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    profiles = (
        await db.scalars(
            select(Profile).where(Profile.role == "participant").order_by(Profile.name)
        )
    ).all()
    if format == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "id",
                "name",
                "email",
                "student_staff_id",
                "reference_id",
                "university_name",
                "technical_skills",
                "preferred_role",
                "invite_status",
                "created_at",
            ]
        )
        for p in profiles:
            writer.writerow(
                [
                    p.id,
                    p.name,
                    p.email,
                    p.student_staff_id,
                    p.reference_id,
                    p.university_name,
                    p.technical_skills,
                    p.preferred_role,
                    p.invite_status,
                    p.created_at,
                ]
            )
        return Response(
            content=buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=participants.csv"},
        )
    return AdminParticipantsResponse(
        count=len(profiles),
        cap=settings.participant_cap,
        remaining=max(settings.participant_cap - len(profiles), 0),
        participants=profiles,
    )


@router.post(
    "/{participant_id}/change-email",
    response_model=MessageResponse,
    summary="Correct a participant's email address (admin)",
    description=(
        "For fixing a wrong address in the imported Excel. Updates the email "
        "immediately via Supabase Auth's admin API (no confirmation link). "
        "Supabase's admin email update leaves password sign-in unreliable "
        "afterward even for already-activated accounts, so a set-password / "
        "reset link is always sent to the corrected address."
    ),
    responses=error_responses(401, 403, 404, 409, 503),
)
async def change_participant_email(
    participant_id: uuid.UUID,
    body: AdminChangeEmailRequest,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    profile = await db.get(Profile, participant_id)
    if profile is None or profile.role != "participant":
        raise ApiError(404, "Participant not found")
    new_email = body.new_email.strip().lower()
    taken = await db.scalar(
        select(Profile).where(Profile.email == new_email, Profile.id != profile.id)
    )
    if taken is not None:
        raise ApiError(409, "That email is already registered to another account")
    old_email = profile.email
    try:
        await supabase_auth.admin_update_user_by_id(
            str(profile.id), email=new_email, email_confirm=True
        )
    except ApiError:
        # Legacy row whose id doesn't match auth.users.id — locate by old email,
        # or create the auth user fresh if none exists at all.
        auth_user = await supabase_auth.admin_get_user_by_email(old_email)
        if auth_user is not None:
            await supabase_auth.admin_update_user_by_id(
                auth_user["id"], email=new_email, email_confirm=True
            )
        else:
            await supabase_auth.admin_create_user(
                new_email, secrets.token_urlsafe(16), email_confirm=True
            )
    profile.email = new_email
    # Supabase's admin email update leaves password sign-in unreliable even for
    # already-activated accounts, so always send a reset link — it doubles as
    # "set your password" for never-activated accounts too, landing on the
    # same /accept-invite page as an invite.
    await supabase_auth.reset_password_for_email(new_email)
    log_admin_action(
        db,
        admin.id,
        "participant_email_changed",
        target_table="profiles",
        target_id=profile.id,
        details=f"{old_email} -> {new_email}",
    )
    await db.commit()
    return MessageResponse(
        message=(
            f"Email updated to {new_email} — a set-password link was sent to the "
            "new address (required for sign-in to keep working after an email change)."
        )
    )


@router.post(
    "/{participant_id}/reset-password",
    response_model=ResetPasswordResponse,
    summary="Reset a locked-out participant's password (admin fallback)",
    description=(
        "Fallback for when the participant's email doesn't work (typo, spam "
        "filter, unchecked inbox): sets a temporary password via Supabase "
        "Auth's admin API and force-confirms the email, so the account works "
        "without any email ever being delivered. Give the temporary password "
        "to the participant; first_login forces them to change it."
    ),
    responses=error_responses(401, 403, 404, 503),
)
async def reset_password(
    participant_id: uuid.UUID,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ResetPasswordResponse:
    profile = await db.get(Profile, participant_id)
    if profile is None or profile.role != "participant":
        raise ApiError(404, "Participant not found")
    temporary_password = secrets.token_urlsafe(9)
    try:
        await supabase_auth.admin_update_user_by_id(
            str(profile.id), password=temporary_password, email_confirm=True
        )
    except ApiError:
        # Legacy account whose profile id doesn't match auth.users.id (or no
        # auth user at all) — find by email, creating the auth user if needed.
        auth_user = await supabase_auth.admin_get_user_by_email(profile.email)
        if auth_user is not None:
            await supabase_auth.admin_update_user_by_id(
                auth_user["id"], password=temporary_password, email_confirm=True
            )
        else:
            await supabase_auth.admin_create_user(
                profile.email, temporary_password, email_confirm=True
            )
    profile.first_login = True
    profile.invite_status = "active"  # usable without the invite email now
    log_admin_action(
        db, admin.id, "participant_password_reset", target_table="profiles", target_id=profile.id
    )
    await db.commit()
    return ResetPasswordResponse(
        participant_id=profile.id, temporary_password=temporary_password
    )
