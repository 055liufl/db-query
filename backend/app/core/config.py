from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    db_query_path: Path = Path.home() / ".db_query"
    openai_api_key: str | None = None


def get_settings() -> Settings:
    return Settings()
