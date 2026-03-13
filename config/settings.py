from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    environment: str = "dev"
    debug: bool = True
    api_token: str = ""
    integration_url: str = "https://integration.regos.uz"
    integration_rps: int = 2
    integration_burst: int = 50
    service_a_token: str = ""
    log_level: str = "DEBUG"
    redis_enabled: bool = False
    redis_host: str = "host"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = "psw"
    redis_cache_ttl: int = 60
    telegram_update_mode: str = "webhook"

    oauth_endpoint: str = "https://auth.regos.uz/" # oath/token
    oauth_client_id: str = ""
    oauth_secret: str = ""

    @field_validator("debug", mode="before")
    @classmethod
    def _normalize_debug(cls, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return True
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "y", "on", "debug"}:
            return True
        if text in {"0", "false", "no", "n", "off", "release", "prod", "production"}:
            return False
        return value

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value):
        if value is None:
            return "INFO"
        text = str(value).strip().upper()
        if not text:
            return "INFO"
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
        if text == "TRACE":
            return "DEBUG"
        if text in allowed:
            return text
        return "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
