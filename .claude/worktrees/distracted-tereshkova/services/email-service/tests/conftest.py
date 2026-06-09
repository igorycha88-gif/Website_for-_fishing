import pytest


@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.yandex.ru")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USER", "test@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "test_password")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "test@example.com")
    monkeypatch.setenv("SMTP_FROM_NAME", "FishMap")
