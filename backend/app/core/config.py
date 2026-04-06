from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend 根目录（容器内即 /app）。用绝对路径读 .env；本地 uv run 读文件，Docker 中由 compose env_file 注入环境变量
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_DOTENV_PATH = _BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_DOTENV_PATH if _DOTENV_PATH.is_file() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_query_path: Path = Path.home() / ".db_query"
    openai_api_key: str | None = None
    # 不设则走 SDK 默认 https://api.openai.com/v1；可填兼容 OpenAI 的代理或网关 Base URL
    openai_base_url: str | None = None
    # Chat Completions model id；第三方网关常限制可用模型，需与 OPENAI_BASE_URL 文档一致
    openai_model: str = "gpt-4o-mini"

    @field_validator("openai_model", mode="before")
    @classmethod
    def empty_openai_model_as_default(cls, v: object) -> object:
        if v is None or (isinstance(v, str) and not v.strip()):
            return "gpt-4o-mini"
        return str(v).strip()

    @field_validator("openai_base_url", mode="before")
    @classmethod
    def empty_openai_base_url_as_none(cls, v: object) -> object:
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return str(v).strip().rstrip("/")


def get_settings() -> Settings:
    return Settings()
