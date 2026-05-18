from pydantic import SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigurationError(Exception):
    pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    zendesk_email: str
    zendesk_token: SecretStr
    zendesk_subdomain: str
    zendesk_timeout: int = 30
    zendesk_max_retries: int = 3
    log_level: str = "INFO"
    environment: str = "production"


def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        missing = [
            str(err["loc"][0]).upper() for err in e.errors() if err["type"] == "missing"
        ]
        if missing:
            raise ConfigurationError(
                f"Missing required environment variable(s): {', '.join(missing)}"
            ) from e
        raise ConfigurationError(str(e)) from e
