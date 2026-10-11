from datetime import datetime

from pydantic import BaseModel, Field

_EMAIL_RE = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class PublicLandingCountdownRead(BaseModel):
    """Minimal, intentionally-public shape — never add fields here without
    checking they're safe to expose with zero authentication from any origin."""

    landing_countdown_at: datetime | None
    landing_countdown_label: str | None


class PublicContactRequest(BaseModel):
    """Landing page 'Help Desk' contact form — zero auth, so every field is
    length-capped and the message is HTML-escaped before it's emailed."""

    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254, pattern=_EMAIL_RE, examples=["jane@student.edu.my"])
    message: str = Field(min_length=1, max_length=2000)
