import pytest

from zendesk_mcp_ro.client import ZendeskClient
from zendesk_mcp_ro.config import ConfigurationError, get_settings
from zendesk_mcp_ro.server import _create_app


async def test_create_app_returns_mcp_and_client(settings):
    mcp, client = _create_app(settings)
    assert client is not None
    assert isinstance(client, ZendeskClient)
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "get_ticket" in tool_names
    assert "get_user" in tool_names
    assert "get_organization" in tool_names
    assert "list_satisfaction_ratings" in tool_names


def test_get_settings_raises_configuration_error_when_env_missing(monkeypatch):
    monkeypatch.delenv("ZENDESK_EMAIL", raising=False)
    monkeypatch.delenv("ZENDESK_TOKEN", raising=False)
    monkeypatch.delenv("ZENDESK_SUBDOMAIN", raising=False)
    with pytest.raises(ConfigurationError, match="ZENDESK_EMAIL"):
        get_settings()


def test_create_app_debug_off_in_production(settings):
    _, client = _create_app(settings)
    assert isinstance(client, ZendeskClient)


async def test_create_app_with_development_environment(mock_env, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    from zendesk_mcp_ro.config import Settings

    dev_settings = Settings()
    mcp, client = _create_app(dev_settings)
    assert isinstance(client, ZendeskClient)
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "get_ticket" in tool_names
