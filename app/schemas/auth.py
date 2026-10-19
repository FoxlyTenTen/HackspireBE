from typing import Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(
        description="Email address or student/staff ID",
        examples=["A123456"],
    )
    password: str = Field(examples=["A123456"])

    model_config = {
        "json_schema_extra": {
            "examples": [{"username": "A123456", "password": "A123456"}]
        }
    }


class LoginResponse(BaseModel):
    jwt: str = Field(
        description="Supabase access token — send as the bearer token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    refresh_token: str = Field(
        description="Exchange via POST /auth/refresh when the access token expires"
    )
    first_login: bool = Field(
        description="If true, the client must call /auth/change-password before anything else",
        examples=[False],
    )
    role: Literal["participant", "admin"] = Field(
        description="Account role, so the client can route to the right area",
        examples=["participant"],
    )


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    jwt: str
    refresh_token: str = Field(description="Refresh tokens rotate — store the new one")


class VerifyOtpRequest(BaseModel):
    token_hash: str = Field(description="The `token_hash` query param from a Supabase email link")
    type: str = Field(examples=["invite", "recovery", "email_change"])


class VerifyOtpResponse(BaseModel):
    jwt: str
    refresh_token: str
    type: str = Field(description="Echoes the verified link type so the client knows what to show")


class ForgotPasswordRequest(BaseModel):
    email: str = Field(examples=["aisyah@student.edu.my"])


class ChangePasswordRequest(BaseModel):
    new_password: str = Field(min_length=8, examples=["S3cure-new-pass!"])


class ChangePasswordResponse(BaseModel):
    jwt: str = Field(description="Fresh access token — the caller's old one is now revoked")
    refresh_token: str = Field(description="Fresh refresh token, paired with `jwt`")
    message: str
