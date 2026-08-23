import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TeamStatus = Literal["open", "looking_for_teammates", "closed", "full"]
ApprovalStatus = Literal["pending", "approved", "rejected"]


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100, examples=["Neon Nebula"])

    model_config = {"json_schema_extra": {"examples": [{"name": "Neon Nebula"}]}}


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    capacity: int | None = Field(
        default=None, ge=1, le=5, description="Max 5; cannot go below current member count"
    )
    status: Literal["open", "looking_for_teammates", "closed"] | None = Field(
        default=None, description="'full' is set automatically when the team fills up"
    )


class TeamMemberRead(BaseModel):
    participant_id: uuid.UUID
    name: str
    student_staff_id: str
    is_leader: bool
    joined_at: datetime


class TeamListItem(BaseModel):
    id: uuid.UUID
    name: str
    reference_id: str | None
    member_count: int
    capacity: int
    status: TeamStatus


class TeamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    reference_id: str | None
    leader_id: uuid.UUID
    capacity: int
    status: TeamStatus
    approval_status: ApprovalStatus
    admin_note: str | None
    locked: bool
    created_at: datetime
    member_count: int
    members: list[TeamMemberRead]
