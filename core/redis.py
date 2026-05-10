import asyncio
import json
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

import redis.asyncio as redis

from config.settings import settings

_redis_client = None
_LOCAL_JSON_CACHE: Dict[str, Tuple[float, Any]] = {}
_LOCAL_JSON_CACHE_LOCK = asyncio.Lock()
_LOCAL_JSON_CACHE_MAX_ITEMS = 10000

if settings.redis_enabled:
    _redis_client = redis.Redis(
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
    if _redis_client is None:
        raise RuntimeError("Redis is not enabled")
    return _redis_client


def redis_is_enabled() -> bool:
    return _redis_client is not None


class RedisOps:
    """Thin Redis command facade so integrations never import the raw client."""

    def __bool__(self) -> bool:
        return redis_is_enabled()

    def pipeline(self, *args: Any, **kwargs: Any):
        return _require_redis_client().pipeline(*args, **kwargs)

    def lock(self, *args: Any, **kwargs: Any):
        return _require_redis_client().lock(*args, **kwargs)

    async def get(self, *args: Any, **kwargs: Any):
        return await _require_redis_client().get(*args, **kwargs)

    async def set(self, *args: Any, **kwargs: Any):
        return await _require_redis_client().set(*args, **kwargs)

    async def setex(self, *args: Any, **kwargs: Any):
        return await _require_redis_client().setex(*args, **kwargs)

    async def delete(self, *args: Any, **kwargs: Any):
        return await _require_redis_client().delete(*args, **kwargs)

    async def exists(self, *args: Any, **kwargs: Any):
        return await _require_redis_client().exists(*args, **kwargs)

    async def expire(self, *args: Any, **kwargs: Any):
        return await _require_redis_client().expire(*args, **kwargs)

    async def eval(self, *args: Any, **kwargs: Any):
        return await _require_redis_client().eval(*args, **kwargs)

    async def smembers(self, *args: Any, **kwargs: Any):
        return await _require_redis_client().smembers(*args, **kwargs)

    async def srem(self, *args: Any, **kwargs: Any):
        return await _require_redis_client().srem(*args, **kwargs)

    async def mget(self, *args: Any, **kwargs: Any):
        return await _require_redis_client().mget(*args, **kwargs)

    async def incr(self, *args: Any, **kwargs: Any):
        return await _require_redis_client().incr(*args, **kwargs)

    async def xack(self, *args: Any, **kwargs: Any):
        return await _require_redis_client().xack(*args, **kwargs)

    async def xdel(self, *args: Any, **kwargs: Any):
        return await _require_redis_client().xdel(*args, **kwargs)

    async def xautoclaim(self, *args: Any, **kwargs: Any):
        return await _require_redis_client().xautoclaim(*args, **kwargs)

    async def xreadgroup(self, *args: Any, **kwargs: Any):
        return await _require_redis_client().xreadgroup(*args, **kwargs)


redis_ops = RedisOps()


def redis_make_key(*parts: Any) -> str:
    return ":".join(str(part).strip(":") for part in parts if str(part or "").strip(":"))


def _prune_local_json_cache(now: float) -> None:
    if len(_LOCAL_JSON_CACHE) <= _LOCAL_JSON_CACHE_MAX_ITEMS:
        return
    expired_keys = [key for key, (expires_at, _) in _LOCAL_JSON_CACHE.items() if expires_at <= now]
    for key in expired_keys:
        _LOCAL_JSON_CACHE.pop(key, None)
    if len(_LOCAL_JSON_CACHE) <= _LOCAL_JSON_CACHE_MAX_ITEMS:
        return
    overflow = len(_LOCAL_JSON_CACHE) - _LOCAL_JSON_CACHE_MAX_ITEMS
    for key in sorted(_LOCAL_JSON_CACHE, key=lambda item: _LOCAL_JSON_CACHE[item][0])[:overflow]:
        _LOCAL_JSON_CACHE.pop(key, None)


async def redis_get_json(key: str, *, local_ttl_sec: int = 5) -> Optional[Any]:
    now = time.monotonic()
    if local_ttl_sec > 0:
        async with _LOCAL_JSON_CACHE_LOCK:
            _prune_local_json_cache(now)
            cached = _LOCAL_JSON_CACHE.get(key)
            if cached and cached[0] > now:
                return cached[1]

    raw = await _require_redis_client().get(key)
    if not raw:
        return None
    value = json.loads(raw)
    if local_ttl_sec > 0:
        async with _LOCAL_JSON_CACHE_LOCK:
            _LOCAL_JSON_CACHE[key] = (now + local_ttl_sec, value)
    return value


async def redis_set_json(
    key: str,
    value: Any,
    ttl_sec: int,
    *,
    local_ttl_sec: int = 5,
) -> None:
    ttl = max(int(ttl_sec or 1), 1)
    await _require_redis_client().set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
    if local_ttl_sec > 0:
        async with _LOCAL_JSON_CACHE_LOCK:
            _prune_local_json_cache(time.monotonic())
            _LOCAL_JSON_CACHE[key] = (time.monotonic() + local_ttl_sec, value)


async def redis_delete_keys(*keys: str) -> None:
    valid = [key for key in keys if key]
    if not valid:
        return
    async with _LOCAL_JSON_CACHE_LOCK:
        for key in valid:
            _LOCAL_JSON_CACHE.pop(key, None)
    await _require_redis_client().delete(*valid)


async def redis_acquire_lock(
    key: str,
    ttl_sec: int,
    *,
    wait_timeout_sec: float = 0,
    retry_delay_sec: float = 0.05,
) -> Optional[str]:
    client = _require_redis_client()
    token = uuid.uuid4().hex
    deadline = time.monotonic() + max(float(wait_timeout_sec or 0), 0)
    ttl = max(int(ttl_sec or 1), 1)
    while True:
        if await client.set(key, token, ex=ttl, nx=True):
            return token
        if time.monotonic() >= deadline:
            return None
        await asyncio.sleep(max(float(retry_delay_sec or 0.05), 0.01))


async def redis_release_lock(key: str, token: Optional[str]) -> None:
    if not key or not token:
        return
    script = (
        "if redis.call('get', KEYS[1]) == ARGV[1] "
        "then return redis.call('del', KEYS[1]) else return 0 end"
    )
    await _require_redis_client().eval(script, 1, key, token)


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


async def redis_stream_ack_delete(stream_key: str, group_name: str, entry_id: str) -> None:
    """Finalize a Redis stream queue item without keeping processed payloads."""
    if not stream_key or not group_name or not entry_id:
        return
    async with _require_redis_client().pipeline(transaction=True) as pipe:
        await pipe.xack(stream_key, group_name, entry_id)
        await pipe.xdel(stream_key, entry_id)
        await pipe.execute()
