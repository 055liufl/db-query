from __future__ import annotations

from datetime import datetime

import asyncpg
from fastapi import APIRouter, HTTPException, Query, Response, status

from app.models.db_connection import DbConnectionPutRequest, DbConnectionResponse
from app.models.metadata import DbMetadataResponse
from app.models.query import NaturalQueryRequest, NaturalQueryResult, QueryRequest, QueryResult
from app.services import connection as connection_service
from app.services import llm as llm_service
from app.services import metadata as metadata_service
from app.services import query as query_service
from app.storage import sqlite as sqlite_storage

router = APIRouter()


def _parse_dt(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def _row_to_connection(row: dict) -> DbConnectionResponse:
    return DbConnectionResponse(
        name=row["name"],
        url=row["url"],
        created_at=_parse_dt(row["created_at"]),
        updated_at=_parse_dt(row["updated_at"]),
    )


def _http_error(status_code: int, error: str, message: str, detail: str | None = None) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"error": error, "message": message, "detail": detail})


@router.get("/dbs", response_model=list[DbConnectionResponse])
async def list_dbs() -> list[DbConnectionResponse]:
    rows = sqlite_storage.list_connections()
    return [_row_to_connection(r) for r in rows]


@router.put("/dbs/{name}")
async def put_db(name: str, body: DbConnectionPutRequest, response: Response) -> DbConnectionResponse:
    try:
        connection_service.validate_connection_name(name)
        connection_service.validate_db_url(body.url)
        await connection_service.test_connection(body.url)
    except ValueError as e:
        raise _http_error(status.HTTP_400_BAD_REQUEST, "invalid_request", str(e)) from e
    except (OSError, asyncpg.PostgresError, Exception) as e:
        if isinstance(e, (OSError, asyncpg.PostgresError)):
            raise _http_error(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "connection_failed",
                "无法连接到数据库，请检查连接 URL 是否正确",
                str(e),
            ) from e
        # aiomysql errors
        raise _http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "connection_failed",
            "无法连接到数据库，请检查连接 URL 是否正确",
            str(e),
        ) from e

    existed = sqlite_storage.connection_exists(name)
    if existed:
        old = sqlite_storage.get_connection(name)
        if old is not None and old["url"] != body.url:
            sqlite_storage.delete_metadata(name)
    try:
        row = sqlite_storage.upsert_connection(name, body.url, is_new=not existed)
    except Exception as e:  # noqa: BLE001
        raise _http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "storage_error",
            "保存连接信息失败",
            str(e),
        ) from e

    response.status_code = status.HTTP_201_CREATED if not existed else status.HTTP_200_OK
    return _row_to_connection(row)


@router.delete("/dbs/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_db(name: str) -> None:
    try:
        connection_service.validate_connection_name(name)
    except ValueError as e:
        raise _http_error(status.HTTP_400_BAD_REQUEST, "invalid_request", str(e)) from e
    if not sqlite_storage.connection_exists(name):
        raise _http_error(
            status.HTTP_404_NOT_FOUND,
            "connection_not_found",
            f"未找到名为 '{name}' 的数据库连接",
        )
    sqlite_storage.delete_connection(name)


@router.get("/dbs/{name}", response_model=DbMetadataResponse)
async def get_db_metadata(
    name: str,
    refresh: bool = Query(False),
) -> DbMetadataResponse:
    try:
        connection_service.validate_connection_name(name)
    except ValueError as e:
        raise _http_error(status.HTTP_400_BAD_REQUEST, "invalid_request", str(e)) from e

    row = sqlite_storage.get_connection(name)
    if row is None:
        raise _http_error(status.HTTP_404_NOT_FOUND, "connection_not_found", f"未找到名为 '{name}' 的数据库连接")

    url = row["url"]

    if not refresh:
        cached = sqlite_storage.get_metadata_row(name)
        if cached is not None:
            return metadata_service.parse_cached_metadata(cached["metadata_json"])

    try:
        meta = await metadata_service.fetch_metadata(url)
    except (OSError, asyncpg.PostgresError) as e:
        raise _http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "connection_failed",
            "无法连接到数据库以获取元数据",
            str(e),
        ) from e
    except Exception as e:
        raise _http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "connection_failed",
            "无法连接到数据库以获取元数据",
            str(e),
        ) from e

    meta = meta.model_copy(update={"connection_name": name})
    sqlite_storage.save_metadata(name, meta.model_dump_json(by_alias=True))
    return meta


@router.post("/dbs/{name}/query", response_model=QueryResult)
async def post_query(name: str, body: QueryRequest) -> QueryResult:
    try:
        connection_service.validate_connection_name(name)
    except ValueError as e:
        raise _http_error(status.HTTP_400_BAD_REQUEST, "invalid_request", str(e)) from e

    row = sqlite_storage.get_connection(name)
    if row is None:
        raise _http_error(status.HTTP_404_NOT_FOUND, "connection_not_found", f"未找到名为 '{name}' 的数据库连接")

    url = row["url"]
    try:
        return await query_service.execute_select(url, body.sql)
    except ValueError as e:
        raise _http_error(status.HTTP_400_BAD_REQUEST, "invalid_sql", str(e)) from e
    except (OSError, asyncpg.PostgresError) as e:
        raise _http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "query_failed",
            "执行查询失败",
            str(e),
        ) from e
    except Exception as e:
        raise _http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "query_failed",
            "执行查询失败",
            str(e),
        ) from e


@router.post("/dbs/{name}/query/natural", response_model=NaturalQueryResult)
async def post_natural_query(name: str, body: NaturalQueryRequest) -> NaturalQueryResult:
    try:
        connection_service.validate_connection_name(name)
    except ValueError as e:
        raise _http_error(status.HTTP_400_BAD_REQUEST, "invalid_request", str(e)) from e

    row = sqlite_storage.get_connection(name)
    if row is None:
        raise _http_error(status.HTTP_404_NOT_FOUND, "connection_not_found", f"未找到名为 '{name}' 的数据库连接")

    try:
        sql = await llm_service.generate_select_sql(name, body.prompt)
        return NaturalQueryResult(generated_sql=sql)
    except LookupError:
        raise _http_error(
            status.HTTP_404_NOT_FOUND,
            "metadata_not_found",
            "尚未加载该数据库的元数据，请先访问 GET /api/v1/dbs/{name} 获取元数据",
        ) from None
    except llm_service.NaturalQueryUnusableError as e:
        raise _http_error(
            status.HTTP_400_BAD_REQUEST,
            "natural_query_unusable",
            "无法理解该查询描述，请尝试更具体的表述",
            e.detail,
        ) from None
    except llm_service.LlmUnavailableError as e:
        raise _http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "llm_unavailable",
            "AI 服务暂时不可用，请稍后重试或手动编写 SQL",
            e.public_detail,
        ) from e
    except RuntimeError as e:
        raise _http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "natural_query_failed",
            "自然语言生成失败",
            str(e),
        ) from e
    except Exception as e:
        raise _http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "natural_query_failed",
            "自然语言生成失败",
            str(e),
        ) from e
