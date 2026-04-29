from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from config.settings import settings

redis_client = None

if settings.redis_enabled:
    redis_client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password or None,
        decode_responses=True,
    )


def redis_error_contains(error: Any, marker: str) -> bool:
    return str(marker).upper() in str(error or "").upper()


def redis_ttl_seconds(ttl_sec: Any, *, min_ttl_sec: int = 60) -> int:
    return max(int(ttl_sec), min_ttl_sec)


def redis_ttl_refresh_due(
    touch_ts_by_key: Dict[str, int],
    key: str,
    ttl_sec: int,
    now_ts: int,
    *,
    min_refresh_sec: int,
    force: bool = False,
) -> bool:
    refresh_interval_sec = min(3600, max(min_refresh_sec, ttl_sec // 4))
    last_touch_ts = int(touch_ts_by_key.get(key) or 0)
    return force or now_ts - last_touch_ts >= refresh_interval_sec


def _require_redis_client():
    if redis_client is None:
        raise RuntimeError("Redis is not enabled")
    return redis_client


async def redis_expire_if_due(
    key: str,
    ttl_sec: int,
    touch_ts_by_key: Dict[str, int],
    now_ts: int,
    *,
    min_refresh_sec: int,
    force: bool = False,
) -> bool:
    if not redis_ttl_refresh_due(
        touch_ts_by_key,
        key,
        ttl_sec,
        now_ts,
        min_refresh_sec=min_refresh_sec,
        force=force,
    ):
        return False
    await _require_redis_client().expire(key, ttl_sec)
    touch_ts_by_key[key] = now_ts
    return True


async def redis_sadd_with_ttl(key: str, value: str, ttl_sec: int) -> None:
    async with _require_redis_client().pipeline(transaction=True) as pipe:
        await pipe.sadd(key, value)
        await pipe.expire(key, ttl_sec)
        await pipe.execute()


async def redis_incr_with_ttl(key: str, ttl_sec: int) -> int:
    async with _require_redis_client().pipeline(transaction=True) as pipe:
        await pipe.incr(key)
        await pipe.expire(key, ttl_sec)
        value, _ = await pipe.execute()
    return int(value or 0)


async def redis_zadd_with_ttl(
    key: str,
    value: str,
    score: Any,
    ttl_sec: int,
    *,
    max_items: Optional[int] = None,
    prune_max_score: Optional[Any] = None,
) -> None:
    async with _require_redis_client().pipeline(transaction=True) as pipe:
        if prune_max_score is not None:
            await pipe.zremrangebyscore(key, "-inf", prune_max_score)
        await pipe.zadd(key, {value: score})
        if max_items and max_items > 0:
            await pipe.zremrangebyrank(key, 0, -(int(max_items) + 1))
        await pipe.expire(key, ttl_sec)
        await pipe.execute()


async def redis_zrangebyscore_with_ttl(
    key: str,
    min_score: Any,
    max_score: Any,
    ttl_sec: int,
    *,
    max_items: Optional[int] = None,
    prune_max_score: Optional[Any] = None,
) -> List[str]:
    result_index = 0
    async with _require_redis_client().pipeline(transaction=True) as pipe:
        if prune_max_score is not None:
            await pipe.zremrangebyscore(key, "-inf", prune_max_score)
            result_index += 1
        if max_items and max_items > 0:
            await pipe.zrangebyscore(key, min_score, max_score, start=0, num=int(max_items))
        else:
            await pipe.zrangebyscore(key, min_score, max_score)
        await pipe.expire(key, ttl_sec)
        results = await pipe.execute()
    values = results[result_index] if len(results) > result_index else []
    return list(values) if isinstance(values, list) else []


async def redis_stream_add_with_ttl(
    stream_key: str,
    fields: Dict[str, str],
    *,
    maxlen: int,
    ttl_sec: int,
    touch_ts_by_key: Dict[str, int],
    now_ts: int,
    min_refresh_sec: int = 10,
) -> None:
    client = _require_redis_client()
    should_touch = redis_ttl_refresh_due(
        touch_ts_by_key,
        stream_key,
        ttl_sec,
        now_ts,
        min_refresh_sec=min_refresh_sec,
    )
    if not should_touch:
        await client.xadd(stream_key, fields, maxlen=maxlen, approximate=True)
        return
    async with client.pipeline(transaction=True) as pipe:
        await pipe.xadd(stream_key, fields, maxlen=maxlen, approximate=True)
        await pipe.expire(stream_key, ttl_sec)
        await pipe.execute()
    touch_ts_by_key[stream_key] = now_ts


async def redis_stream_group_create_with_ttl(
    stream_key: str,
    group_name: str,
    *,
    ttl_sec: int,
    touch_ts_by_key: Dict[str, int],
    now_ts: int,
) -> None:
    async with _require_redis_client().pipeline(transaction=True) as pipe:
        await pipe.xgroup_create(stream_key, group_name, id="0-0", mkstream=True)
        await pipe.expire(stream_key, ttl_sec)
        results = await pipe.execute(raise_on_error=False)
    group_result = results[0] if results else None
    if isinstance(group_result, Exception) and not redis_error_contains(
        group_result,
        "BUSYGROUP",
    ):
        raise group_result
    touch_ts_by_key[stream_key] = now_ts
