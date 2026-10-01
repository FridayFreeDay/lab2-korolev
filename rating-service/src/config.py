from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = "postgresql+psycopg://program:test@localhost:5432/ratings"
DEFAULT_PORT = 8050
POSTGRES_SCHEME_PREFIXES = ("postgres://", "postgresql://")
PSYCOPG_SCHEME = "postgresql+psycopg://"


def normalize_database_url(url: str) -> str:
    """Приводит URL со схемой `postgres://` к драйверу psycopg3."""
    for prefix in POSTGRES_SCHEME_PREFIXES:
        if url.startswith(prefix):
            return PSYCOPG_SCHEME + url[len(prefix):]
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = DEFAULT_DATABASE_URL
    port: int = DEFAULT_PORT

    @field_validator("database_url")
    @classmethod
    def _normalize(cls, value: str) -> str:
        return normalize_database_url(value)


settings = Settings()
