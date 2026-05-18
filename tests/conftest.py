import pytest


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("ZENDESK_EMAIL", "test@example.com")
    monkeypatch.setenv("ZENDESK_TOKEN", "secret-token")
    monkeypatch.setenv("ZENDESK_SUBDOMAIN", "test-company")
