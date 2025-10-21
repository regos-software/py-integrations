from pydantic_settings import BaseSettings


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

    oauth_client_id: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
