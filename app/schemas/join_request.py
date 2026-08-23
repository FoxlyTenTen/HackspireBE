import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class JoinRequestRead(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    team_name: str
    participant_id: uuid.UUID
    participant_name: str
    status: Literal["pending", "approved", "rejected"]
    initiated_by: Literal["participant", "leader"]
    created_at: datetime
    responded_at: datetime | None


class JoinRequestRespond(BaseModel):
    decision: Literal["approve", "reject"] = Field(examples=["approve"])

    model_config = {"json_schema_extra": {"examples": [{"decision": "approve"}]}}


class InviteCreate(BaseModel):
    participant_id: uuid.UUID = Field(
        description="Profile ID of an unassigned participant to invite"
    )
