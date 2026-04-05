from typing import Any

from pydantic import Field

from app.models import AppBaseModel


class QueryRequest(AppBaseModel):
    sql: str


class QueryColumn(AppBaseModel):
    name: str
    data_type: str


class QueryResult(AppBaseModel):
    sql: str
    columns: list[QueryColumn]
    rows: list[dict[str, Any]]
    row_count: int
    truncated: bool
    elapsed_ms: int


class NaturalQueryRequest(AppBaseModel):
    prompt: str = Field(..., min_length=1)


class NaturalQueryResult(AppBaseModel):
    generated_sql: str


class ErrorResponse(AppBaseModel):
    error: str
    message: str
    detail: str | None = None
