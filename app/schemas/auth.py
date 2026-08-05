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
    jwt: str = Field(examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."])
    first_login: bool = Field(
        description="If true, the client must call /auth/change-password before anything else",
        examples=[True],
    )
    role: Literal["participant", "admin"] = Field(
        description="Account role, so the client can route to the right area",
        examples=["participant"],
    )


class ChangePasswordRequest(BaseModel):
    new_password: str = Field(min_length=8, examples=["S3cure-new-pass!"])
