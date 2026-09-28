from datetime import datetime

from pydantic import BaseModel


class PublicLandingCountdownRead(BaseModel):
    """Minimal, intentionally-public shape — never add fields here without
    checking they're safe to expose with zero authentication from any origin."""

    landing_countdown_at: datetime | None
    landing_countdown_label: str | None
