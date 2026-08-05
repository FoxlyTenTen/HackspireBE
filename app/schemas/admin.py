import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.profile import ProfileRead
from app.schemas.team import ApprovalStatus, TeamStatus


class ImportRow(BaseModel):
    row_number: int = Field(description="1-based row number in the uploaded sheet")
    name: str | None
    email: str | None
    student_staff_id: str | None
    status: Literal["ok", "flagged"]
    issues: list[str] = Field(
        default_factory=list,
        description="Per-row problems, e.g. duplicate email or missing fields",
    )


class ImportPreviewResponse(BaseModel):
    rows: list[ImportRow]
    ok_count: int
    flagged_count: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "rows": [
                        {
                            "row_number": 2,
                            "name": "Aisyah Rahman",
                            "email": "aisyah@student.edu.my",
                            "student_staff_id": "A123456",
                            "status": "ok",
                            "issues": [],
                        },
                        {
                            "row_number": 3,
                            "name": "Ben Tan",
                            "email": "aisyah@student.edu.my",
                            "student_staff_id": "A123457",
                            "status": "flagged",
                            "issues": ["duplicate email within file"],
                        },
                    ],
                    "ok_count": 1,
                    "flagged_count": 1,
                }
            ]
        }
    }


class ImportConfirmRowIn(BaseModel):
    name: str = Field(examples=["Aisyah Rahman"])
    email: str = Field(examples=["aisyah@student.edu.my"])
    student_staff_id: str = Field(examples=["A123456"])


class ImportConfirmRequest(BaseModel):
    rows: list[ImportConfirmRowIn] = Field(
        description="Rows to create, as returned by the import preview (ok rows)"
    )


class ImportConfirmResponse(BaseModel):
    created: int
    skipped: int
    skipped_rows: list[ImportRow] = Field(
        default_factory=list, description="Rows skipped on confirm with reasons"
    )


class AdminParticipantsResponse(BaseModel):
    count: int = Field(description="Current number of participant accounts")
    cap: int = Field(examples=[150])
    remaining: int
    participants: list[ProfileRead]


class ResetPasswordResponse(BaseModel):
    participant_id: uuid.UUID
    temporary_password: str = Field(
        description="Give this to the participant; first_login is set so they must change it"
    )


class AdminTeamRead(BaseModel):
    id: uuid.UUID
    name: str
    leader_id: uuid.UUID
    leader_name: str
    member_count: int
    capacity: int
    status: TeamStatus
    approval_status: ApprovalStatus
    admin_note: str | None
    locked: bool
    has_submission: bool
    created_at: datetime


class AdminTeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    capacity: int | None = Field(default=None, ge=1, le=5)
    status: TeamStatus | None = None
    leader_id: uuid.UUID | None = Field(
        default=None, description="Reassign leadership; must be a current member"
    )
    locked: bool | None = Field(
        default=None, description="Explicitly unlock (revert approval) or lock a team"
    )


class AdminRejectRequest(BaseModel):
    note: str | None = Field(
        default=None,
        examples=["Team has only 1 member — merge with another team or recruit more."],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"note": "Team needs at least 3 members before approval."}]
        }
    }


class AdminSubmissionRow(BaseModel):
    team_id: uuid.UUID
    team_name: str
    url: str
    submitted_at: datetime
    updated_at: datetime


class DeadlineUpdate(BaseModel):
    submission_deadline_at: datetime = Field(
        examples=["2026-09-13T12:00:00+08:00"]
    )


class EventSettingsRead(BaseModel):
    countdown_at: datetime | None
    submission_deadline_at: datetime | None
    updated_at: datetime
