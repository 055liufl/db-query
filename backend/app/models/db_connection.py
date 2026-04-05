from datetime import datetime

from pydantic import Field

from app.models import AppBaseModel


class DbConnectionPutRequest(AppBaseModel):
    url: str = Field(..., description="PostgreSQL connection URL")


class DbConnectionResponse(AppBaseModel):
    name: str
    url: str
    created_at: datetime
    updated_at: datetime
