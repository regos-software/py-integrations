from pydantic_settings import BaseSettings
from pydantic import AliasChoices, Field, field_validator


class Settings(BaseSettings):
    environment: str = "dev"
    debug: bool = True
    api_token: str = ""
    integration_url: str = "https://integration.regos.uz"
    domain_url: str = Field(
        default="",
        validation_alias=AliasChoices("domain_url", "DOMAIN_URL"),
    )
    proxy_integration_url: str = ""
    integration_rps: int = 2
    integration_burst: int = 30
    integration_429_retry_attempts: int = 3
    integration_429_base_delay_sec: float = 1.0
    integration_429_max_delay_sec: float = 30.0
    integration_429_cooldown_ttl_sec: int = 120
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
    redis_socket_timeout: float = 10.0
    redis_socket_connect_timeout: float = 5.0
    mariadb_enabled: bool = False
    mariadb_host: str = "host"
    mariadb_port: int = 3306
    mariadb_database: str = ""
    mariadb_user: str = ""
    mariadb_password: str = ""
    mariadb_pool_min_size: int = 1
    mariadb_pool_max_size: int = 10
    mariadb_connect_timeout: int = 10
    telegram_api_base_url: str = "https://api.telegram.org"
    telegram_webhook_refresh_ttl: int = 86400
    telegram_update_mode: str = "webhook"
    telegram_notification_stream_workers: int = 2
    telegram_notification_stream_batch_size: int = 50
    telegram_notification_stream_maxlen: int = 100000
    telegram_notification_send_concurrency: int = 20
    telegram_notification_chat_min_interval_sec: float = 1.0
    telegram_notification_flood_retry_attempts: int = 3
    telegram_notification_flood_extra_delay_sec: float = 0.5
    telegram_notification_operating_cash_cache_ttl: int = 3600
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
    telegram_business_webhook_refresh_ttl: int = 86400
    telegram_business_update_mode: str = "webhook"
    telegram_business_crm_channel_stream_workers: int = 2
    telegram_business_crm_channel_stream_batch_size: int = 50
    telegram_business_crm_channel_stream_maxlen: int = 100000
    telegram_business_crm_channel_send_concurrency: int = 20
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
    edo_fakturauz_stream_ttl: int = 86400
    edo_fakturauz_token_cache_ttl: int = 240
    edo_didox_stream_workers: int = 2
    edo_didox_stream_batch_size: int = 20
    edo_didox_stream_maxlen: int = 100000
    edo_didox_stream_retry_limit: int = 3
    edo_didox_stream_ttl: int = 86400
    edo_didox_token_cache_ttl: int = 21000
    didox_partner_token: str = Field(
        default="",
        validation_alias=AliasChoices("didox_partner_token", "DIDOX_PARTNER_TOKEN"),
    )
    didox_base_url: str = Field(
        default="https://api-partners.didox.uz",
        validation_alias=AliasChoices("didox_base_url", "DIDOX_BASE_URL"),
    )
    didox_document_types: str = Field(
        default="002,005,008,023",
        validation_alias=AliasChoices("didox_document_types", "DIDOX_DOCUMENT_TYPES"),
    )
    marketplace_external_timeout: int = 60
    marketplace_unload_page_size: int = 250
    marketplace_cache_ttl: int = 300
    marketplace_lock_ttl: int = 30
    marketplace_lock_wait_timeout: float = 5.0
    marketplace_order_dedupe_ttl: int = 86400
    marketplace_toserver_lock_ttl: int = 3600
    marketplace_toserver_stream_workers: int = 1
    marketplace_toserver_stream_batch_size: int = 10
    marketplace_toserver_stream_maxlen: int = 10000
    marketplace_toserver_stream_ttl: int = 86400
    marketplace_toserver_disable_schedule_after_auth_errors: int = 3
    marketplace_toserver_auth_error_ttl: int = 3600
    bank_ipak_yuli_stream_workers: int = 1
    bank_ipak_yuli_stream_batch_size: int = 10
    bank_ipak_yuli_stream_maxlen: int = 10000
    bank_ipak_yuli_stream_ttl: int = 86400
    instagram_app_id: str = ""
    instagram_app_secret: str = ""
    instagram_redirect_uri: str = ""
    instagram_webhook_verify_token: str = ""
    instagram_graph_version: str = "v25.0"
    meta_leadgen_app_id: str = ""
    meta_leadgen_app_secret: str = ""
    meta_leadgen_redirect_uri: str = ""
    meta_leadgen_webhook_verify_token: str = ""
    meta_leadgen_graph_version: str = "v25.0"
    chatgpt_regos_openai_api_key: str = Field(
        default="",
        validation_alias="CHATGPT_REGOS_OPENAI_API_KEY",
    )
    chatgpt_regos_openai_model: str = Field(
        default="gpt-5.6-terra",
        validation_alias="CHATGPT_REGOS_OPENAI_MODEL",
    )
    chatgpt_regos_temperature: float = Field(
        default=0.2,
        validation_alias="CHATGPT_REGOS_TEMPERATURE",
    )
    chatgpt_regos_max_tool_rounds: int = Field(
        default=5,
        validation_alias="CHATGPT_REGOS_MAX_TOOL_ROUNDS",
    )
    chatgpt_regos_max_output_tokens: int = Field(
        default=1200,
        validation_alias="CHATGPT_REGOS_MAX_OUTPUT_TOKENS",
    )
    chatgpt_regos_confirmation_ttl_sec: int = Field(
        default=900,
        validation_alias="CHATGPT_REGOS_CONFIRMATION_TTL_SEC",
    )
    chatgpt_regos_parent_origin: str = Field(
        default="https://regos.online",
        validation_alias="CHATGPT_REGOS_PARENT_ORIGIN",
    )
    chatgpt_regos_debug_token: str = Field(
        default="",
        validation_alias="CHATGPT_REGOS_DEBUG_TOKEN",
    )
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
