import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TimelineItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    time_label: str
    title: str
    description: str | None
    order_index: int


class TimelineItemWrite(BaseModel):
    time_label: str = Field(examples=["09:00"])
    title: str = Field(examples=["Opening ceremony"])
    description: str | None = Field(default=None, examples=["Welcome address by organizers"])
    order_index: int = Field(default=0, examples=[0])


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
    timeline: list[TimelineItemRead]
    sponsors: list[dict]
    prize_pool: dict
    contact: dict


class MaterialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_name: str
    file_url: str
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


class AnnouncementCreate(BaseModel):
    title: str = Field(examples=["Lunch is served"])
    body: str = Field(examples=["Food trucks are open at the main hall until 2pm."])


class AnnouncementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    body: str
    posted_by: uuid.UUID
    posted_at: datetime
