import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.core.security import validate_password_strength


class UserRegisterRequest(BaseModel):
    """
    Schema for user and organization registration request.
    """

    full_name: str = Field(..., min_length=1, max_length=255, description="Full name of user")
    email: EmailStr = Field(..., description="Valid user email address")
    password: str = Field(..., min_length=8, max_length=128, description="Strong password")
    organization_name: str = Field(..., min_length=1, max_length=255, description="Name of company or organization")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        return validate_password_strength(v)

    @field_validator("full_name", "organization_name")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Field cannot be empty or only whitespace.")
            return trimmed
        return v


class LoginRequest(BaseModel):
    """
    JSON login request payload.
    """

    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., min_length=1, description="Password")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class OrganizationResponse(BaseModel):
    """
    Safe organization information.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    created_at: datetime


class UserResponse(BaseModel):
    """
    Safe user information without password hashes.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """
    Response schema returning access token and safe user details.
    """

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class RegisterResponse(BaseModel):
    """
    Response schema returning newly created user and organization details.
    """

    message: str = "User and organization registered successfully"
    user: UserResponse
    organization: OrganizationResponse
    access_token: Optional[str] = None
    token_type: str = "bearer"


class UserProfileResponse(BaseModel):
    """
    Response schema for authenticated user profile including organization context.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    organization: OrganizationResponse
