from pydantic import BaseModel, Field

_ERROR_DESCRIPTIONS = {
    400: "Bad request — invalid input or business rule violated",
    401: "Missing or invalid bearer token",
    403: "Authenticated but not allowed to perform this action",
    404: "Resource not found",
    409: "Conflict with current state (e.g. team locked or full, deadline passed)",
    422: "Request body failed validation",
    503: "Supabase Auth is not configured or unreachable",
}


class ErrorResponse(BaseModel):
    """Standard error shape returned by every 4xx response."""

    error: str = Field(examples=["Team is locked and cannot be modified"])


class MessageResponse(BaseModel):
    message: str = Field(examples=["Password changed successfully"])


def error_responses(*codes: int) -> dict:
    """Build the `responses=` dict referencing ErrorResponse for the given codes."""
    return {
        code: {"model": ErrorResponse, "description": _ERROR_DESCRIPTIONS[code]}
        for code in codes
    }
