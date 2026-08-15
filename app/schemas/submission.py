import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SubmissionWrite(BaseModel):
    github_url: str | None = Field(
        default=None,
        description="Must be a well-formed GitHub link",
        examples=["https://github.com/neon-nebula/lumina-project"],
    )
    gdrive_url: str | None = Field(
        default=None,
        description="Single Drive link containing both the infographic and pitch deck",
        examples=["https://drive.google.com/drive/folders/abc123"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "github_url": "https://github.com/neon-nebula/lumina-project",
                    "gdrive_url": "https://drive.google.com/drive/folders/abc123",
                }
            ]
        }
    }

    @model_validator(mode="after")
    def at_least_one_link(self) -> "SubmissionWrite":
        if not self.github_url and not self.gdrive_url:
            raise ValueError("At least one of github_url or gdrive_url must be provided")
        return self


class SubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    team_id: uuid.UUID
    github_url: str | None
    gdrive_url: str | None
    submitted_by: uuid.UUID | None
    submitted_at: datetime
    updated_at: datetime
