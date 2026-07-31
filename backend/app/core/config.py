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

    refresh_token_expire_days: int = Field(
        default=7,
        gt=0,
        alias="REFRESH_TOKEN_EXPIRE_DAYS",
    )

    frontend_origin: str = Field(
        default="http://localhost:5173",
        alias="FRONTEND_ORIGIN",
    )

    trusted_hosts: str = Field(
        default="localhost,127.0.0.1,testserver",
        alias="TRUSTED_HOSTS",
    )

    @property
    def trusted_host_list(self) -> list[str]:
        return [
            host.strip()
            for host in self.trusted_hosts.split(",")
            if host.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
