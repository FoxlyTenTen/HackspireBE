import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SubmissionWrite(BaseModel):
    github_url: str | None = Field(
        default=None,
        description="Must be a well-formed GitHub link",
        examples=["https://github.com/neon-nebula/lumina-project"],
    )
    infographic_url: str | None = Field(
        default=None,
        description="Link to the team's infographic",
        examples=["https://drive.google.com/file/d/abc123/view"],
    )
    pitch_deck_url: str | None = Field(
        default=None,
        description="Link to the team's pitch deck",
        examples=["https://drive.google.com/file/d/def456/view"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "github_url": "https://github.com/neon-nebula/lumina-project",
                    "infographic_url": "https://drive.google.com/file/d/abc123/view",
                    "pitch_deck_url": "https://drive.google.com/file/d/def456/view",
                }
            ]
        }
    }

    @model_validator(mode="after")
    def at_least_one_link(self) -> "SubmissionWrite":
        if not self.github_url and not self.infographic_url and not self.pitch_deck_url:
            raise ValueError(
                "At least one of github_url, infographic_url, or pitch_deck_url must be provided"
            )
        return self


class SubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    team_id: uuid.UUID
    round: int
    github_url: str | None
    infographic_url: str | None
    pitch_deck_url: str | None
    submitted_by: uuid.UUID | None
    submitted_at: datetime
    updated_at: datetime
