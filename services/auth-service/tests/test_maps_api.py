import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.database import get_redis


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_redis():
    return AsyncMock()


def test_maps_health_check_success(client, mock_redis):
    mock_redis.ping.return_value = True
    app.dependency_overrides[get_redis] = lambda: mock_redis

    try:
        response = client.get("/api/v1/maps/health")

        assert response.status_code == 200
        assert response.json()["service"] == "maps"
        assert response.json()["redis"] == "ok"
        assert response.json()["status"] == "healthy"
    finally:
        app.dependency_overrides.clear()


def test_maps_health_check_redis_error(client, mock_redis):
    mock_redis.ping.side_effect = Exception("Redis connection error")
    app.dependency_overrides[get_redis] = lambda: mock_redis

    try:
        response = client.get("/api/v1/maps/health")

        assert response.status_code == 200
        assert response.json()["service"] == "maps"
        assert response.json()["redis"] == "error"
        assert response.json()["status"] == "degraded"
    finally:
        app.dependency_overrides.clear()
