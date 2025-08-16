import redis.asyncio as redis
from config.settings import settings

redis_client = None

if settings.redis_enabled:
    redis_client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password or None,  
        decode_responses=True
    )
