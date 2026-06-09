import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ.setdefault("SMTP_HOST", "smtp.yandex.ru")
os.environ.setdefault("SMTP_PORT", "465")
os.environ.setdefault("SMTP_USER", "test@example.com")
os.environ.setdefault("SMTP_PASSWORD", "test_password")
os.environ.setdefault("SMTP_FROM_EMAIL", "noreply@fishing.com")
os.environ.setdefault("SMTP_FROM_NAME", "FishMap")
os.environ.setdefault("EMAIL_SERVICE_API_KEY", "test-api-key-for-testing-min-32-chars")

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def api_key():
    return "test-api-key-for-testing-min-32-chars"


@pytest.fixture
def api_headers(api_key):
    return {"X-API-Key": api_key}
