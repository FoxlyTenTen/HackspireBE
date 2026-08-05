import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubmissionWrite(BaseModel):
    url: str = Field(
        description="Must be a well-formed GitHub or Google Drive link",
        examples=["https://github.com/neon-nebula/lumina-project"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"url": "https://github.com/neon-nebula/lumina-project"}]
        }
    }


class SubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    team_id: uuid.UUID
    url: str
    submitted_at: datetime
    updated_at: datetime
