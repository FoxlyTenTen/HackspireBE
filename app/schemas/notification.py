import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: Literal["join_request", "join_response", "announcement", "team_update", "round2_open"]
    reference_id: uuid.UUID | None
    message: str
    read: bool
    created_at: datetime
