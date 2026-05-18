import pytest

from zendesk_mcp_ro.client import ZendeskClient
from zendesk_mcp_ro.config import Settings


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("ZENDESK_EMAIL", "test@example.com")
    monkeypatch.setenv("ZENDESK_TOKEN", "secret-token")
    monkeypatch.setenv("ZENDESK_SUBDOMAIN", "test-company")


@pytest.fixture
def settings(mock_env):
    return Settings()


@pytest.fixture
def zendesk_client(settings):
    return ZendeskClient(settings)
