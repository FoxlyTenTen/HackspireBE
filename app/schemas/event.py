import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TimelineStatus = Literal["TBD", "Proposed", "Confirmed", "Declined"]
MaterialCategory = Literal["general", "submission_template"]


class TimelineItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bootcamp_name: str
    date_label: str
    time_session: str
    session_type: str
    speaker_name: str | None
    speaker_bio: str | None
    organization: str | None
    session_description: str | None
    speaker_photo_url: str | None
    status: TimelineStatus
    remarks: str | None
    order_index: int
    zoom_link: str | None
    material_file_url: str | None
    material_file_name: str | None


class TimelineItemWrite(BaseModel):
    bootcamp_name: str = Field(examples=["Online Bootcamp 1"])
    date_label: str = Field(examples=["13-15 Oct 2026"])
    time_session: str = Field(examples=["2:10 PM - Keynote Session 1"])
    session_type: str = Field(examples=["Keynote"])
    speaker_name: str | None = Field(default=None, examples=["Jane Doe"])
    speaker_bio: str | None = Field(default=None)
    organization: str | None = Field(default=None, examples=["Acme Corp"])
    session_description: str | None = Field(default=None)
    speaker_photo_url: str | None = Field(default=None)
    status: TimelineStatus = Field(default="TBD")
    remarks: str | None = Field(default=None)
    order_index: int = Field(default=0, examples=[0])
    zoom_link: str | None = Field(default=None)
    material_file_url: str | None = Field(
        default=None, description="Pass through unchanged — set via PATCH /admin/event/timeline/{id}"
    )
    material_file_name: str | None = Field(default=None)


class TimelineUpdate(BaseModel):
    items: list[TimelineItemWrite] = Field(
        description="Full replacement of the timeline, ordered by order_index"
    )


class CountdownUpdate(BaseModel):
    countdown_at: datetime = Field(
        description="Event start date/time the countdown targets",
        examples=["2026-09-12T09:00:00+08:00"],
    )


class EventInfoResponse(BaseModel):
    name: str
    tagline: str
    venue: str
    countdown_at: datetime | None
    submission_deadline_at: datetime | None
    round2_submission_deadline_at: datetime | None
    timeline: list[TimelineItemRead]
    sponsors: list[dict]
    prize_pool: dict
    contact: dict


class MaterialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_name: str
    file_url: str
    category: MaterialCategory
    uploaded_at: datetime


class FinalistRead(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    team_name: str
    published: bool
    published_at: datetime | None


class FinalistsPut(BaseModel):
    team_ids: list[uuid.UUID] = Field(
        description="Full replacement of the finalist list"
    )
    published: bool = Field(
        default=False, description="If true, the list becomes visible to participants"
    )


class WinnerRead(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    team_name: str
    placement: str
    published: bool
    published_at: datetime | None


class WinnerEntry(BaseModel):
    team_id: uuid.UUID
    placement: str = Field(examples=["champion"])


class WinnersPut(BaseModel):
    winners: list[WinnerEntry] = Field(description="Full replacement of the winner list")
    published: bool = Field(default=False)


class AnnouncementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    body: str
    image_url: str | None
    posted_by: uuid.UUID
    posted_at: datetime
    updated_at: datetime | None
