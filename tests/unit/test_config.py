import pytest

from zendesk_mcp_ro.config import ConfigurationError, Settings, get_settings


def test_settings_created_with_required_vars(mock_env):
    settings = Settings()
    assert settings.zendesk_email == "test@example.com"
    assert settings.zendesk_subdomain == "test-company"


def test_settings_defaults(mock_env):
    settings = Settings()
    assert settings.environment == "production"
    assert settings.log_level == "INFO"
    assert settings.zendesk_timeout == 30
    assert settings.zendesk_max_retries == 3


def test_settings_token_masked(mock_env):
    settings = Settings()
    assert "secret-token" not in repr(settings)
    assert "secret-token" not in str(settings)


def test_get_settings_raises_on_missing_var(monkeypatch):
    monkeypatch.delenv("ZENDESK_EMAIL", raising=False)
    monkeypatch.delenv("ZENDESK_TOKEN", raising=False)
    monkeypatch.delenv("ZENDESK_SUBDOMAIN", raising=False)
    with pytest.raises(
        ConfigurationError, match="ZENDESK_EMAIL|ZENDESK_TOKEN|ZENDESK_SUBDOMAIN"
    ):
        get_settings()


def test_get_settings_returns_settings_instance(mock_env):
    settings = get_settings()
    assert isinstance(settings, Settings)
