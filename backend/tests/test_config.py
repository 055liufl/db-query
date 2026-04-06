from __future__ import annotations

import pytest
from app.core.config import Settings

# Pass openai_base_url / openai_model explicitly so tests do not depend on developer backend/.env.


def test_openai_model_empty_string_uses_default() -> None:
    s = Settings(
        openai_api_key="sk-test",
        openai_base_url=None,
        openai_model="",
    )
    assert s.openai_model == "gpt-4o-mini"


def test_openai_base_url_strips_trailing_slash() -> None:
    s = Settings(
        openai_api_key="sk-test",
        openai_base_url="https://example.com/v1/",
        openai_model="gpt-4o-mini",
    )
    assert s.openai_base_url == "https://example.com/v1"


def test_openai_base_url_empty_becomes_none() -> None:
    s = Settings(
        openai_api_key="sk-test",
        openai_base_url="",
        openai_model="gpt-4o-mini",
    )
    assert s.openai_base_url is None


@pytest.mark.parametrize(
    ("raw", "want"),
    [
        ("gpt-3.4-mini", "gpt-3.4-mini"),
        ("  gpt-4o  ", "gpt-4o"),
    ],
)
def test_openai_model_strips(raw: str, want: str) -> None:
    s = Settings(
        openai_api_key="sk-test",
        openai_base_url=None,
        openai_model=raw,
    )
    assert s.openai_model == want
