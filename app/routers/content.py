from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Profile
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.common import error_responses
from app.schemas.event import (
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
