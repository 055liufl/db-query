from datetime import datetime

from pydantic import Field

from app.models import AppBaseModel


class ColumnInfo(AppBaseModel):
    name: str
    data_type: str = Field(..., description="PostgreSQL data type name")
    is_nullable: bool
    column_default: str | None = None


class TableInfo(AppBaseModel):
    schema_name: str
    table_name: str
    table_type: str = Field(..., description="BASE TABLE or VIEW")
    columns: list[ColumnInfo]


class DbMetadataResponse(AppBaseModel):
    connection_name: str
    tables: list[TableInfo]
    cached_at: datetime
