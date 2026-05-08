from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    environment: str = "dev"
    debug: bool = True
    api_token: str = ""
    integration_url: str = "https://integration.regos.uz"
    proxy_integration_url: str = ""
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
    telegram_webhook_refresh_ttl: int = 86400
    telegram_update_mode: str = "webhook"
    telegram_notification_stream_workers: int = 2
    telegram_notification_stream_batch_size: int = 50
    telegram_notification_stream_maxlen: int = 100000
    telegram_notification_send_concurrency: int = 20
    telegram_orders_stream_workers: int = 2
    telegram_orders_stream_batch_size: int = 50
    telegram_orders_stream_maxlen: int = 100000
    telegram_orders_send_concurrency: int = 20
    telegram_crm_channel_stream_workers: int = 2
    telegram_crm_channel_stream_batch_size: int = 50
    telegram_crm_channel_stream_maxlen: int = 100000
    telegram_crm_channel_send_concurrency: int = 20
    instagram_app_id: str = ""
    instagram_app_secret: str = ""
    instagram_redirect_uri: str = ""
    instagram_webhook_verify_token: str = ""
    meta_leadgen_app_id: str = ""
    meta_leadgen_app_secret: str = ""
    meta_leadgen_redirect_uri: str = ""
    meta_leadgen_webhook_verify_token: str = ""
    meta_leadgen_graph_version: str = "v20.0"

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
