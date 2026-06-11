from __future__ import annotations

import asyncio
import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx

from clients.base import ClientBase
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from core.redis import (
    redis_error_contains,
    redis_expire_if_due,
    redis_is_enabled,
    redis_make_key,
    redis_ops,
    redis_stream_ack_delete,
    redis_stream_add_with_ttl,
    redis_stream_group_create_with_ttl,
    redis_ttl_seconds,
)
from schemas.api.chat.chat_message import ChatMessageAddRequest, ChatMessageTypeEnum
from schemas.api.crm.client import Client, ClientEditRequest, ClientGetRequest
from schemas.api.crm.ticket import Ticket, TicketGetRequest, TicketStatusEnum
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingRequest,
)


logger = setup_logger("billing_connector")


BILLING_HTTP_TIMEOUT = 30.0
DEDUPE_TTL_SEC = 300
QUEUE_DEDUPE_TTL_SEC = 10 * 60
STREAM_GROUP = "bcw"
STREAM_TTL_SEC = 24 * 60 * 60
STREAM_MAXLEN = 10000
STREAM_BATCH_SIZE = 10
STREAM_WORKERS = 1
STREAM_READ_BLOCK_MS = 5000
STREAM_MIN_IDLE_MS = 60_000
STREAM_CLAIM_INTERVAL_SEC = 30
STREAM_MAX_RETRIES = 3
MAX_ACTIVE_TICKETS_PER_CLIENT = 200
SUPPORTED_WEBHOOKS = {
    "TicketAdded",
    "ClientEdited",
}
ACTIVE_TICKET_STATUSES = [
    TicketStatusEnum.Open,
    TicketStatusEnum.WaitingClient,
    TicketStatusEnum.WaitingStaff,
]
CLIENT_UPDATE_FIELDS = (
    "name",
    "phone",
    "email",
    "photo_url",
    "description",
)

_INSTANCE_ID = uuid.uuid4().hex[:12]
_STREAM_WORKER_TASKS: Dict[str, asyncio.Task] = {}
_STREAM_WORKER_LOCK = asyncio.Lock()
_STREAM_TTL_TOUCH_TS: Dict[str, int] = {}
_STREAM_GROUP_READY: Set[str] = set()
_STREAM_CLAIM_TS: Dict[str, int] = {}

_ENQUEUE_DEDUPE_LUA = """
local ok = redis.call('set', KEYS[1], '1', 'EX', ARGV[1], 'NX')
if not ok then
  return 0
end
redis.call('xadd', KEYS[2], 'MAXLEN', '~', ARGV[2], '*', unpack(ARGV, 5))
if ARGV[4] == '1' then
  redis.call('expire', KEYS[2], ARGV[3])
end
return 1
"""


@dataclass(frozen=True)
class RuntimeConfig:
    connected_integration_id: str
    billing_client_info_url: str
    billing_bearer_token: str
    billing_message_template: Optional[str] = None


class BillingConnectorError(Exception):
    pass


class _SafeFormatDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + str(key) + "}"


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _optional_text(value: Any) -> Optional[str]:
    text = _text(value)
    return text or None


def _to_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(str(value).strip())
    except Exception:
        return default


def _normalize_settings(rows: Any) -> Dict[str, str]:
    settings: Dict[str, str] = {}
    if not isinstance(rows, list):
        return settings
    for row in rows:
        key = _text(getattr(row, "key", None)).lower()
        if key:
            settings[key] = _text(getattr(row, "value", None))
    return settings


def _setting(settings: Dict[str, str], key: str) -> str:
    return _text(settings.get(key.lower()))


def _payload_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(mode="json", exclude_none=True)
        return dumped if isinstance(dumped, dict) else {}
    return {}


def _lookup(data: Any, *keys: str) -> Any:
    if not isinstance(data, dict):
        return None
    lower_map = {str(key).lower(): value for key, value in data.items()}
    for key in keys:
        if key in data:
            return data[key]
        value = lower_map.get(str(key).lower())
        if value is not None:
            return value
    return None


def _extract_id(payload: Dict[str, Any], *keys: str) -> int:
    value = _lookup(payload, *keys)
    return _to_int(value, 0)


def _drop_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _drop_none(row) for key, row in value.items() if row is not None}
    if isinstance(value, list):
        return [_drop_none(row) for row in value]
    return value


