import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ApiError
from app.core.uploads import MAX_EXCEL_BYTES, MAX_IMAGE_BYTES, check_upload_size
from app.db.models import AuditLog, Material, Profile
from app.db.session import get_db
from app.dependencies import require_admin
from app.schemas.admin import (
    AuditLogRead,
    EventSettingsRead,
    TeamFormationDeadlineUpdate,
    TimelineImportConfirmRequest,
    TimelineImportConfirmResponse,
    TimelineImportPreviewResponse,
)
from app.schemas.common import error_responses
from app.schemas.notification import NotificationBroadcast, NotificationBroadcastResponse
from app.schemas.event import (
    AnnouncementRead,
    CountdownUpdate,
    FinalistRead,
    FinalistsPut,
    LandingCountdownUpdate,
    MaterialCategory,
    MaterialRead,
    TimelineItemRead,
    TimelineUpdate,
    WinnerRead,
    WinnersPut,
)
from app.services import content as content_service
from app.services import notifications as notification_service
from app.services import timeline_import as timeline_import_service
from app.services.audit import log_admin_action
from app.services.storage import get_announcements_storage, get_materials_storage

router = APIRouter(prefix="/admin", tags=["Admin — Event Content"])


@router.patch(
    "/event/countdown",
    response_model=EventSettingsRead,
    summary="Update the event start date/time",
    responses=error_responses(401, 403, 422),
)
async def update_countdown(
    body: CountdownUpdate,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> EventSettingsRead:
    row = await content_service.set_countdown(
        db, admin, body.countdown_at, body.countdown_description
    )
    return _to_event_settings_read(row)


@router.patch(
    "/event/landing-countdown",
    response_model=EventSettingsRead,
    summary="Update the public marketing landing page's countdown",
    description=(
        "Separate from /event/countdown — this targets the standalone marketing "
        "site at the apex domain (read with no auth via GET /public/landing-countdown), "
        "not the authenticated app's Dashboard widget."
    ),
    responses=error_responses(401, 403, 422),
)
async def update_landing_countdown(
    body: LandingCountdownUpdate,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> EventSettingsRead:
    row = await content_service.set_landing_countdown(
        db, admin, body.landing_countdown_at, body.landing_countdown_label
    )
    return _to_event_settings_read(row)


@router.patch(
    "/event/team-formation-deadline",
    response_model=EventSettingsRead,
    summary="Set or update the team-formation deadline",
    description=(
        "After this moment participants can no longer create teams, request/invite, "
        "answer requests, leave, or edit team membership. Admin actions are unaffected."
    ),
    responses=error_responses(401, 403, 422),
)
async def update_team_formation_deadline(
    body: TeamFormationDeadlineUpdate,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> EventSettingsRead:
    row = await content_service.set_team_formation_deadline(
        db, admin, body.team_formation_deadline_at
    )
    return _to_event_settings_read(row)


def _to_event_settings_read(row) -> EventSettingsRead:
    return EventSettingsRead(
        countdown_at=row.countdown_at,
        countdown_description=row.countdown_description,
        landing_countdown_at=row.landing_countdown_at,
        landing_countdown_label=row.landing_countdown_label,
        submission_deadline_at=row.submission_deadline_at,
        round2_submission_deadline_at=row.round2_submission_deadline_at,
        team_formation_deadline_at=row.team_formation_deadline_at,
        updated_at=row.updated_at,
    )


@router.patch(
    "/event/timeline",
    response_model=list[TimelineItemRead],
    summary="Replace the event timeline/agenda",
    description="Full replacement: the submitted items become the entire timeline.",
    responses=error_responses(401, 403, 422),
)
async def update_timeline(
    body: TimelineUpdate,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[TimelineItemRead]:
    return await content_service.replace_timeline(db, admin, body.items)


@router.patch(
    "/event/timeline/{item_id}",
    response_model=TimelineItemRead,
    summary="Edit a single timeline entry",
    description=(
        "Partial update of one timeline item — only the fields sent are changed. "
        "Optionally attach/replace a material file, or set remove_material=true "
        "to detach the existing one. Sending zoom_link or recording_url as an "
        "empty string clears it. hide_zoom_link only flags the session — the "
        "participant page decides not to show the link."
    ),
    responses=error_responses(400, 401, 403, 404, 413, 422),
)
async def update_timeline_item(
    item_id: uuid.UUID,
    bootcamp_name: str | None = Form(default=None),
    date_label: str | None = Form(default=None),
    time_session: str | None = Form(default=None),
    session_type: str | None = Form(default=None),
    speaker_name: str | None = Form(default=None),
    speaker_bio: str | None = Form(default=None),
    organization: str | None = Form(default=None),
    session_description: str | None = Form(default=None),
    speaker_photo_url: str | None = Form(default=None),
    status: str | None = Form(default=None),
    remarks: str | None = Form(default=None),
    order_index: int | None = Form(default=None),
    zoom_link: str | None = Form(default=None),
    hide_zoom_link: bool | None = Form(default=None),
    recording_url: str | None = Form(default=None),
    remove_material: bool = Form(default=False),
    material: UploadFile | None = File(default=None, description="Optional material file to attach"),
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> TimelineItemRead:
    material_file: tuple[str, str] | None = None
    if material is not None and material.filename:
        content = await material.read()
        if not content:
            raise ApiError(400, "Uploaded material is empty")
        check_upload_size(content, MAX_IMAGE_BYTES, "Material file")
        file_url = await get_materials_storage().save(material.filename, content)
        material_file = (material.filename, file_url)
    return await content_service.update_timeline_item(
        db,
        admin,
        item_id,
        bootcamp_name=bootcamp_name,
        date_label=date_label,
        time_session=time_session,
        session_type=session_type,
        speaker_name=speaker_name,
        speaker_bio=speaker_bio,
        organization=organization,
        session_description=session_description,
        speaker_photo_url=speaker_photo_url,
        status=status,
        remarks=remarks,
        order_index=order_index,
        zoom_link=zoom_link,
        hide_zoom_link=hide_zoom_link,
        recording_url=recording_url,
        material_file=material_file,
        remove_material=remove_material,
    )


@router.post(
    "/timeline/import",
    response_model=TimelineImportPreviewResponse,
    summary="Upload the timeline Excel file for preview",
    description=(
        "Step 1 of 2: parses the uploaded `.xlsx` and returns a per-row preview "
        "WITHOUT writing anything."
    ),
    responses=error_responses(400, 401, 403, 413, 422),
)
async def timeline_import_preview(
    file: UploadFile = File(description="Excel .xlsx file of timeline sessions"),
    admin: Profile = Depends(require_admin),
) -> TimelineImportPreviewResponse:
    content = await file.read()
    check_upload_size(content, MAX_EXCEL_BYTES, "Excel file")
    return timeline_import_service.preview(content)


@router.post(
    "/timeline/import/confirm",
    response_model=TimelineImportConfirmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Confirm the timeline import and replace the timeline",
    description=(
        "Step 2 of 2: send back the `ok` rows from the preview. Replaces the "
        "entire timeline, same semantics as PATCH /admin/event/timeline."
    ),
    responses=error_responses(400, 401, 403, 422),
)
async def timeline_import_confirm(
    body: TimelineImportConfirmRequest,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> TimelineImportConfirmResponse:
    return await timeline_import_service.confirm(db, admin, body.rows)


@router.put(
    "/finalists",
    response_model=list[FinalistRead],
    summary="Publish or update the finalist list",
    description=(
        "Full replacement of the finalist list. With `published=true` the list "
        "becomes visible to participants via GET /finalists."
    ),
    responses=error_responses(401, 403, 404, 422),
)
async def put_finalists(
    body: FinalistsPut,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[FinalistRead]:
    return await content_service.put_finalists(db, admin, body)


@router.put(
    "/winners",
    response_model=list[WinnerRead],
    summary="Publish or update the winner announcement",
    description=(
        "Full replacement of the winner list with placements. With "
        "`published=true` it becomes visible via GET /winners."
    ),
    responses=error_responses(401, 403, 404, 422),
)
async def put_winners(
    body: WinnersPut,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[WinnerRead]:
    return await content_service.put_winners(db, admin, body)


@router.post(
    "/materials",
    response_model=MaterialRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a material file",
    description="Stored in a public Supabase Storage bucket.",
    responses=error_responses(400, 401, 403, 413, 422),
)
async def upload_material(
    file: UploadFile = File(description="The file to publish to participants"),
    category: MaterialCategory = Form(default="general"),
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MaterialRead:
    content = await file.read()
    if not content:
        raise ApiError(400, "Uploaded file is empty")
    check_upload_size(content, MAX_IMAGE_BYTES, "Material file")
    file_url = await get_materials_storage().save(file.filename or "material", content)
    material = Material(
        file_name=file.filename or "material",
        file_url=file_url,
        category=category,
        uploaded_by=admin.id,
    )
    db.add(material)
    await db.flush()
    log_admin_action(
        db, admin.id, "material_uploaded", target_table="materials", target_id=material.id
    )
    await db.commit()
    return material


@router.delete(
    "/materials/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a material file",
    responses=error_responses(401, 403, 404),
)
async def delete_material(
    material_id: uuid.UUID,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    material = await db.get(Material, material_id)
    if material is None:
        raise ApiError(404, "Material not found")
    await get_materials_storage().delete(material.file_url)
    log_admin_action(
        db, admin.id, "material_deleted", target_table="materials", target_id=material.id
    )
    await db.delete(material)
    await db.commit()


@router.post(
    "/announcements",
    response_model=AnnouncementRead,
    status_code=status.HTTP_201_CREATED,
    summary="Post an announcement to all participants",
    description=(
        "Also creates an `announcement` notification for every participant. "
        "The image, if any, is uploaded as a file (not a link)."
    ),
    responses=error_responses(400, 401, 403, 413, 422),
)
async def post_announcement(
    title: str = Form(...),
    body: str = Form(...),
    image: UploadFile | None = File(default=None, description="Optional image to attach"),
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AnnouncementRead:
    image_url = None
    if image is not None and image.filename:
        content = await image.read()
        if not content:
            raise ApiError(400, "Uploaded image is empty")
        check_upload_size(content, MAX_IMAGE_BYTES, "Image")
        image_url = await get_announcements_storage().save(image.filename, content)
    return await content_service.create_announcement(db, admin, title, body, image_url)


@router.patch(
    "/announcements/{announcement_id}",
    response_model=AnnouncementRead,
    summary="Edit a posted announcement",
    description="Uploading a new image replaces the old one; the old file is deleted.",
    responses=error_responses(400, 401, 403, 404, 413, 422),
)
async def patch_announcement(
    announcement_id: uuid.UUID,
    title: str | None = Form(default=None),
    body: str | None = Form(default=None),
    image: UploadFile | None = File(default=None, description="Optional replacement image"),
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AnnouncementRead:
    image_url = None
    if image is not None and image.filename:
        content = await image.read()
        if not content:
            raise ApiError(400, "Uploaded image is empty")
        check_upload_size(content, MAX_IMAGE_BYTES, "Image")
        existing = await content_service.get_announcement_or_404(db, announcement_id)
        old_image_url = existing.image_url
        image_url = await get_announcements_storage().save(image.filename, content)
        if old_image_url:
            await get_announcements_storage().delete(old_image_url)
    return await content_service.update_announcement(
        db, admin, announcement_id, title, body, image_url
    )


@router.delete(
    "/announcements/{announcement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an announcement",
    responses=error_responses(401, 403, 404),
)
async def delete_announcement(
    announcement_id: uuid.UUID,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    announcement = await content_service.get_announcement_or_404(db, announcement_id)
    image_url = announcement.image_url
    await content_service.delete_announcement(db, admin, announcement_id)
    if image_url:
        await get_announcements_storage().delete(image_url)


@router.post(
    "/notifications/broadcast",
    response_model=NotificationBroadcastResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a quick notification to every participant",
    description=(
        "Notification-only broadcast: no title/image, not saved anywhere else, and "
        "doesn't show up on the Announcements page — just lands in every participant's "
        "notification feed. Use the Announcements endpoints for anything that needs "
        "to persist and be browsable."
    ),
    responses=error_responses(401, 403, 422),
)
async def broadcast_notification(
    body: NotificationBroadcast,
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> NotificationBroadcastResponse:
    recipients = await notification_service.broadcast(db, admin, body.message)
    return NotificationBroadcastResponse(recipients=recipients)


@router.get(
    "/audit-log",
    response_model=list[AuditLogRead],
    summary="View the admin action history",
    description="Most recent actions first. Use `limit`/`offset` to page through history.",
    responses=error_responses(401, 403),
)
async def list_audit_log(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLogRead]:
    entries = (
        await db.scalars(
            select(AuditLog)
            .options(selectinload(AuditLog.admin))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [
        AuditLogRead(
            id=e.id,
            admin_id=e.admin_id,
            admin_name=e.admin.name if e.admin else None,
            action=e.action,
            target_table=e.target_table,
            target_id=e.target_id,
            details=e.details,
            created_at=e.created_at,
        )
        for e in entries
    ]
