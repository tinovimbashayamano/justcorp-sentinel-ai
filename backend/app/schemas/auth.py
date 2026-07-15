from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from backend.app.models.user import UserRole


class UserCreateRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[A-Za-z0-9_.-]+$",
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=12,
        max_length=128,
    )

    full_name: str | None = Field(
        default=None,
        max_length=150,
    )

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        checks = {
            "uppercase letter": any(char.isupper() for char in value),
            "lowercase letter": any(char.islower() for char in value),
            "number": any(char.isdigit() for char in value),
            "special character": any(
                not char.isalnum() for char in value
            ),
        }

        missing = [
            requirement
            for requirement, passed in checks.items()
            if not passed
        ]

        if missing:
            raise ValueError(
                "Password must contain at least one "
                + ", ".join(missing)
                + "."
            )

        return value


class UserLoginRequest(BaseModel):
    username_or_email: str = Field(
        ...,
        min_length=3,
        max_length=255,
    )

    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    full_name: str | None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class TokenPayload(BaseModel):
    sub: str
    role: UserRole
    exp: int
    iat: int
    type: str
