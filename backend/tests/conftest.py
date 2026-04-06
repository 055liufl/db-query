from __future__ import annotations

from pathlib import Path

import pytest
from starlette.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DB_QUERY_PATH", str(tmp_path))
    from app.main import app

    with TestClient(app) as tc:
        yield tc
