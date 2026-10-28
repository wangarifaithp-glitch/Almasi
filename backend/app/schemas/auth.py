from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


def validate_password_strength(password: str) -> str:
    requirements = (
        len(password) >= 8,
        any(character.islower() for character in password),
        any(character.isupper() for character in password),
        any(character.isdigit() for character in password),
        any(not character.isalnum() and not character.isspace() for character in password),
    )
    if not all(requirements):
        raise ValueError(
            "Password must be at least 8 characters and include uppercase, "
            "lowercase, a number, and a special character."
        )
    return password


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterRequest(Credentials):
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be blank.")
        return value

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return validate_password_strength(value)


class LoginRequest(Credentials):
    pass


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=32, max_length=256)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return validate_password_strength(value)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: Literal["learner", "facilitator", "supervisor", "administrator"]
    is_active: bool
    email_verified_at: datetime | None

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str


class WorkspaceAccessResponse(BaseModel):
    role: Literal["learner", "facilitator", "supervisor", "administrator"]
    workspace: Literal["learner", "facilitator", "supervisor", "administrator"]
