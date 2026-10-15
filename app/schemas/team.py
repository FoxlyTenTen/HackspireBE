import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TeamStatus = Literal["open", "looking_for_teammates", "closed", "full"]
ApprovalStatus = Literal["pending", "approved", "rejected"]
# Mirrors ROLE_OPTIONS in lumina-frontend/src/constants/roles.ts.
PreferredRole = Literal[
    "Data Scientist",
    "ML Engineer",
    "Backend Developer",
    "Frontend Developer",
    "UI/UX & Dashboard Designer",
    "Project Manager (PM)",
]


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
    project_title: str | None = Field(default=None, max_length=150)
    preferred_roles: list[PreferredRole] | None = Field(
        default=None, description="Roles the team still needs; replaces the whole list"
    )
    remarks: str | None = Field(default=None, max_length=1000)


class TeamMemberRead(BaseModel):
    participant_id: uuid.UUID
    name: str
    email: str | None = Field(
        default=None,
        description="Only returned to members of the same team and admins; null for everyone else",
    )
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
    project_title: str | None
    preferred_roles: list[str]
    remarks: str | None
    leader_name: str
    leader_email: str = Field(
        description="Shared with every participant on purpose so people browsing teams can contact the leader"
    )


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
    project_title: str | None
    preferred_roles: list[str]
    remarks: str | None
    created_at: datetime
    member_count: int
    members: list[TeamMemberRead]