def _stable_hash(payload: Any) -> str:
    dumped = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _json_loads(raw: str) -> Any:
    return json.loads(raw)


def _now_ts() -> int:
    return int(time.time())


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _client_snapshot(client: Client) -> Dict[str, Any]:
    return {
        "id": getattr(client, "id", None),
        "external_id": getattr(client, "external_id", None),
        "name": getattr(client, "name", None),
        "phone": getattr(client, "phone", None),
        "email": getattr(client, "email", None),
    }


def _ticket_snapshot(ticket: Ticket) -> Dict[str, Any]:
    return {
        "id": getattr(ticket, "id", None),
        "status": _text(_enum_value(getattr(ticket, "status", None))),
        "channel_id": getattr(ticket, "channel_id", None),
        "subject": getattr(ticket, "subject", None),
    }


def _normalize_billing_parameters(rows: Any) -> List[Dict[str, str]]:
    if not isinstance(rows, list):
        return []
    result: List[Dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = _text(row.get("key"))
        if not key:
            continue
        result.append(
            {
                "key": key,
                "name": _text(row.get("name"), key),
                "value": _text(row.get("value")),
            }
        )
    return result


def _render_message(template: str, parameters: List[Dict[str, str]]) -> str:
    values = _SafeFormatDict({row["key"]: row["value"] for row in parameters})
    if template:
        try:
            return template.format_map(values).strip()
        except Exception:
            logger.warning("Billing message template rendering failed")
            return template.strip()

    lines = [
        f"{row['name']}: {row['value']}"
        for row in parameters
        if row.get("value")
    ]
    return "\n".join(lines).strip()


def _billing_client_hash_payload(billing_client: Dict[str, Any]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for field in CLIENT_UPDATE_FIELDS:
        if field in billing_client:
            value = _optional_text(billing_client.get(field))
            if value is not None:
                result[field] = value
    return result


def _normalize_webhook_payload(
    action: Optional[str],
    data: Optional[Dict[str, Any]],
    extra: Dict[str, Any],
) -> tuple[Optional[str], Dict[str, Any], Optional[str]]:
    event_id = _text(extra.get("event_id")) or None

    if isinstance(action, str) and action in SUPPORTED_WEBHOOKS:
        if isinstance(data, dict):
            return action, data, event_id
        payload = {
            key: value
            for key, value in extra.items()
            if key not in {"event_id", "connected_integration_id"}
        }
        return action, payload, event_id

    if action == "HandleWebhook":
        payload = data if isinstance(data, dict) else {}
        nested = payload.get("data")
        wrapped_event_id = _text(payload.get("event_id") or event_id) or None
        if isinstance(nested, dict):
            nested_action = nested.get("action")
            nested_data = nested.get("data")
            if isinstance(nested_action, str) and isinstance(nested_data, dict):
                return nested_action, nested_data, wrapped_event_id
        return None, {}, wrapped_event_id

    if isinstance(data, dict):
        nested_action = data.get("action")
        nested_data = data.get("data")
        nested_event_id = _text(data.get("event_id") or event_id) or None
        if isinstance(nested_action, str) and isinstance(nested_data, dict):
            return nested_action, nested_data, nested_event_id

    return None, {}, event_id


class BillingConnectorIntegration(ClientBase):
    integration_key = "billing_connector"

    def __init__(self) -> None:
        self.connected_integration_id: Optional[str] = None

    @classmethod
    def _redis_key(cls, *parts: Any) -> str:
        return redis_make_key(cls.integration_key, *parts)

    @classmethod
    def _require_redis(cls) -> None:
        if not redis_is_enabled():
            raise BillingConnectorError("Redis is required for billing_connector queue")

    @classmethod
    def _stream_key(cls) -> str:
        return cls._redis_key("stream", "events")

    @classmethod
    def _dlq_stream_key(cls) -> str:
        return cls._redis_key("stream", "dlq")

    @classmethod
    def _worker_task_key(cls, worker_index: int) -> str:
        return f"{cls._stream_key()}:{int(worker_index)}"

    @classmethod
    def _queue_dedupe_key(
        cls,
        connected_integration_id: str,
        action: str,
        payload: Dict[str, Any],
        event_id: Optional[str],
    ) -> str:
        raw_event_key = _text(event_id) or _stable_hash({"action": action, "payload": payload})
        event_hash = hashlib.sha256(raw_event_key.encode("utf-8")).hexdigest()[:24]
        return cls._redis_key("queue_dedupe", connected_integration_id, event_hash)

    @classmethod
    def _resolve_stream_ttl(cls) -> int:
        return redis_ttl_seconds(STREAM_TTL_SEC)

    @classmethod
    async def _touch_stream_ttl(cls, stream_key: str, *, force: bool = False) -> None:
        cls._require_redis()
        await redis_expire_if_due(
            stream_key,
            cls._resolve_stream_ttl(),
            _STREAM_TTL_TOUCH_TS,
            _now_ts(),
            min_refresh_sec=10,
            force=force,
        )

    @classmethod
    async def _ensure_consumer_group(cls, stream_key: str, *, force: bool = False) -> None:
        cls._require_redis()
        if not force and stream_key in _STREAM_GROUP_READY:
            return
        await redis_stream_group_create_with_ttl(
            stream_key,
            STREAM_GROUP,
            ttl_sec=cls._resolve_stream_ttl(),
            touch_ts_by_key=_STREAM_TTL_TOUCH_TS,
            now_ts=_now_ts(),
        )
        _STREAM_GROUP_READY.add(stream_key)

    @classmethod
    def _serialize_stream_fields(cls, fields: Dict[str, Any]) -> Dict[str, str]:
        serialized: Dict[str, str] = {}
        for key, value in fields.items():
            if isinstance(value, (dict, list)):
                serialized[str(key)] = _json_dumps(value)
            elif value is None:
                serialized[str(key)] = ""
            else:
                serialized[str(key)] = str(value)
        return serialized

    @classmethod
    def _decode_stream_payload(cls, raw: Any) -> Any:
        if isinstance(raw, (dict, list)):
            return raw
        text = _text(raw)
        if not text:
            return {}
        try:
            return _json_loads(text)
        except Exception:
            return {}

    @classmethod
    async def _enqueue_stream(cls, stream_key: str, fields: Dict[str, Any]) -> None:
        cls._require_redis()
        await redis_stream_add_with_ttl(
            stream_key,
            cls._serialize_stream_fields(fields),
            maxlen=STREAM_MAXLEN,
            ttl_sec=cls._resolve_stream_ttl(),
            touch_ts_by_key=_STREAM_TTL_TOUCH_TS,
            now_ts=_now_ts(),
        )

    @classmethod
    async def _enqueue_stream_deduped(
        cls,
        *,
        stream_key: str,
        dedupe_key: str,
        fields: Dict[str, Any],
    ) -> bool:
        cls._require_redis()
        stream_ttl = cls._resolve_stream_ttl()
        now_ts = _now_ts()
        should_touch = (
            now_ts - int(_STREAM_TTL_TOUCH_TS.get(stream_key) or 0)
            >= min(3600, max(10, stream_ttl // 4))
        )
        serialized = cls._serialize_stream_fields(fields)
        field_args: List[str] = []
        for key, value in serialized.items():
            field_args.extend([key, value])
        queued = await redis_ops.eval(
            _ENQUEUE_DEDUPE_LUA,
            2,
            dedupe_key,
            stream_key,
            str(QUEUE_DEDUPE_TTL_SEC),
            str(STREAM_MAXLEN),
            str(stream_ttl),
            "1" if should_touch else "0",
            *field_args,
        )
        if queued and should_touch:
            _STREAM_TTL_TOUCH_TS[stream_key] = now_ts
        return bool(queued)

    @classmethod
    async def _enqueue_event(
        cls,
        *,
        connected_integration_id: str,
        action: str,
        payload: Dict[str, Any],
        event_id: Optional[str],
        attempt: int = 0,
        last_error: Optional[str] = None,
        dedupe: bool = True,
    ) -> bool:
        await cls._ensure_stream_workers(ensure_groups=False)
        stream_key = cls._stream_key()
        fields = {
            "connected_integration_id": connected_integration_id,
            "action": action,
            "event_id": _text(event_id),
            "payload": payload,
            "attempt": str(max(int(attempt), 0)),
            "enqueued_at": str(_now_ts()),
            "last_error": _text(last_error),
        }
        if not dedupe:
            await cls._enqueue_stream(stream_key, fields)
            return True
        return await cls._enqueue_stream_deduped(
            stream_key=stream_key,
            dedupe_key=cls._queue_dedupe_key(
                connected_integration_id,
                action,
                payload,
                event_id,
            ),
            fields=fields,
        )

    @classmethod
    async def _ensure_stream_workers(cls, *, ensure_groups: bool = True) -> None:
        cls._require_redis()
        stream_key = cls._stream_key()
        if ensure_groups:
            await cls._ensure_consumer_group(stream_key)
        for worker_index in range(STREAM_WORKERS):
            task_key = cls._worker_task_key(worker_index)
            async with _STREAM_WORKER_LOCK:
                task = _STREAM_WORKER_TASKS.get(task_key)
                if task and not task.done():
                    continue
                _STREAM_WORKER_TASKS[task_key] = asyncio.create_task(
                    cls._stream_worker_loop(worker_index),
                    name=f"billing_connector_stream_{worker_index}",
                )

    @classmethod
    async def _ack_stream_entry(cls, stream_key: str, entry_id: str) -> None:
        await redis_stream_ack_delete(stream_key, STREAM_GROUP, entry_id)

    @classmethod
    async def _process_claimed_entries(
        cls,
        stream_key: str,
        consumer: str,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        try:
            claimed_raw = await redis_ops.xautoclaim(
                stream_key,
                STREAM_GROUP,
                consumer,
                min_idle_time=STREAM_MIN_IDLE_MS,
                start_id="0-0",
                count=STREAM_BATCH_SIZE,
            )
        except Exception as error:
            if redis_error_contains(error, "NOGROUP"):
                await cls._ensure_consumer_group(stream_key, force=True)
                return []
            logger.warning("Billing connector stream xautoclaim failed: %s", error)
            return []

        entries: List[Tuple[str, Dict[str, Any]]] = []
        if isinstance(claimed_raw, (list, tuple)) and len(claimed_raw) >= 2:
            entries = claimed_raw[1] or []
        return [
            (str(entry_id), fields if isinstance(fields, dict) else {})
            for entry_id, fields in entries
        ]

    @classmethod
    async def _stream_worker_loop(cls, worker_index: int) -> None:
        stream_key = cls._stream_key()
        task_key = cls._worker_task_key(worker_index)
        consumer = f"{_INSTANCE_ID}:events:{worker_index}"
        logger.info("Billing connector stream worker started: stream=%s", stream_key)
        try:
            await cls._ensure_consumer_group(stream_key)
            while True:
                try:
                    await cls._touch_stream_ttl(stream_key)
                    now_ts = _now_ts()
                    last_claim_ts = int(_STREAM_CLAIM_TS.get(stream_key) or 0)
                    if now_ts - last_claim_ts >= STREAM_CLAIM_INTERVAL_SEC:
                        _STREAM_CLAIM_TS[stream_key] = now_ts
                        claimed_entries = await cls._process_claimed_entries(
                            stream_key,
                            consumer,
                        )
                        for entry_id, fields in claimed_entries:
                            await cls._process_stream_entry(
                                stream_key=stream_key,
                                entry_id=entry_id,
                                fields=fields,
                            )

                    try:
                        records = await redis_ops.xreadgroup(
                            groupname=STREAM_GROUP,
                            consumername=consumer,
                            streams={stream_key: ">"},
                            count=STREAM_BATCH_SIZE,
                            block=STREAM_READ_BLOCK_MS,
                        )
                    except Exception as error:
                        if redis_error_contains(error, "NOGROUP"):
                            await cls._ensure_consumer_group(stream_key, force=True)
                            continue
                        raise

                    for _, entries in records or []:
                        for entry_id, fields in entries or []:
                            await cls._process_stream_entry(
                                stream_key=stream_key,
                                entry_id=str(entry_id),
                                fields=fields if isinstance(fields, dict) else {},
                            )
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    logger.exception("Billing connector stream worker error: %s", error)
                    await asyncio.sleep(2)
        finally:
            async with _STREAM_WORKER_LOCK:
                current = _STREAM_WORKER_TASKS.get(task_key)
                if current is asyncio.current_task():
                    _STREAM_WORKER_TASKS.pop(task_key, None)

    @classmethod
    def _stream_entry_attempt(cls, fields: Dict[str, Any]) -> int:
        return max(_to_int(fields.get("attempt"), 0), 0)

    @classmethod
    def _is_non_retryable_error(cls, error: object) -> bool:
        text = str(error or "")
        return (
            "Missing settings:" in text
            or "billing_auth_failed" in text
            or "connected_integration_id is required" in text
        )

    @classmethod
    async def _process_stream_entry(
        cls,
        *,
        stream_key: str,
        entry_id: str,
        fields: Dict[str, Any],
    ) -> None:
        ci = _text(fields.get("connected_integration_id"))
        action = _text(fields.get("action"))
        event_id = _optional_text(fields.get("event_id"))
        payload = cls._decode_stream_payload(fields.get("payload"))
        if not ci or action not in SUPPORTED_WEBHOOKS or not isinstance(payload, dict):
            logger.warning(
                "Billing connector stream entry has invalid payload: entry_id=%s fields=%s",
                entry_id,
                fields,
            )
            await cls._ack_stream_entry(stream_key, entry_id)
            return

        attempt = cls._stream_entry_attempt(fields)
        worker = cls()
        worker.connected_integration_id = ci
        try:
            result = await worker._process_webhook_event(action, payload, event_id)
            logger.debug(
                "Billing connector stream job processed: "
                "ci=%s action=%s entry_id=%s status=%s",
                ci,
                action,
                entry_id,
                result.get("status") if isinstance(result, dict) else result,
            )
            await cls._ack_stream_entry(stream_key, entry_id)
        except Exception as error:
            if cls._is_non_retryable_error(error):
                logger.warning(
                    "Billing connector stream job skipped: "
                    "ci=%s action=%s entry_id=%s error=%s",
                    ci,
                    action,
                    entry_id,
                    error,
                )
                await cls._ack_stream_entry(stream_key, entry_id)
                return

            next_attempt = attempt + 1
            if next_attempt >= STREAM_MAX_RETRIES:
                dlq_payload = dict(fields)
                dlq_payload["attempt"] = str(next_attempt)
                dlq_payload["source_stream"] = stream_key
                dlq_payload["source_entry_id"] = entry_id
                dlq_payload["failed_at"] = str(_now_ts())
                dlq_payload["error"] = str(error)
                await cls._enqueue_stream(cls._dlq_stream_key(), dlq_payload)
                await cls._ack_stream_entry(stream_key, entry_id)
                logger.error(
                    "Billing connector stream job moved to DLQ: "
                    "ci=%s action=%s entry_id=%s error=%s",
                    ci,
                    action,
                    entry_id,
                    error,
                )
                return

            await cls._enqueue_event(
                connected_integration_id=ci,
                action=action,
                payload=payload,
                event_id=event_id,
                attempt=next_attempt,
                last_error=str(error),
                dedupe=False,
            )
            await cls._ack_stream_entry(stream_key, entry_id)
            logger.warning(
                "Billing connector stream job requeued: "
                "ci=%s action=%s entry_id=%s attempt=%s error=%s",
                ci,
                action,
                entry_id,
                next_attempt,
                error,
            )

    def _ci(self, connected_integration_id: Optional[str] = None) -> str:
        ci = _text(connected_integration_id or self.connected_integration_id)
        if not ci:
            raise BillingConnectorError("connected_integration_id is required")
        return ci

    async def connect(self, **kwargs: Any) -> Dict[str, Any]:
        """Validate billing settings; webhook subscription is configured manually."""
        runtime = await self._load_runtime(
            connected_integration_id=_optional_text(kwargs.get("connected_integration_id"))
        )
        self._require_redis()
        await self._ensure_stream_workers()
        return {
            "status": "connected",
            "integration_key": self.integration_key,
            "billing_client_info_url": runtime.billing_client_info_url,
            "webhooks": sorted(SUPPORTED_WEBHOOKS),
            "queue_enabled": True,
        }

    async def reconnect(self, **kwargs: Any) -> Dict[str, Any]:
        return await self.connect(**kwargs)

    async def disconnect(self, **kwargs: Any) -> Dict[str, Any]:
        _ = kwargs
        return {"status": "disconnected"}

    async def update_settings(
        self,
        settings: Optional[dict] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        _ = settings
        return await self.connect(**kwargs)

    async def handle_external(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """Billing Connector has no external callback endpoint."""
        _ = envelope
        return {"status": "ignored", "reason": "external_endpoint_not_supported"}

    async def handle_webhook(
        self,
        action: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Accept REGOS ticket/client events quickly and process them from Redis Stream."""
        if not self.connected_integration_id:
            return {"status": "error", "description": "connected_integration_id is required"}

        webhook_action, payload, event_id = _normalize_webhook_payload(action, data, kwargs)
        if webhook_action not in SUPPORTED_WEBHOOKS:
            return {"status": "ignored", "reason": f"unsupported_action:{webhook_action}"}

        try:
            queued = await self._enqueue_event(
                connected_integration_id=self._ci(),
                action=webhook_action,
                payload=payload,
                event_id=event_id,
            )
        except BillingConnectorError as error:
            logger.warning(
                "Billing connector enqueue error: ci=%s action=%s error=%s",
                self.connected_integration_id,
                webhook_action,
                error,
            )
            return {"status": "error", "action": webhook_action, "reason": str(error)}
        except Exception as error:
            logger.exception(
                "Billing connector enqueue failed: ci=%s action=%s error=%s",
                self.connected_integration_id,
                webhook_action,
                error,
            )
            return {"status": "error", "action": webhook_action, "reason": "enqueue_failed"}

        return {
            "status": "accepted",
            "action": webhook_action,
            "event_id": event_id,
            "queued": 1 if queued else 0,
            "duplicate": not queued,
        }

    async def _process_webhook_event(
        self,
        webhook_action: str,
        payload: Dict[str, Any],
        event_id: Optional[str],
    ) -> Dict[str, Any]:
        runtime = await self._load_runtime()
        async with RegosAPI(runtime.connected_integration_id) as api:
            if webhook_action == "TicketAdded":
                result = await self._handle_ticket_added(api, runtime, payload)
            else:
                result = await self._handle_client_edited(api, runtime, payload)
        return {
            "status": result.get("status", "processed"),
            "action": webhook_action,
            "event_id": event_id,
            "result": result,
        }

    async def ticket_added(
        self,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Adapter for direct REGOS webhook calls with action=TicketAdded."""
        payload = data if isinstance(data, dict) else dict(kwargs)
        event_id = kwargs.get("event_id")
        return await self.handle_webhook(action="TicketAdded", data=payload, event_id=event_id)

    async def client_edited(
        self,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Adapter for direct REGOS webhook calls with action=ClientEdited."""
        payload = data if isinstance(data, dict) else dict(kwargs)
        event_id = kwargs.get("event_id")
        return await self.handle_webhook(action="ClientEdited", data=payload, event_id=event_id)

    async def _handle_ticket_added(
        self,
        api: RegosAPI,
        runtime: RuntimeConfig,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        ticket_id = _extract_id(payload, "id", "ticket_id")
        if ticket_id <= 0:
            return {"status": "ignored", "reason": "ticket_id_missing"}

        ticket = await self._get_ticket(api, ticket_id)
        if ticket is None:
            return {"status": "ignored", "reason": "ticket_not_found", "ticket_id": ticket_id}
        if not self._is_active_ticket(ticket):
            return {"status": "ignored", "reason": "ticket_closed", "ticket_id": ticket_id}
        client_id = _to_int(getattr(ticket, "client_id", None))
        if client_id <= 0:
            return {"status": "ignored", "reason": "client_id_missing", "ticket_id": ticket_id}

        client = await self._get_client(api, client_id)
        if client is None:
            return {
                "status": "ignored",
                "reason": "client_not_found",
                "ticket_id": ticket_id,
                "client_id": client_id,
            }
        return await self._enrich_ticket_client(
            api=api,
            runtime=runtime,
            ticket=ticket,
            client=client,
            source="TicketAdded",
        )

    async def _handle_client_edited(
        self,
        api: RegosAPI,
        runtime: RuntimeConfig,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        client_id = _extract_id(payload, "id", "client_id")
        if client_id <= 0:
            return {"status": "ignored", "reason": "client_id_missing"}

        client = await self._get_client(api, client_id)
        if client is None:
            return {"status": "ignored", "reason": "client_not_found", "client_id": client_id}

        tickets = await self._get_active_tickets_for_client(api, client_id)
        if not tickets:
            return {"status": "ignored", "reason": "active_tickets_not_found", "client_id": client_id}

        results: List[Dict[str, Any]] = []
        for ticket in tickets:
            result = await self._enrich_ticket_client(
                api=api,
                runtime=runtime,
                ticket=ticket,
                client=client,
                source="ClientEdited",
            )
            results.append(result)

        processed = [row for row in results if row.get("status") == "processed"]
        return {
            "status": "processed" if processed else "ignored",
            "client_id": client_id,
            "tickets": len(tickets),
            "processed": len(processed),
            "details": results,
        }

    async def _enrich_ticket_client(
        self,
        *,
        api: RegosAPI,
        runtime: RuntimeConfig,
        ticket: Ticket,
        client: Client,
        source: str,
    ) -> Dict[str, Any]:
        ticket_id = _to_int(getattr(ticket, "id", None))
        client_id = _to_int(getattr(client, "id", None))
        chat_id = _text(getattr(ticket, "chat_id", None))
        if ticket_id <= 0 or client_id <= 0 or not chat_id:
            return {
                "status": "ignored",
                "reason": "invalid_ticket_context",
                "ticket_id": ticket_id,
                "client_id": client_id,
            }

        billing = await self._request_billing(runtime, ticket, client)
        billing_client = billing.get("client") if isinstance(billing.get("client"), dict) else {}
        parameters = _normalize_billing_parameters(billing.get("parameters"))
        message_template = runtime.billing_message_template or _text(billing.get("message_template"))
        message_text = _render_message(message_template, parameters)
        client_patch = self._build_client_patch(client, billing_client)

        if not client_patch and not message_text:
            return {
                "status": "ignored",
                "reason": "empty_billing_response",
                "ticket_id": ticket_id,
                "client_id": client_id,
            }

        response_hash = _stable_hash(
            {
                "ticket_id": ticket_id,
                "client_id": client_id,
                "billing_client": _billing_client_hash_payload(billing_client),
                "message_text": message_text,
            }
        )
        dedupe_key = redis_make_key(
            "billing_connector",
            "sync",
            runtime.connected_integration_id,
            ticket_id,
            client_id,
            response_hash,
        )
        # Mark before side effects to absorb ClientEdited emitted by our own Client/Edit.
        if not await self._mark_dedupe(dedupe_key):
            return {
                "status": "ignored",
                "reason": "duplicate_billing_payload",
                "ticket_id": ticket_id,
                "client_id": client_id,
            }

        if client_patch:
            await self._update_client(api, client_id, client_patch)
            for field, value in client_patch.items():
                setattr(client, field, value)

        message_sent = False
        if message_text:
            await self._add_ticket_chat_message(
                api=api,
                chat_id=chat_id,
                text=message_text,
                external_message_id=f"billing_connector:{ticket_id}:{client_id}:{response_hash[:16]}",
            )
            message_sent = True

        return {
            "status": "processed",
            "source": source,
            "ticket_id": ticket_id,
            "client_id": client_id,
            "client_updated": bool(client_patch),
            "message_sent": message_sent,
        }

    async def _load_runtime(
        self,
        connected_integration_id: Optional[str] = None,
    ) -> RuntimeConfig:
        ci = self._ci(connected_integration_id)
        async with RegosAPI(ci) as api:
            response = await api.integrations.connected_integration_setting.get(
                ConnectedIntegrationSettingRequest(connected_integration_id=ci)
            )
        if not response.ok:
            raise BillingConnectorError("ConnectedIntegrationSetting/Get failed")
        settings = _normalize_settings(response.result)

        billing_client_info_url = _setting(settings, "billing_client_info_url")
        billing_bearer_token = _setting(settings, "billing_bearer_token")
        billing_message_template = _optional_text(_setting(settings, "billing_message_template"))
        missing = []
        if not billing_client_info_url:
            missing.append("billing_client_info_url")
        if not billing_bearer_token:
            missing.append("billing_bearer_token")
        if missing:
            raise BillingConnectorError(f"Missing settings: {', '.join(missing)}")

        return RuntimeConfig(
            connected_integration_id=ci,
            billing_client_info_url=billing_client_info_url,
            billing_bearer_token=billing_bearer_token,
            billing_message_template=billing_message_template,
        )

    async def _request_billing(
        self,
        runtime: RuntimeConfig,
        ticket: Ticket,
        client: Client,
    ) -> Dict[str, Any]:
        payload = {
            "client": _client_snapshot(client),
            "ticket": _ticket_snapshot(ticket),
        }
        headers = {
            "Authorization": f"Bearer {runtime.billing_bearer_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=BILLING_HTTP_TIMEOUT) as http_client:
            try:
                response = await http_client.post(
                    runtime.billing_client_info_url,
                    json=_drop_none(payload),
                    headers=headers,
                )
            except httpx.RequestError as error:
                raise BillingConnectorError("billing_request_failed") from error

        if response.status_code in {401, 403}:
            raise BillingConnectorError("billing_auth_failed")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise BillingConnectorError("billing_http_error") from error

        try:
            data = response.json()
        except Exception as error:
            raise BillingConnectorError("billing_response_not_json") from error
        if not isinstance(data, dict):
            raise BillingConnectorError("billing_response_not_object")
        return data

    async def _get_ticket(self, api: RegosAPI, ticket_id: int) -> Optional[Ticket]:
        response = await api.crm.ticket.get(TicketGetRequest(ids=[ticket_id], limit=1, offset=0))
        if not response.ok:
            raise BillingConnectorError(f"Ticket/Get failed for id={ticket_id}")
        rows = response.result or []
        return rows[0] if rows else None

    async def _get_client(self, api: RegosAPI, client_id: int) -> Optional[Client]:
        response = await api.crm.client.get(ClientGetRequest(ids=[client_id], limit=1, offset=0))
        if not response.ok:
            raise BillingConnectorError(f"Client/Get failed for id={client_id}")
        rows = response.result or []
        return rows[0] if rows else None

    async def _get_active_tickets_for_client(
        self,
        api: RegosAPI,
        client_id: int,
    ) -> List[Ticket]:
        result: List[Ticket] = []
        offset = 0
        page_size = 100
        while len(result) < MAX_ACTIVE_TICKETS_PER_CLIENT:
            response = await api.crm.ticket.get(
                TicketGetRequest(
                    client_ids=[client_id],
                    statuses=ACTIVE_TICKET_STATUSES,
                    limit=page_size,
                    offset=offset,
                )
            )
            if not response.ok:
                raise BillingConnectorError(f"Ticket/Get failed for client_id={client_id}")
            rows = response.result or []
            result.extend(rows)
            next_offset = _to_int(response.next_offset, 0)
            if not rows or next_offset <= 0 or next_offset == offset:
                break
            offset = next_offset
        return result[:MAX_ACTIVE_TICKETS_PER_CLIENT]

    def _build_client_patch(self, client: Client, billing_client: Dict[str, Any]) -> Dict[str, str]:
        patch: Dict[str, str] = {}
        for field in CLIENT_UPDATE_FIELDS:
            if field not in billing_client:
                continue
            value = _optional_text(billing_client.get(field))
            if value is None:
                continue
            current = _text(getattr(client, field, None))
            if value != current:
                patch[field] = value
        return patch

    async def _update_client(
        self,
        api: RegosAPI,
        client_id: int,
        patch: Dict[str, str],
    ) -> None:
        response = await api.crm.client.edit(ClientEditRequest(id=client_id, **patch))
        if not response.ok:
            raise BillingConnectorError(
                f"Client/Edit failed for id={client_id}: {_payload_dict(response.result)}"
            )

    async def _add_ticket_chat_message(
        self,
        *,
        api: RegosAPI,
        chat_id: str,
        text: str,
        external_message_id: str,
    ) -> None:
        response = await api.chat.chat_message.add(
            ChatMessageAddRequest(
                chat_id=chat_id,
                message_type=ChatMessageTypeEnum.System,
                text=text,
                external_message_id=external_message_id,
            )
        )
        if not response.ok:
            raise BillingConnectorError(
                f"ChatMessage/Add failed for chat_id={chat_id}: {_payload_dict(response.result)}"
            )

    def _is_active_ticket(self, ticket: Ticket) -> bool:
        return _enum_value(getattr(ticket, "status", None)) != TicketStatusEnum.Closed.value

    async def _mark_dedupe(self, key: str) -> bool:
        self._require_redis()
        inserted = await redis_ops.set(key, "1", ex=DEDUPE_TTL_SEC, nx=True)
        return bool(inserted)


__all__ = ["BillingConnectorIntegration"]
