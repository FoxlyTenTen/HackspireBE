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
from app.core.security import hash_password_async
from app.db.models import Profile
from app.db.session import get_db
from app.dependencies import require_admin
from app.schemas.admin import (
    AdminParticipantsResponse,
    ImportConfirmRequest,
    ImportConfirmResponse,
    ImportPreviewResponse,
    ResetPasswordResponse,
)
from app.schemas.common import error_responses
from app.services import admin_import

router = APIRouter(prefix="/admin/participants", tags=["Admin — Participants"])


@router.post(
    "/import",
    response_model=ImportPreviewResponse,
    summary="Upload the participant Excel file for preview",
    description=(
        "Step 1 of 2: parses the uploaded `.xlsx` and returns a per-row preview "
        "WITHOUT writing anything. Rows with duplicate emails/IDs or missing "
        "required fields are flagged individually — one bad row never rejects the "
        "whole file. Expected header columns: `name`, `email`, `student_staff_id`."
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
    summary="Confirm the import and create accounts",
    description=(
        "Step 2 of 2: send back the `ok` rows from the preview. Each row is "
        "re-validated, then an account + profile is created with the "
        "student/staff ID as the initial password and `first_login=true`. Rows "
        "that fail re-validation are skipped and reported, not fatal."
    ),
    responses=error_responses(400, 401, 403, 422),
)
async def import_confirm(
    body: ImportConfirmRequest,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ImportConfirmResponse:
    return await admin_import.confirm(db, body.rows)


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
        writer.writerow(["id", "name", "email", "student_staff_id", "first_login", "created_at"])
        for p in profiles:
            writer.writerow(
                [p.id, p.name, p.email, p.student_staff_id, p.first_login, p.created_at]
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
    "/{participant_id}/reset-password",
    response_model=ResetPasswordResponse,
    summary="Reset a locked-out participant's password",
    description=(
        "Generates a temporary password and re-enables the forced first-login "
        "password change. Give the temporary password to the participant."
    ),
    responses=error_responses(401, 403, 404),
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
    profile.hashed_password = await hash_password_async(temporary_password)
    profile.first_login = True
    await db.commit()
    return ResetPasswordResponse(
        participant_id=profile.id, temporary_password=temporary_password
    )
