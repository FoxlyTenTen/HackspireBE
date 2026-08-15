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
    username: str | None
    email_verified: bool
    reference_id: str | None
    university_name: str | None
    technical_skills: str | None
    preferred_role: str | None
    created_at: datetime


class ProfileUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    university_name: str | None = Field(default=None, max_length=200)
    technical_skills: str | None = Field(default=None, max_length=500)
    preferred_role: str | None = Field(default=None, max_length=100)


class ParticipantListItem(BaseModel):
    id: uuid.UUID
    name: str
    username: str | None
    reference_id: str | None
    technical_skills: str | None
    preferred_role: str | None
    status: Literal["no_team", "in_team"] = Field(
        description="Whether the participant currently belongs to a team"
    )
    team_name: str | None = None
