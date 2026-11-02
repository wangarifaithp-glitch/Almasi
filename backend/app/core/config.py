from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    app_name: str = "ALMASI API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    app_base_url: str = "http://localhost:5173"
    auth_secret_key: str | None = None
    resend_api_key: str | None = None
    resend_from_email: str | None = None

    model_config = SettingsConfigDict(
        env_file=BACKEND_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        configured_origins = [
            origin.strip().rstrip("/")
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]
        app_origin = self.app_base_url.strip().rstrip("/")
        if app_origin and app_origin not in configured_origins:
            configured_origins.append(app_origin)
        return configured_origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
