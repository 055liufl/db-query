from __future__ import annotations

from datetime import UTC, datetime

from app.models.metadata import DbMetadataResponse
from app.services.metadata import parse_cached_metadata


def test_parse_cached_metadata_round_trip() -> None:
    at = datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)
    meta = DbMetadataResponse(connection_name="pg", tables=[], cached_at=at)
    blob = meta.model_dump_json(by_alias=True)
    out = parse_cached_metadata(blob)
    assert out.connection_name == "pg"
    assert out.tables == []
