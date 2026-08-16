import uuid

import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import Material, Profile
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.common import error_responses
from app.schemas.event import (
    AnnouncementRead,
    EventInfoResponse,
    FinalistRead,
    MaterialRead,
    WinnerRead,
)
from app.services import content as content_service

router = APIRouter(tags=["Home / Content"])


@router.get(
    "/event/info",
    response_model=EventInfoResponse,
    summary="Event info for the home screen",
    description=(
        "Event name, venue, countdown target, submission deadline, timeline/agenda, "
        "sponsors, prize pool and contact details."
    ),
    responses=error_responses(401, 403),
)
async def get_event_info(
    user: Profile = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> EventInfoResponse:
    return await content_service.event_info(db)


@router.get(
    "/materials",
    response_model=list[MaterialRead],
    summary="List downloadable materials",
    description="Slides, guidelines and other files uploaded by the organizers.",
    responses=error_responses(401, 403),
)
async def get_materials(
    user: Profile = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[MaterialRead]:
    return await content_service.list_materials(db)


@router.get(
    "/materials/{material_id}/download",
    summary="Download a material file",
    description="Streams the file with Content-Disposition: attachment so the browser downloads it instead of navigating.",
    responses=error_responses(401, 403, 404),
)
async def download_material(
    material_id: uuid.UUID,
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    material = await db.get(Material, material_id)
    if material is None:
        raise ApiError(404, "Material not found")
    async with httpx.AsyncClient(timeout=30.0) as client:
        upstream = await client.get(material.file_url)
    if upstream.status_code != 200:
        raise ApiError(404, "Material file not found")
    return Response(
        content=upstream.content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{material.file_name}"'},
    )


@router.get(
    "/finalists",
    response_model=list[FinalistRead],
    summary="Published finalist list",
    description="Only finalists the admin has published are returned.",
    responses=error_responses(401, 403),
)
async def get_finalists(
    user: Profile = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[FinalistRead]:
    return await content_service.list_finalists(db, published_only=True)


@router.get(
    "/winners",
    response_model=list[WinnerRead],
    summary="Published winner announcement",
    description="Only winners the admin has published are returned.",
    responses=error_responses(401, 403),
)
async def get_winners(
    user: Profile = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[WinnerRead]:
    return await content_service.list_winners(db, published_only=True)


@router.get(
    "/announcements",
    response_model=list[AnnouncementRead],
    summary="List announcements",
    description="All posted announcements, newest first.",
    responses=error_responses(401, 403),
)
async def get_announcements(
    user: Profile = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[AnnouncementRead]:
    return await content_service.list_announcements(db)


@router.get(
    "/announcements/{announcement_id}",
    response_model=AnnouncementRead,
    summary="Announcement detail",
    responses=error_responses(401, 403, 404),
)
async def get_announcement(
    announcement_id: uuid.UUID,
    user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnnouncementRead:
    return await content_service.get_announcement_or_404(db, announcement_id)
