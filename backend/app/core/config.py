from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(
        default=(
            "postgresql://justcorp_user:justcorp_password"
            "@localhost:5432/justcorp_sentinel_ai"
        ),
        alias="DATABASE_URL",
    )

    jwt_secret_key: str = Field(
        ...,
        min_length=32,
        alias="JWT_SECRET_KEY",
    )

    jwt_algorithm: str = Field(
        default="HS256",
        alias="JWT_ALGORITHM",
    )

    access_token_expire_minutes: int = Field(
        default=30,
        gt=0,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
