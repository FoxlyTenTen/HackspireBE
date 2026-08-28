import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: Literal[
        "join_request",
        "join_response",
        "announcement",
        "team_update",
        "round2_open",
        "team_invite",
        "invite_response",
        "broadcast",
    ]
    reference_id: uuid.UUID | None
    message: str
    read: bool
    created_at: datetime


class NotificationBroadcast(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=500,
        examples=["Reminder: submissions close in 1 hour!"],
    )


class NotificationBroadcastResponse(BaseModel):
    recipients: int
