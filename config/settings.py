from pydantic_settings import BaseSettings
from pydantic import AliasChoices, Field, field_validator


class Settings(BaseSettings):
    environment: str = "dev"
    debug: bool = True
    api_token: str = ""
    integration_url: str = "https://integration.regos.uz"
    proxy_integration_url: str = ""
    integration_rps: int = 2
    integration_burst: int = 50
    service_a_token: str = ""
    scheduler_hostname: str = Field(
        default="",
        validation_alias=AliasChoices(
            "scheduler_hostname",
            "SCHEDULER_HOSTNAME",
            "SCHEDULER_HOST_NAME",
            "Scheduler_HostName",
        ),
    )
    scheduler_token: str = Field(
        default="",
        validation_alias=AliasChoices(
            "scheduler_token",
            "SCHEDULER_TOKEN",
            "Scheduler_Token",
        ),
    )
    scheduler_timeout: int = 30
    scheduler_verify_ssl: bool = False
    log_level: str = "DEBUG"
    redis_enabled: bool = False
    redis_host: str = "host"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = "psw"
    redis_cache_ttl: int = 60
    mariadb_enabled: bool = False
    mariadb_host: str = "host"
    mariadb_port: int = 3306
    mariadb_database: str = ""
    mariadb_user: str = ""
    mariadb_password: str = ""
    mariadb_pool_min_size: int = 1
    mariadb_pool_max_size: int = 10
    mariadb_connect_timeout: int = 10
    telegram_webhook_refresh_ttl: int = 86400
    telegram_update_mode: str = "webhook"
    telegram_notification_stream_workers: int = 2
    telegram_notification_stream_batch_size: int = 50
    telegram_notification_stream_maxlen: int = 100000
    telegram_notification_send_concurrency: int = 20
    telegram_notification_chat_min_interval_sec: float = 1.0
    telegram_notification_flood_retry_attempts: int = 3
    telegram_notification_flood_extra_delay_sec: float = 0.5
    telegram_orders_stream_workers: int = 2
    telegram_orders_stream_batch_size: int = 50
    telegram_orders_stream_maxlen: int = 100000
    telegram_orders_send_concurrency: int = 20
    telegram_min_quantity_stream_workers: int = 2
    telegram_min_quantity_stream_batch_size: int = 50
    telegram_min_quantity_stream_maxlen: int = 100000
    telegram_min_quantity_stream_retry_limit: int = 3
    telegram_min_quantity_send_concurrency: int = 20
    telegram_crm_channel_stream_workers: int = 2
    telegram_crm_channel_stream_batch_size: int = 50
    telegram_crm_channel_stream_maxlen: int = 100000
    telegram_crm_channel_send_concurrency: int = 20
    asterisk_crm_channel_stream_workers: int = 2
    asterisk_crm_channel_stream_batch_size: int = 50
    asterisk_crm_channel_stream_maxlen: int = 100000
    asterisk_crm_channel_stream_retry_limit: int = 5
    asterisk_crm_channel_event_concurrency: int = 20
    external_chat_crm_channel_stream_workers: int = 2
    external_chat_crm_channel_stream_batch_size: int = 50
    external_chat_crm_channel_stream_maxlen: int = 100000
    external_chat_crm_channel_stream_retry_limit: int = 5
    external_chat_crm_channel_event_concurrency: int = 20
    gpt_crm_chat_assistant_stream_workers: int = 2
    gpt_crm_chat_assistant_stream_batch_size: int = 50
    gpt_crm_chat_assistant_stream_maxlen: int = 100000
    gpt_crm_chat_assistant_stream_retry_limit: int = 5
    gpt_crm_chat_assistant_event_concurrency: int = 20
    instagram_crm_channel_stream_workers: int = 2
    instagram_crm_channel_stream_batch_size: int = 50
    instagram_crm_channel_stream_maxlen: int = 100000
    instagram_crm_channel_stream_retry_limit: int = 3
    edo_fakturauz_stream_workers: int = 2
    edo_fakturauz_stream_batch_size: int = 20
    edo_fakturauz_stream_maxlen: int = 100000
    edo_fakturauz_stream_retry_limit: int = 3
    edo_fakturauz_stream_ttl: int = 604800
    edo_fakturauz_token_cache_ttl: int = 240
    marketplace_external_timeout: int = 60
    marketplace_unload_page_size: int = 250
    marketplace_cache_ttl: int = 300
    marketplace_lock_ttl: int = 30
    marketplace_lock_wait_timeout: float = 5.0
    marketplace_order_dedupe_ttl: int = 86400
    marketplace_toserver_lock_ttl: int = 3600
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
