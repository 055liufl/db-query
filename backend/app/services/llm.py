from __future__ import annotations

from openai import APIError, APITimeoutError, AsyncOpenAI, OpenAIError, RateLimitError

from app.core.config import get_settings
from app.services.metadata import parse_cached_metadata
from app.storage import sqlite as sqlite_storage


def _strip_code_fence(text: str) -> str:
    t = text.strip()
    if not t.startswith("```"):
        return t
    lines = t.split("\n")
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


async def generate_select_sql(connection_name: str, user_prompt: str) -> str:
    row = sqlite_storage.get_metadata_row(connection_name)
    if row is None:
        msg = "metadata_not_found"
        raise LookupError(msg)

    meta = parse_cached_metadata(row["metadata_json"])
    settings = get_settings()
    if not settings.openai_api_key:
        msg = "llm_unavailable"
        raise RuntimeError(msg)

    meta_json = meta.model_dump_json(by_alias=True)
    system = (
        "你是 PostgreSQL SQL 专家。下面 JSON 是数据库表结构（camelCase 字段名）。\n"
        "规则：\n"
        "1. 只输出一条 SELECT 语句，不要 Markdown、不要解释。\n"
        "2. 使用标准 PostgreSQL 语法。\n"
        f"\nSchema JSON:\n{meta_json}"
    )
    client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=30.0)
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt.strip()},
            ],
            temperature=0,
        )
    except (APITimeoutError, APIError, RateLimitError, OpenAIError) as e:
        msg = "llm_unavailable"
        raise RuntimeError(msg) from e

    raw = (resp.choices[0].message.content or "").strip()
    if not raw:
        msg = "llm_unavailable"
        raise RuntimeError(msg)
    return _strip_code_fence(raw)
