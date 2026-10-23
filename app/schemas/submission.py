import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# The 5 fixed challenge domains a team tags their submission with — shown
# as a dropdown in the participant Projects page, before the Canvas link.
DOMAIN_OPTIONS = (
    "Predictive Infrastructure & Energy Analytics",
    "Smart Mobility & Citizen-Centric AI",
    "E-Commerce & Consumer Intelligence",
    "Intelligent Transit & Urban Mobility",
    "Global Edu-Tech & Talent Ecosystems",
)
Domain = Literal[
    "Predictive Infrastructure & Energy Analytics",
    "Smart Mobility & Citizen-Centric AI",
    "E-Commerce & Consumer Intelligence",
    "Intelligent Transit & Urban Mobility",
    "Global Edu-Tech & Talent Ecosystems",
]


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
    domain: Domain | None = Field(
        default=None,
        description="One of the 5 fixed challenge domains",
        examples=["Smart Mobility & Citizen-Centric AI"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "github_url": "https://github.com/neon-nebula/lumina-project",
                    "infographic_url": "https://drive.google.com/file/d/abc123/view",
                    "pitch_deck_url": "https://drive.google.com/file/d/def456/view",
                    "domain": "Smart Mobility & Citizen-Centric AI",
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
    domain: str | None
    submitted_by: uuid.UUID | None
    submitted_at: datetime
    updated_at: datetime
