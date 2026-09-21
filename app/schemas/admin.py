import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.event import TimelineStatus
from app.schemas.profile import ProfileRead
from app.schemas.team import ApprovalStatus, TeamStatus


class ImportRow(BaseModel):
    row_number: int = Field(description="1-based row number in the uploaded sheet")
    name: str | None
    email: str | None
    student_staff_id: str | None
    reference_id: str | None = None
    university_name: str | None = None
    technical_skills: str | None = None
    preferred_role: str | None = None
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
                            "reference_id": "P0001",
                            "status": "ok",
                            "issues": [],
                        },
                        {
                            "row_number": 3,
                            "name": "Ben Tan",
                            "email": "aisyah@student.edu.my",
                            "student_staff_id": "A123457",
                            "reference_id": "P0002",
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
    reference_id: str | None = Field(default=None, examples=["P0001"])
    university_name: str | None = Field(default=None, examples=["Universiti Malaya"])
    technical_skills: str | None = Field(default=None, examples=["React, Python"])
    preferred_role: str | None = Field(default=None, examples=["Frontend"])


class ImportConfirmRequest(BaseModel):
    rows: list[ImportConfirmRowIn] = Field(
        description="Rows to create, as returned by the import preview (ok rows)"
    )


class ImportConfirmResponse(BaseModel):
    created: int = Field(description="Accounts created — each was sent an invite email")
    skipped: int
    invite_failed: int = Field(
        default=0,
        description=(
            "Rows whose Supabase invite call failed — included in skipped_rows "
            "with the reason; no account was created for them"
        ),
    )
    skipped_rows: list[ImportRow] = Field(
        default_factory=list, description="Rows skipped on confirm with reasons"
    )


class AdminParticipantsResponse(BaseModel):
    count: int = Field(description="Current number of participant accounts")
    cap: int = Field(examples=[150])
    remaining: int
    participants: list[ProfileRead]


class AdminChangeEmailRequest(BaseModel):
    new_email: str = Field(
        min_length=3,
        examples=["corrected.address@student.edu.my"],
        description="Replaces the participant's email immediately (no confirmation link)",
    )


class ResetPasswordResponse(BaseModel):
    participant_id: uuid.UUID
    temporary_password: str = Field(
        description=(
            "Give this to the participant. Set via Supabase Auth's admin API with "
            "the email force-confirmed, so it works even when their inbox doesn't; "
            "first_login forces a change on next login."
        )
    )


class AdminTeamRead(BaseModel):
    id: uuid.UUID
    name: str
    reference_id: str | None
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
    team_reference_id: str | None
    team_name: str
    round: int
    github_url: str | None
    infographic_url: str | None
    pitch_deck_url: str | None
    submitted_at: datetime
    updated_at: datetime


class DeadlineUpdate(BaseModel):
    round: Literal[1, 2] = Field(default=1, description="Which round's deadline to set")
    submission_deadline_at: datetime = Field(
        examples=["2026-09-13T12:00:00+08:00"]
    )


class TeamFormationDeadlineUpdate(BaseModel):
    team_formation_deadline_at: datetime = Field(examples=["2026-09-12T12:00:00+08:00"])


class EventSettingsRead(BaseModel):
    countdown_at: datetime | None
    countdown_description: str | None
    submission_deadline_at: datetime | None
    round2_submission_deadline_at: datetime | None
    team_formation_deadline_at: datetime | None
    updated_at: datetime


class AuditLogRead(BaseModel):
    id: uuid.UUID
    admin_id: uuid.UUID
    admin_name: str | None
    action: str
    target_table: str | None
    target_id: uuid.UUID | None
    details: str | None
    created_at: datetime


class TimelineImportRow(BaseModel):
    row_number: int = Field(description="1-based row number in the uploaded sheet")
    bootcamp_name: str | None
    date_label: str | None
    time_session: str | None
    session_type: str | None
    speaker_name: str | None
    speaker_bio: str | None
    organization: str | None
    session_description: str | None
    speaker_photo_url: str | None
    status: str | None
    remarks: str | None
    order_index: int
    row_status: Literal["ok", "flagged"]
    issues: list[str] = Field(default_factory=list)


class TimelineImportPreviewResponse(BaseModel):
    rows: list[TimelineImportRow]
    ok_count: int
    flagged_count: int


class TimelineImportConfirmRowIn(BaseModel):
    bootcamp_name: str
    date_label: str
    time_session: str
    session_type: str
    speaker_name: str | None = None
    speaker_bio: str | None = None
    organization: str | None = None
    session_description: str | None = None
    speaker_photo_url: str | None = None
    status: TimelineStatus = "TBD"
    remarks: str | None = None
    order_index: int = 0


class TimelineImportConfirmRequest(BaseModel):
    rows: list[TimelineImportConfirmRowIn] = Field(
        description=(
            "Rows to write, as returned by the import preview (ok rows). Replaces "
            "the entire timeline, same as PATCH /admin/event/timeline."
        )
    )


class TimelineImportConfirmResponse(BaseModel):
    created: int
