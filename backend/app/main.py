from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.routers import dbs
from app.services.llm import LLM_DNS_RESOLVER, LLM_HTTP_TRANSPORT, close_openai_client
from app.storage import sqlite as sqlite_storage

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    db_file = settings.db_query_path / "db_query.db"
    sqlite_storage.configure(db_file)
    sqlite_storage.init_db()
    yield
    await close_openai_client()


app = FastAPI(title="DB Query API", lifespan=lifespan)


class PrivateNetworkAccessMiddleware(BaseHTTPMiddleware):
    """Chrome: preflight may send Access-Control-Request-Private-Network; answer or fetch fails."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.headers.get("access-control-request-private-network") == "true":
            response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(PrivateNetworkAccessMiddleware)

app.include_router(dbs.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    """Confirm deployed backend includes expected LLM HTTP/DNS stack (llmTransport, llmDns)."""
    return {
        "status": "ok",
        "llmTransport": LLM_HTTP_TRANSPORT,
        "llmDns": LLM_DNS_RESOLVER,
    }


@app.exception_handler(ResponseValidationError)
async def response_validation_handler(
    _request: Request, exc: ResponseValidationError
) -> JSONResponse:
    """Avoid plain-text 500 when response_model validation fails."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "response_validation_error",
            "message": "API 返回数据与模型约定不一致",
            "detail": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Any unhandled error becomes JSON so Swagger shows body instead of text/plain."""
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "服务器内部错误",
            "detail": f"{type(exc).__name__}: {exc!s}",
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "message" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "error", "message": str(exc.detail), "detail": None},
    )
