import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    student_staff_id: str
    role: Literal["participant", "admin"]
    first_login: bool
    created_at: datetime


class ParticipantListItem(BaseModel):
    id: uuid.UUID
    name: str
    student_staff_id: str
    status: Literal["no_team", "in_team"] = Field(
        description="Whether the participant currently belongs to a team"
    )
    team_name: str | None = None
