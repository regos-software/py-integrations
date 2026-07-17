from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from config.settings import settings as app_settings
from core.redis import (
    redis_ops,
    redis_error_contains,
    redis_expire_if_due,
    redis_sadd_with_ttl,
    redis_stream_add_with_ttl,
    redis_stream_ack_delete,
    redis_stream_group_create_with_ttl,
    redis_ttl_seconds,
)

from .config import MetaLeadgenCrmChannelConfig
from .models import json_dumps, json_loads, now_ts, to_int


_REDIS_TTL_TOUCH_TS: Dict[str, int] = {}


def redis_enabled() -> bool:
    return bool(app_settings.redis_enabled and redis_ops)


class MetaLeadgenRedisState:
    @staticmethod
    def key(*parts: Any) -> str:
        tokens = [str(item).strip() for item in parts if str(item or "").strip()]
        return f"{MetaLeadgenCrmChannelConfig.REDIS_PREFIX}{':'.join(tokens)}"

    @classmethod
    def settings_cache_key(cls, connected_integration_id: str) -> str:
        return cls.key("settings", connected_integration_id)

    @classmethod
    def ci_active_cache_key(cls, connected_integration_id: str) -> str:
        return cls.key("ci_active", connected_integration_id)

    @classmethod
    def page_ci_key(cls, page_id: str) -> str:
        return cls.key("map", "page_ci", page_id)

    @classmethod
    def active_ci_ids_key(cls) -> str:
        return cls.key("active_ci_ids")

    @classmethod
    def stream_key(cls, connected_integration_id: str) -> str:
        return cls.key("stream", connected_integration_id)

    @classmethod
    def dlq_stream_key(cls, connected_integration_id: str) -> str:
        return cls.key("stream", "dlq", connected_integration_id)

    @classmethod
    def worker_heartbeat_key(cls, connected_integration_id: str) -> str:
        return cls.key("worker", "heartbeat", connected_integration_id)

    @classmethod
    def field_ready_key(cls, connected_integration_id: str) -> str:
        return cls.key("field_ready", connected_integration_id)

    @classmethod
    def mapping_ready_key(cls, connected_integration_id: str, digest: str) -> str:
        return cls.key("mapping_ready", connected_integration_id, digest)

    @classmethod
    def lock_key(cls, connected_integration_id: str, identity: str) -> str:
        return cls.key("lock", connected_integration_id, identity)

    @classmethod
    def dedupe_key(cls, connected_integration_id: str, identity: str) -> str:
        return cls.key("dedupe", connected_integration_id, identity)

    @staticmethod
    def active_ci_ids_ttl() -> int:
        return redis_ttl_seconds(MetaLeadgenCrmChannelConfig.ACTIVE_CI_IDS_TTL_SEC)

    @staticmethod
    async def get(key: str) -> Optional[str]:
        if not redis_enabled():
            return None
        return await redis_ops.get(key)

    @staticmethod
    async def set(key: str, value: str, ttl_sec: int, min_ttl_sec: int = 60) -> None:
        if not redis_enabled():
            return
        ttl = max(to_int(ttl_sec, min_ttl_sec) or min_ttl_sec, min_ttl_sec)
        await redis_ops.set(key, value, ex=ttl)

    @staticmethod
    async def set_nx(key: str, value: str, ttl_sec: int, min_ttl_sec: int = 60) -> bool:
        if not redis_enabled():
            return False
        ttl = max(to_int(ttl_sec, min_ttl_sec) or min_ttl_sec, min_ttl_sec)
        return bool(await redis_ops.set(key, value, ex=ttl, nx=True))

    @staticmethod
    async def delete(*keys: str) -> None:
        if not redis_enabled():
            return
        rows = [str(key).strip() for key in keys if str(key or "").strip()]
        if rows:
            await redis_ops.delete(*rows)

    @classmethod
    async def set_json(cls, key: str, payload: Dict[str, Any], ttl_sec: int) -> None:
        await cls.set(key, json_dumps(payload), ttl_sec)

    @classmethod
    async def get_json(cls, key: str) -> Optional[Dict[str, Any]]:
        raw = await cls.get(key)
        if not raw:
            return None
        try:
            parsed = json_loads(raw)
        except Exception:
            return None
        return parsed if isinstance(parsed, dict) else None

    @classmethod
    async def mark_ci_active(cls, connected_integration_id: str) -> None:
        if not redis_enabled():
            return
        ci = str(connected_integration_id or "").strip()
        if not ci:
            return
        await redis_sadd_with_ttl(cls.active_ci_ids_key(), ci, cls.active_ci_ids_ttl())
        _REDIS_TTL_TOUCH_TS[cls.active_ci_ids_key()] = now_ts()

    @classmethod
    async def mark_ci_inactive(cls, connected_integration_id: str) -> None:
        if not redis_enabled():
            return
        ci = str(connected_integration_id or "").strip()
        if ci:
            await redis_ops.srem(cls.active_ci_ids_key(), ci)

    @classmethod
    async def touch_active_ci_ids_ttl(cls, *, force: bool = False) -> None:
        if not redis_enabled():
            return
        await redis_expire_if_due(
            cls.active_ci_ids_key(),
            cls.active_ci_ids_ttl(),
            _REDIS_TTL_TOUCH_TS,
            now_ts(),
            min_refresh_sec=60,
            force=force,
        )

    @classmethod
    async def active_ci_ids(cls) -> List[str]:
        if not redis_enabled():
            return []
        raw_ids = await redis_ops.smembers(cls.active_ci_ids_key())
        return sorted(
            str(value or "").strip()
            for value in (raw_ids or set())
            if str(value or "").strip()
        )

    @classmethod
    async def sync_page_index(
        cls,
        connected_integration_id: str,
        page_id: Optional[str],
    ) -> None:
        page = str(page_id or "").strip()
        if page:
            await cls.set(
                cls.page_ci_key(page),
                str(connected_integration_id or "").strip(),
                MetaLeadgenCrmChannelConfig.MAP_TTL_SEC,
            )

    @classmethod
    async def resolve_ci_by_page_id(cls, page_id: str) -> Optional[str]:
        value = await cls.get(cls.page_ci_key(page_id))
        return str(value or "").strip() or None

    @classmethod
    async def set_worker_heartbeat(cls, connected_integration_id: str) -> None:
        if not redis_enabled():
            return
        await redis_ops.setex(
            cls.worker_heartbeat_key(connected_integration_id),
            MetaLeadgenCrmChannelConfig.WORKER_HEARTBEAT_TTL_SEC,
            str(now_ts()),
        )
        await cls.touch_active_ci_ids_ttl()

    @classmethod
    def resolve_stream_ttl(cls) -> int:
        return redis_ttl_seconds(MetaLeadgenCrmChannelConfig.STREAM_TTL_SEC)

    @classmethod
    async def touch_stream_ttl(cls, stream_key: str, *, force: bool = False) -> None:
        if not redis_enabled():
            return
        await redis_expire_if_due(
            stream_key,
            cls.resolve_stream_ttl(),
            _REDIS_TTL_TOUCH_TS,
            now_ts(),
            min_refresh_sec=10,
            force=force,
        )

    @classmethod
    async def ensure_consumer_group(cls, stream_key: str) -> None:
        if not redis_enabled():
            return
        await redis_stream_group_create_with_ttl(
            stream_key,
            MetaLeadgenCrmChannelConfig.STREAM_GROUP,
            ttl_sec=cls.resolve_stream_ttl(),
            touch_ts_by_key=_REDIS_TTL_TOUCH_TS,
            now_ts=now_ts(),
        )

    @classmethod
    async def enqueue(cls, stream_key: str, fields: Dict[str, Any]) -> None:
        if not redis_enabled():
            raise RuntimeError("Redis is not enabled")

        serialized: Dict[str, str] = {}
        for key, value in fields.items():
            if isinstance(value, (dict, list)):
                serialized[str(key)] = json_dumps(value)
            elif value is None:
                serialized[str(key)] = ""
            else:
                serialized[str(key)] = str(value)

        await redis_stream_add_with_ttl(
            stream_key,
            serialized,
            maxlen=MetaLeadgenCrmChannelConfig.STREAM_MAXLEN,
            ttl_sec=cls.resolve_stream_ttl(),
            touch_ts_by_key=_REDIS_TTL_TOUCH_TS,
            now_ts=now_ts(),
        )

    @classmethod
    async def ack_stream_entry(cls, stream_key: str, entry_id: str) -> None:
        await redis_stream_ack_delete(stream_key, MetaLeadgenCrmChannelConfig.STREAM_GROUP, entry_id)

    @classmethod
    async def process_claimed_entries(
        cls,
        stream_key: str,
        consumer: str,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        try:
            claimed_raw = await redis_ops.xautoclaim(
                stream_key,
                MetaLeadgenCrmChannelConfig.STREAM_GROUP,
                consumer,
                min_idle_time=MetaLeadgenCrmChannelConfig.STREAM_MIN_IDLE_MS,
                start_id="0-0",
                count=MetaLeadgenCrmChannelConfig.STREAM_BATCH_SIZE,
            )
        except Exception as error:
            if redis_error_contains(error, "NOGROUP"):
                await cls.ensure_consumer_group(stream_key)
                return []
            raise

        entries: List[Tuple[str, Dict[str, Any]]] = []
        if isinstance(claimed_raw, (list, tuple)) and len(claimed_raw) >= 2:
            entries = claimed_raw[1] or []
        return [
            (str(entry_id), fields if isinstance(fields, dict) else {})
            for entry_id, fields in entries
        ]

    @staticmethod
    def stream_entry_attempt(fields: Dict[str, Any]) -> int:
        return max(to_int(fields.get("attempt"), 0) or 0, 0)

    @staticmethod
    def decode_stream_payload(raw: Any) -> Dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        try:
            payload = json_loads(str(raw or ""))
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    @classmethod
    async def acquire_lock(cls, lock_key: str, ttl_sec: int) -> Optional[str]:
        import uuid

        token = uuid.uuid4().hex
        if await cls.set_nx(lock_key, token, ttl_sec, 10):
            return token
        return None

    @classmethod
    async def release_lock(cls, lock_key: str, token: Optional[str]) -> None:
        if not token:
            return
        if await cls.get(lock_key) == token:
            await cls.delete(lock_key)
