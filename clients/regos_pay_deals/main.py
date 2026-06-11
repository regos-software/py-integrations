from __future__ import annotations

import asyncio
import hashlib
import json
import re
import time
import uuid
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
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
from schemas.api.common.filters import Filter, FilterOperator
from schemas.api.crm.deal import Deal, DealEditRequest, DealGetRequest, DealSetStageRequest
from schemas.api.crm.pipeline import CrmEntityTypeEnum, PipelineGetRequest
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingRequest,
)
from schemas.api.references.field import FieldAddRequest, FieldGetRequest


logger = setup_logger("regos_pay_deals")


DEFAULT_CHECKOUT_URL = "https://pay.regos.uz/api/CheckOut"
DEFAULT_DESCRIPTION_TEMPLATE = "Payment for deal #{deal_id}: {title}"
DEAL_ENTITY_TYPE = "Deal"
CHECKOUT_HTTP_TIMEOUT = 30.0
REDIS_PREFIX = "rpd"
QUEUE_DEDUPE_TTL_SEC = 10 * 60
STREAM_GROUP = "rpdw"
STREAM_TTL_SEC = 24 * 60 * 60
STREAM_MAXLEN = 10000
STREAM_BATCH_SIZE = 10
STREAM_WORKERS = 1
STREAM_READ_BLOCK_MS = 5000
STREAM_MIN_IDLE_MS = 60_000
STREAM_CLAIM_INTERVAL_SEC = 30
STREAM_MAX_RETRIES = 3
TRACE_TTL_SEC = 24 * 60 * 60
TRACE_MAXLEN = 200
ORDER_ID_FIELD_RAW_KEY = "regos_pay_order_id"
ORDER_ID_FIELD_KEY = f"field_{ORDER_ID_FIELD_RAW_KEY}"
ORDER_ID_FIELD_NAME = "REGOS Pay order ID"
ACCEPTED_DEAL_WEBHOOKS = {
    "DealStageSet",
}

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
    checkout_url: str
    service_id: str
    secret_key: str
    pipeline_id: int
    checkout_stage_id: int
    paid_stage_id: int


class RegosPayDealsError(Exception):
    pass


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
        return int(Decimal(str(value).strip()))
    except Exception:
        return default


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value).strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def _money(value: Any) -> Decimal:
    amount = _to_decimal(value)
    if amount is None:
        raise RegosPayDealsError("amount is required")
    amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount <= 0:
        raise RegosPayDealsError("amount must be greater than zero")
    return amount


def _money_string(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")


def _amount_minor_string(value: Any) -> str:
    amount = _to_decimal(value)
    if amount is None:
        return ""
    minor = (amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return str(int(minor))


def _json_amount(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _stable_hash(payload: Any) -> str:
    dumped = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _json_loads(raw: str) -> Any:
    return json.loads(raw)


def _now_ts() -> int:
    return int(time.time())


def _normalize_settings(rows: Any) -> Dict[str, str]:
    settings: Dict[str, str] = {}
    if not isinstance(rows, list):
        return settings
    for row in rows:
        key = _text(getattr(row, "key", None)).lower()
        if not key:
            continue
        settings[key] = _text(getattr(row, "value", None))
    return settings


def _setting(settings: Dict[str, str], *keys: str) -> str:
    for key in keys:
        value = _text(settings.get(str(key).lower()))
        if value:
            return value
    return ""


def _drop_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _drop_none(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_drop_none(v) for v in value]
    return value


def _trace_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _trace_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_trace_value(item) for item in value]
    return str(value)


def _payload_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(mode="json", exclude_none=True)
        return dumped if isinstance(dumped, dict) else {}
    return {}


def _extract_field_value(entity: Any, field_key: str) -> Optional[str]:
    expected = _text(field_key).lower()
    if not expected:
        return None
    fields = getattr(entity, "fields", None)
    if not isinstance(fields, list):
        return None
    for field in fields:
        key = _text(getattr(field, "key", None)).lower()
        if key != expected:
            continue
        value = getattr(field, "value", None)
        return None if value is None else str(value)
    return None


def _request_id(payload: Dict[str, Any]) -> int:
    value = _to_int(payload.get("id"), 0)
    return value if value > 0 else 0


def _param(params: Dict[str, Any], *names: str) -> Any:
    lower_map = {str(key).lower(): value for key, value in params.items()}
    for name in names:
        if name in params:
            return params[name]
        value = lower_map.get(str(name).lower())
        if value is not None:
            return value
    return None


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


def _plain_int_text(value: Any) -> str:
    if value is None or value == "":
        return ""
    try:
        return str(int(Decimal(str(value).strip())))
    except Exception:
        return str(value).strip()


def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _parse_json_body(body: Any) -> Dict[str, Any]:
    if isinstance(body, dict):
        return body
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="ignore")
    if isinstance(body, str) and body.strip():
        try:
            decoded = json.loads(body)
            return decoded if isinstance(decoded, dict) else {}
        except Exception:
            return {}
    return {}


def _parse_deal_id_from_external_id(external_id: Any) -> int:
    text = _text(external_id)
    if not text:
        return 0
    match = re.fullmatch(r"(?:deal[:_-])?(\d+)", text, flags=re.IGNORECASE)
    if not match:
        return 0
    return int(match.group(1))


def _extract_deal_id(payload: Dict[str, Any]) -> int:
    candidates = [
        _lookup(payload, "deal_id", "entity_id", "object_id", "id"),
        _lookup(payload.get("deal") if isinstance(payload.get("deal"), dict) else {}, "id"),
        _lookup(payload.get("entity") if isinstance(payload.get("entity"), dict) else {}, "id"),
        _lookup(payload.get("object") if isinstance(payload.get("object"), dict) else {}, "id"),
    ]
    for candidate in candidates:
        deal_id = _to_int(candidate)
        if deal_id > 0:
            return deal_id
    return 0


def _callback_method_from_path(external_path: Any) -> str:
    parts = [
        part.strip()
        for part in str(external_path or "").strip("/").split("/")
        if part.strip()
    ]
    if parts and re.fullmatch(r"[0-9a-fA-F]{32}", parts[0]):
        parts = parts[1:]
    if not parts:
        return ""
    return parts[-1].lower()


def _normalize_regos_webhook_payload(
    action: Optional[str],
    data: Optional[Dict[str, Any]],
    extra: Dict[str, Any],
) -> tuple[Optional[str], Dict[str, Any], Optional[str]]:
    event_id = _text(extra.get("event_id")) or None

    if isinstance(action, str) and action in ACCEPTED_DEAL_WEBHOOKS:
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


def _format_description(template: str, deal: Deal, deal_id: int) -> str:
    title = _text(getattr(deal, "title", None), f"Deal {deal_id}")
    try:
        return template.format(deal_id=deal_id, title=title, amount=getattr(deal, "amount", ""))
    except Exception:
        return DEFAULT_DESCRIPTION_TEMPLATE.format(deal_id=deal_id, title=title)


class RegosPayDealsIntegration(ClientBase):
    integration_key = "regos_pay_deals"

    def __init__(self) -> None:
        self.connected_integration_id: Optional[str] = None

    @classmethod
    def _redis_key(cls, *parts: Any) -> str:
        return redis_make_key(REDIS_PREFIX, *parts)

    @classmethod
    def _trace_key(cls, connected_integration_id: str) -> str:
        return cls._redis_key("t", connected_integration_id)

    @classmethod
    async def _trace(
        cls,
        connected_integration_id: str,
        event: str,
        **details: Any,
    ) -> None:
        ci = _text(connected_integration_id)
        if not ci or not redis_is_enabled():
            return
        entry = _drop_none(
            {
                "ts": _now_ts(),
                "event": _text(event),
                **{str(key): _trace_value(value) for key, value in details.items()},
            }
        )
        try:
            key = cls._trace_key(ci)
            async with redis_ops.pipeline(transaction=True) as pipe:
                await pipe.rpush(key, _json_dumps(entry))
                await pipe.ltrim(key, -TRACE_MAXLEN, -1)
                await pipe.expire(key, TRACE_TTL_SEC)
                await pipe.execute()
        except Exception as error:
            logger.debug("REGOS Pay Redis trace write failed: ci=%s error=%s", ci, error)

    @classmethod
    def _require_redis(cls) -> None:
        if not redis_is_enabled():
            raise RegosPayDealsError("Redis is required for regos_pay_deals queue")

    @classmethod
    def _stream_key(cls) -> str:
        return cls._redis_key("s", "e")

    @classmethod
    def _dlq_stream_key(cls) -> str:
        return cls._redis_key("s", "dlq")

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
        return cls._redis_key("qd", connected_integration_id, event_hash)

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
                    name=f"regos_pay_deals_stream_{worker_index}",
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
            logger.warning("REGOS Pay deals stream xautoclaim failed: %s", error)
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
        logger.info("REGOS Pay deals stream worker started: stream=%s", stream_key)
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
                    logger.exception("REGOS Pay deals stream worker error: %s", error)
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
        if not ci or action not in ACCEPTED_DEAL_WEBHOOKS or not isinstance(payload, dict):
            logger.warning(
                "REGOS Pay deals stream entry has invalid payload: "
                "entry_id=%s fields=%s",
                entry_id,
                fields,
            )
            await cls._ack_stream_entry(stream_key, entry_id)
            return

        attempt = cls._stream_entry_attempt(fields)
        await cls._trace(
            ci,
            "worker_started",
            action=action,
            event_id=event_id,
            entry_id=entry_id,
            attempt=attempt,
        )
        worker = cls()
        worker.connected_integration_id = ci
        try:
            result = await worker._process_webhook_event(action, payload, event_id)
            result_status = result.get("status") if isinstance(result, dict) else None
            result_payload = result.get("result") if isinstance(result, dict) else {}
            result_reason = result_payload.get("reason") if isinstance(result_payload, dict) else None
            await cls._trace(
                ci,
                "worker_done",
                action=action,
                event_id=event_id,
                entry_id=entry_id,
                attempt=attempt,
                status=result_status,
                reason=result_reason,
            )
            logger.debug(
                "REGOS Pay deals stream job processed: "
                "ci=%s action=%s entry_id=%s status=%s",
                ci,
                action,
                entry_id,
                result.get("status") if isinstance(result, dict) else result,
            )
            await cls._ack_stream_entry(stream_key, entry_id)
        except Exception as error:
            if cls._is_non_retryable_error(error):
                await cls._trace(
                    ci,
                    "worker_skipped",
                    action=action,
                    event_id=event_id,
                    entry_id=entry_id,
                    attempt=attempt,
                    error=str(error),
                )
                logger.warning(
                    "REGOS Pay deals stream job skipped: "
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
                await cls._trace(
                    ci,
                    "worker_dlq",
                    action=action,
                    event_id=event_id,
                    entry_id=entry_id,
                    attempt=next_attempt,
                    error=str(error),
                )
                await cls._ack_stream_entry(stream_key, entry_id)
                logger.error(
                    "REGOS Pay deals stream job moved to DLQ: "
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
            await cls._trace(
                ci,
                "worker_retry",
                action=action,
                event_id=event_id,
                entry_id=entry_id,
                attempt=next_attempt,
                error=str(error),
            )
            await cls._ack_stream_entry(stream_key, entry_id)
            logger.warning(
                "REGOS Pay deals stream job requeued: "
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
            raise RegosPayDealsError("connected_integration_id is required")
        return ci

    async def connect(self, **kwargs: Any) -> Dict[str, Any]:
        """Validate settings and create the configured deal field once on connection."""
        runtime = await self._load_runtime(
            connected_integration_id=_optional_text(kwargs.get("connected_integration_id")),
        )
        self._require_redis()
        async with RegosAPI(runtime.connected_integration_id) as api:
            await self._ensure_pipeline_stages(api, runtime)
            fields = await self._ensure_configured_fields(api)
        await self._ensure_stream_workers()
        await self._trace(
            runtime.connected_integration_id,
            "connect_ready",
            pipeline_id=runtime.pipeline_id,
            checkout_stage_id=runtime.checkout_stage_id,
            paid_stage_id=runtime.paid_stage_id,
            stream_key=self._stream_key(),
            trace_key=self._trace_key(runtime.connected_integration_id),
        )
        return {
            "status": "connected",
            "integration_key": self.integration_key,
            "pipeline_id": runtime.pipeline_id,
            "checkout_stage_id": runtime.checkout_stage_id,
            "paid_stage_id": runtime.paid_stage_id,
            "fields": fields,
            "queue_enabled": True,
            "callbacks": {
                "regos_pay": f"/external/{runtime.connected_integration_id}",
            },
            "diagnostics": {
                "trace_key": self._trace_key(runtime.connected_integration_id),
                "trace_ttl_sec": TRACE_TTL_SEC,
                "trace_maxlen": TRACE_MAXLEN,
            },
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

    async def _create_checkout_for_deal(
        self,
        *,
        runtime: RuntimeConfig,
        deal_id: int,
        publish_to_chat: bool = True,
        event_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create one REGOS Pay order for a deal that is on the configured checkout stage."""
        deal_id_int = _to_int(deal_id)
        if deal_id_int <= 0:
            raise RegosPayDealsError("deal_id must be positive")

        async with RegosAPI(runtime.connected_integration_id) as api:
            deal = await self._get_deal(api, deal_id_int)
            if deal is None:
                raise RegosPayDealsError(f"deal {deal_id_int} not found")
            deal_pipeline_id = _to_int(getattr(deal, "pipeline_id", None))
            deal_stage_id = _to_int(getattr(deal, "stage_id", None))
            await self._trace(
                runtime.connected_integration_id,
                "deal_loaded",
                event_id=event_id,
                deal_id=deal_id_int,
                pipeline_id=deal_pipeline_id,
                stage_id=deal_stage_id,
                checkout_stage_id=runtime.checkout_stage_id,
            )
            if not self._deal_pipeline_matches(deal, runtime):
                await self._trace(
                    runtime.connected_integration_id,
                    "checkout_ignored",
                    event_id=event_id,
                    deal_id=deal_id_int,
                    reason="pipeline_mismatch",
                    pipeline_id=deal_pipeline_id,
                    expected_pipeline_id=runtime.pipeline_id,
                )
                return {
                    "status": "ignored",
                    "reason": "pipeline_mismatch",
                    "deal_id": deal_id_int,
                    "pipeline_id": deal_pipeline_id,
                    "expected_pipeline_id": runtime.pipeline_id,
                }
            if not self._deal_checkout_stage_matches(deal, runtime):
                await self._trace(
                    runtime.connected_integration_id,
                    "checkout_ignored",
                    event_id=event_id,
                    deal_id=deal_id_int,
                    reason="stage_mismatch",
                    stage_id=deal_stage_id,
                    checkout_stage_id=runtime.checkout_stage_id,
                )
                return {
                    "status": "ignored",
                    "reason": "stage_mismatch",
                    "deal_id": deal_id_int,
                    "stage_id": deal_stage_id,
                    "checkout_stage_id": runtime.checkout_stage_id,
                }

            current_order_id = _text(_extract_field_value(deal, ORDER_ID_FIELD_KEY))
            if current_order_id:
                await self._trace(
                    runtime.connected_integration_id,
                    "checkout_already_created",
                    event_id=event_id,
                    deal_id=deal_id_int,
                    order_id=current_order_id,
                )
                return _drop_none(
                    {
                        "status": "already_created",
                        "deal_id": deal_id_int,
                        "order_id": current_order_id,
                    }
                )

            try:
                checkout_amount = _money(getattr(deal, "amount", None))
            except RegosPayDealsError as error:
                await self._trace(
                    runtime.connected_integration_id,
                    "checkout_error",
                    event_id=event_id,
                    deal_id=deal_id_int,
                    reason="amount_invalid",
                    error=str(error),
                )
                raise
            checkout_external_id = f"deal:{deal_id_int}"
            checkout_description = _format_description(
                DEFAULT_DESCRIPTION_TEMPLATE,
                deal,
                deal_id_int,
            )

            payload = {
                "external_id": checkout_external_id,
                "service_id": runtime.service_id,
                "amount": _json_amount(checkout_amount),
                "description": checkout_description,
            }
            payload = _drop_none(payload)

            await self._trace(
                runtime.connected_integration_id,
                "checkout_request",
                event_id=event_id,
                deal_id=deal_id_int,
                external_id=checkout_external_id,
                amount=_money_string(checkout_amount),
                checkout_url=runtime.checkout_url,
            )
            try:
                response_payload = await self._send_checkout(runtime, payload)
            except Exception as error:
                await self._trace(
                    runtime.connected_integration_id,
                    "checkout_exception",
                    event_id=event_id,
                    deal_id=deal_id_int,
                    error=str(error),
                )
                raise
            error_code = _to_int(response_payload.get("error_code"), 1)
            if error_code != 0:
                await self._trace(
                    runtime.connected_integration_id,
                    "checkout_error",
                    event_id=event_id,
                    deal_id=deal_id_int,
                    error_code=error_code,
                    error_description=_text(response_payload.get("error_description"), "CheckOut failed"),
                )
                return {
                    "status": "error",
                    "source": "regos_pay",
                    "error_code": error_code,
                    "error_description": _text(response_payload.get("error_description"), "CheckOut failed"),
                }

            order_id = _text(response_payload.get("id"))
            payment_url = _optional_text(response_payload.get("url"))
            if not order_id:
                await self._trace(
                    runtime.connected_integration_id,
                    "checkout_error",
                    event_id=event_id,
                    deal_id=deal_id_int,
                    error_code=error_code,
                    error_description="CheckOut response does not contain id",
                )
                return {
                    "status": "error",
                    "source": "regos_pay",
                    "error_code": error_code,
                    "error_description": "CheckOut response does not contain id",
                }

            fields = [{"key": ORDER_ID_FIELD_KEY, "value": order_id}]

            edit_response = await api.crm.deal.edit(
                DealEditRequest(id=deal_id_int, fields=fields)
            )
            if not edit_response.ok:
                logger.warning(
                    "Deal/Edit rejected while saving REGOS Pay order id: ci=%s deal_id=%s payload=%s",
                    runtime.connected_integration_id,
                    deal_id_int,
                    edit_response.result,
                )
                await self._trace(
                    runtime.connected_integration_id,
                    "checkout_not_saved",
                    event_id=event_id,
                    deal_id=deal_id_int,
                    order_id=order_id,
                    payment_url_present=bool(payment_url),
                )
                return {
                    "status": "created_not_saved",
                    "deal_id": deal_id_int,
                    "order_id": order_id,
                    "external_id": checkout_external_id,
                    "payment_url": payment_url,
                    "warning": "REGOS Pay order was created, but CRM deal field was not updated",
                }

            if publish_to_chat:
                await self._publish_checkout_message(
                    api=api,
                    deal=deal,
                    order_id=order_id,
                    amount=checkout_amount,
                    payment_url=payment_url,
                )

            await self._trace(
                runtime.connected_integration_id,
                "checkout_created",
                event_id=event_id,
                deal_id=deal_id_int,
                order_id=order_id,
                external_id=checkout_external_id,
                amount=_money_string(checkout_amount),
                payment_url_present=bool(payment_url),
            )

        return _drop_none(
            {
                "status": "created",
                "deal_id": deal_id_int,
                "order_id": order_id,
                "external_id": checkout_external_id,
                "amount": _money_string(checkout_amount),
                "payment_url": payment_url,
            }
        )

    async def handle_external(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """REGOS Pay callback entrypoint for Check and Perform external URLs."""
        body = _parse_json_body((envelope or {}).get("body"))
        method = _text(body.get("method")).lower()
        if not method:
            method = _callback_method_from_path((envelope or {}).get("external_path"))
        if method in {"check", "perform"}:
            return await self._handle_callback(method, body, envelope or {})
        request_id = _request_id(body)
        return self._callback_response(
            request_id,
            1,
            f"Unsupported method: {method or 'unknown'}",
        )

    async def handle_webhook(
        self,
        action: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Accept REGOS deal webhooks quickly and process checkout creation from Redis Stream."""
        if not self.connected_integration_id:
            return {"status": "error", "description": "connected_integration_id is required"}
        ci = self._ci()

        webhook_action, payload, event_id = _normalize_regos_webhook_payload(
            action=action,
            data=data,
            extra=kwargs,
        )
        if webhook_action not in ACCEPTED_DEAL_WEBHOOKS:
            await self._trace(
                ci,
                "webhook_ignored",
                action=webhook_action,
                event_id=event_id,
                reason="unsupported_action",
            )
            return {"status": "ignored", "reason": f"unsupported_action:{webhook_action}"}

        deal_id = _extract_deal_id(payload)
        if deal_id <= 0:
            await self._trace(
                ci,
                "webhook_ignored",
                action=webhook_action,
                event_id=event_id,
                reason="deal_id_missing",
            )
            return {"status": "ignored", "reason": "deal_id_missing", "action": webhook_action}

        await self._trace(
            ci,
            "webhook_received",
            action=webhook_action,
            event_id=event_id,
            deal_id=deal_id,
        )
        try:
            queued = await self._enqueue_event(
                connected_integration_id=ci,
                action=webhook_action,
                payload=payload,
                event_id=event_id,
            )
            await self._trace(
                ci,
                "webhook_queued",
                action=webhook_action,
                event_id=event_id,
                deal_id=deal_id,
                queued=bool(queued),
                duplicate=not queued,
            )
        except RegosPayDealsError as error:
            await self._trace(
                ci,
                "webhook_enqueue_error",
                action=webhook_action,
                event_id=event_id,
                deal_id=deal_id,
                error=str(error),
            )
            logger.warning(
                "REGOS Pay deals enqueue error: ci=%s action=%s error=%s",
                self.connected_integration_id,
                webhook_action,
                error,
            )
            return {"status": "error", "action": webhook_action, "reason": str(error)}
        except Exception as error:
            await self._trace(
                ci,
                "webhook_enqueue_error",
                action=webhook_action,
                event_id=event_id,
                deal_id=deal_id,
                error=str(error),
            )
            logger.exception(
                "REGOS Pay deals enqueue failed: ci=%s action=%s error=%s",
                self.connected_integration_id,
                webhook_action,
                error,
            )
            return {"status": "error", "action": webhook_action, "reason": "enqueue_failed"}

        return {
            "status": "accepted",
            "action": webhook_action,
            "event_id": event_id,
            "deal_id": deal_id,
            "queued": 1 if queued else 0,
            "duplicate": not queued,
        }

    async def _process_webhook_event(
        self,
        webhook_action: str,
        payload: Dict[str, Any],
        event_id: Optional[str],
    ) -> Dict[str, Any]:
        deal_id = _extract_deal_id(payload)
        if deal_id <= 0:
            return {"status": "ignored", "reason": "deal_id_missing", "action": webhook_action}

        runtime = await self._load_runtime()
        result = await self._create_checkout_for_deal(
            runtime=runtime,
            deal_id=deal_id,
            publish_to_chat=True,
            event_id=event_id,
        )
        return {
            "status": result.get("status", "processed"),
            "action": webhook_action,
            "event_id": event_id,
            "deal_id": deal_id,
            "result": result,
        }

    async def deal_stage_set(
        self,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Adapter for direct REGOS webhook calls with action=DealStageSet."""
        payload = data if isinstance(data, dict) else dict(kwargs)
        event_id = kwargs.get("event_id")
        if event_id is not None and "event_id" in payload:
            payload = {key: value for key, value in payload.items() if key != "event_id"}
        return await self.handle_webhook(
            action="DealStageSet",
            data=payload,
            event_id=event_id,
        )

    async def _handle_callback(
        self,
        method: str,
        payload: Dict[str, Any],
        envelope: Dict[str, Any],
    ) -> Dict[str, Any]:
        request_id = _request_id(payload)
        params = payload.get("params") if isinstance(payload.get("params"), dict) else {}
        sign = _text(payload.get("sign")).lower()
        try:
            runtime = await self._load_runtime(
                connected_integration_id=_optional_text(envelope.get("connected_integration_id"))
            )
        except Exception as error:
            logger.warning("REGOS Pay callback settings error: %s", error)
            return self._callback_response(request_id, 1, "Integration settings error")

        if not self._verify_callback_sign(runtime, method, sign, params):
            await self._trace(
                runtime.connected_integration_id,
                "callback_error",
                method=method,
                request_id=request_id,
                reason="invalid_sign",
            )
            logger.warning(
                "REGOS Pay callback signature mismatch: ci=%s method=%s params=%s",
                runtime.connected_integration_id,
                method,
                params,
            )
            return self._callback_response(request_id, 1, "Invalid sign")

        try:
            await self._trace(
                runtime.connected_integration_id,
                "callback_received",
                method=method,
                request_id=request_id,
                order_id=_text(_param(params, "order_Id", "order_id")),
                external_id=_text(_param(params, "external_Id", "external_id")),
                amount=_text(_param(params, "amount")),
            )
            if method == "check":
                return await self._callback_check(runtime, request_id, params)
            if method == "perform":
                return await self._callback_perform(runtime, request_id, params)
        except Exception as error:
            await self._trace(
                runtime.connected_integration_id,
                "callback_error",
                method=method,
                request_id=request_id,
                reason="exception",
                error=str(error),
            )
            logger.exception(
                "REGOS Pay callback failed: ci=%s method=%s error=%s",
                runtime.connected_integration_id,
                method,
                error,
            )
            return self._callback_response(request_id, 1, "Callback processing error")

        return self._callback_response(request_id, 1, f"Unsupported method: {method}")

    async def _callback_check(
        self,
        runtime: RuntimeConfig,
        request_id: int,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Confirm by external_Id that the linked deal exists and still has the same amount."""
        order_id = _text(_param(params, "order_Id", "order_id"))
        external_id = _text(_param(params, "external_Id", "external_id"))
        amount = _to_decimal(_param(params, "amount"))
        if not order_id or not external_id or amount is None:
            return await self._callback_error(
                runtime,
                request_id,
                "check",
                "Required params are missing",
            )

        external_deal_id = _parse_deal_id_from_external_id(external_id)
        if external_deal_id <= 0:
            return await self._callback_error(
                runtime,
                request_id,
                "check",
                "External id mismatch",
                external_id=external_id,
            )

        async with RegosAPI(runtime.connected_integration_id) as api:
            deal = await self._get_deal(api, external_deal_id)
            if deal is None:
                return await self._callback_error(
                    runtime,
                    request_id,
                    "check",
                    "Deal not found",
                    deal_id=external_deal_id,
                )

            if not self._deal_pipeline_matches(deal, runtime):
                return await self._callback_error(
                    runtime,
                    request_id,
                    "check",
                    "Deal pipeline mismatch",
                    deal_id=external_deal_id,
                    pipeline_id=_to_int(getattr(deal, "pipeline_id", None)),
                    expected_pipeline_id=runtime.pipeline_id,
                )

            saved_order_id = _text(_extract_field_value(deal, ORDER_ID_FIELD_KEY))
            if saved_order_id and saved_order_id != order_id:
                return await self._callback_error(
                    runtime,
                    request_id,
                    "check",
                    "Order id mismatch",
                    deal_id=external_deal_id,
                    order_id=order_id,
                    saved_order_id=saved_order_id,
                )

            expected_amount = self._expected_amount(deal)
            if expected_amount is None:
                return await self._callback_error(
                    runtime,
                    request_id,
                    "check",
                    "Deal amount is empty",
                    deal_id=external_deal_id,
                )
            if _amount_minor_string(amount) != _amount_minor_string(expected_amount):
                return await self._callback_error(
                    runtime,
                    request_id,
                    "check",
                    "Amount mismatch",
                    deal_id=external_deal_id,
                    amount=_money_string(amount),
                    expected_amount=_money_string(expected_amount),
                )

        return await self._callback_ok(
            runtime,
            request_id,
            "check",
            deal_id=external_deal_id,
            order_id=order_id,
        )

    async def _callback_perform(
        self,
        runtime: RuntimeConfig,
        request_id: int,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Mark successful REGOS Pay payment in the deal chat and optional paid stage."""
        order_id = _text(_param(params, "order_Id", "order_id"))
        if not order_id:
            return await self._callback_error(
                runtime,
                request_id,
                "perform",
                "order_Id is required",
            )

        async with RegosAPI(runtime.connected_integration_id) as api:
            deal = await self._find_deal_by_order_id(api, runtime, order_id)
            if deal is None:
                return await self._callback_error(
                    runtime,
                    request_id,
                    "perform",
                    "Deal not found",
                    order_id=order_id,
                )
            if not self._deal_pipeline_matches(deal, runtime):
                return await self._callback_error(
                    runtime,
                    request_id,
                    "perform",
                    "Deal pipeline mismatch",
                    order_id=order_id,
                    pipeline_id=_to_int(getattr(deal, "pipeline_id", None)),
                    expected_pipeline_id=runtime.pipeline_id,
                )

            deal_id = _to_int(getattr(deal, "id", None))
            if deal_id <= 0:
                return await self._callback_error(
                    runtime,
                    request_id,
                    "perform",
                    "Deal id is empty",
                    order_id=order_id,
                )
            if (
                runtime.paid_stage_id > 0
                and _to_int(getattr(deal, "stage_id", None)) != runtime.paid_stage_id
            ):
                response = await api.crm.deal.set_stage(
                    DealSetStageRequest(
                        id=deal_id,
                        stage_id=runtime.paid_stage_id,
                        comment=f"REGOS Pay order {order_id} paid",
                    )
                )
                if not response.ok:
                    logger.warning(
                        "Deal/SetStage rejected on REGOS Pay perform: ci=%s deal_id=%s payload=%s",
                        runtime.connected_integration_id,
                        deal_id,
                        response.result,
                    )
                    return await self._callback_error(
                        runtime,
                        request_id,
                        "perform",
                        "Deal stage update failed",
                        deal_id=deal_id,
                        order_id=order_id,
                    )

            await self._publish_paid_message(
                api=api,
                deal=deal,
                order_id=order_id,
            )

        return await self._callback_ok(
            runtime,
            request_id,
            "perform",
            deal_id=deal_id,
            order_id=order_id,
        )

    async def _load_runtime(
        self,
        connected_integration_id: Optional[str] = None,
    ) -> RuntimeConfig:
        """Load and validate integration settings from REGOS connected integration storage."""
        ci = self._ci(connected_integration_id)
        async with RegosAPI(ci) as api:
            response = await api.integrations.connected_integration_setting.get(
                ConnectedIntegrationSettingRequest(connected_integration_id=ci)
            )
        if not response.ok:
            raise RegosPayDealsError("ConnectedIntegrationSetting/Get failed")
        settings = _normalize_settings(response.result)

        service_id = _setting(settings, "regos_pay_service_id")
        secret_key = _setting(settings, "regos_pay_secret_key")
        pipeline_id = _to_int(_setting(settings, "regos_pay_deal_pipeline_id"))
        checkout_stage_id = _to_int(_setting(settings, "regos_pay_checkout_stage_id"))
        paid_stage_id = _to_int(_setting(settings, "regos_pay_paid_stage_id"))
        missing = []
        if not service_id:
            missing.append("regos_pay_service_id")
        if not secret_key:
            missing.append("regos_pay_secret_key")
        if pipeline_id <= 0:
            missing.append("regos_pay_deal_pipeline_id")
        if checkout_stage_id <= 0:
            missing.append("regos_pay_checkout_stage_id")
        if missing:
            raise RegosPayDealsError(f"Missing settings: {', '.join(missing)}")

        return RuntimeConfig(
            connected_integration_id=ci,
            checkout_url=DEFAULT_CHECKOUT_URL,
            service_id=service_id,
            secret_key=secret_key,
            pipeline_id=pipeline_id,
            checkout_stage_id=checkout_stage_id,
            paid_stage_id=paid_stage_id,
        )

    async def _send_checkout(
        self,
        runtime: RuntimeConfig,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=CHECKOUT_HTTP_TIMEOUT) as client:
            response = await client.post(runtime.checkout_url, json=payload)
            response.raise_for_status()
        try:
            data = response.json()
        except Exception as error:
            raise RegosPayDealsError("CheckOut response is not valid JSON") from error
        if not isinstance(data, dict):
            raise RegosPayDealsError("CheckOut response must be an object")
        return data

    async def _get_deal(self, api: RegosAPI, deal_id: int) -> Optional[Deal]:
        response = await api.crm.deal.get(
            DealGetRequest(ids=[int(deal_id)], limit=1, offset=0)
        )
        if not response.ok:
            raise RegosPayDealsError(f"Deal/Get failed for id={deal_id}")
        rows = response.result or []
        return rows[0] if rows else None

    async def _find_deal_by_order_id(
        self,
        api: RegosAPI,
        runtime: RuntimeConfig,
        order_id: str,
    ) -> Optional[Deal]:
        """Find the deal through the service order-id field used by callbacks."""
        response = await api.crm.deal.get(
            DealGetRequest(
                pipeline_id=runtime.pipeline_id,
                filters=[
                    Filter(
                        field=ORDER_ID_FIELD_KEY,
                        operator=FilterOperator.Equal,
                        value=str(order_id),
                    )
                ],
                limit=1,
                offset=0,
            )
        )
        if not response.ok:
            raise RegosPayDealsError("Deal/Get by REGOS Pay order id failed")
        rows = response.result or []
        return rows[0] if rows else None

    async def _ensure_pipeline_stages(self, api: RegosAPI, runtime: RuntimeConfig) -> None:
        response = await api.crm.pipeline.get(
            PipelineGetRequest(
                entity_type=CrmEntityTypeEnum.Deal,
                ids=[runtime.pipeline_id],
                active=True,
                limit=1,
                offset=0,
            )
        )
        if not response.ok or not response.result:
            raise RegosPayDealsError(f"Deal pipeline {runtime.pipeline_id} not found")
        pipeline = response.result[0]
        stages = getattr(pipeline, "stages", None) or []
        found_stage_ids = {
            _to_int(getattr(stage, "id", None))
            for stage in stages
            if getattr(stage, "active", True) is not False
        }
        if runtime.checkout_stage_id not in found_stage_ids:
            raise RegosPayDealsError(
                f"Deal checkout stage {runtime.checkout_stage_id} not found "
                f"in pipeline {runtime.pipeline_id}"
            )
        if runtime.paid_stage_id <= 0:
            return
        if runtime.paid_stage_id in found_stage_ids:
            return
        raise RegosPayDealsError(
            f"Deal paid stage {runtime.paid_stage_id} not found "
            f"in pipeline {runtime.pipeline_id}"
        )

    async def _publish_checkout_message(
        self,
        *,
        api: RegosAPI,
        deal: Deal,
        order_id: str,
        amount: Decimal,
        payment_url: Optional[str],
    ) -> None:
        chat_id = _text(getattr(deal, "chat_id", None))
        if not chat_id or not payment_url:
            return
        text = (
            "REGOS Pay payment link\n"
            f"Amount: {_money_string(amount)}\n"
            f"Order: {order_id}\n"
            f"{payment_url}"
        )
        await self._add_deal_chat_message(
            api=api,
            chat_id=chat_id,
            text=text,
            external_message_id=f"regos_pay:checkout:{order_id}",
        )

    async def _publish_paid_message(
        self,
        *,
        api: RegosAPI,
        deal: Deal,
        order_id: str,
    ) -> None:
        chat_id = _text(getattr(deal, "chat_id", None))
        if not chat_id:
            return
        amount = self._expected_amount(deal)
        amount_line = f"\nAmount: {_money_string(amount)}" if amount is not None else ""
        text = f"REGOS Pay payment received{amount_line}\nOrder: {order_id}"
        await self._add_deal_chat_message(
            api=api,
            chat_id=chat_id,
            text=text,
            external_message_id=f"regos_pay:paid:{order_id}",
        )

    async def _add_deal_chat_message(
        self,
        *,
        api: RegosAPI,
        chat_id: str,
        text: str,
        external_message_id: str,
    ) -> None:
        try:
            response = await api.chat.chat_message.add(
                ChatMessageAddRequest(
                    chat_id=chat_id,
                    message_type=ChatMessageTypeEnum.System,
                    text=text,
                    external_message_id=external_message_id,
                )
            )
            if not response.ok:
                logger.warning(
                    "ChatMessage/Add rejected for REGOS Pay deals: chat_id=%s payload=%s",
                    chat_id,
                    response.result,
                )
        except Exception:
            logger.exception(
                "Failed to publish REGOS Pay chat message: chat_id=%s external_message_id=%s",
                chat_id,
                external_message_id,
            )

    async def _ensure_configured_fields(
        self,
        api: RegosAPI,
    ) -> List[Dict[str, Any]]:
        specs = [
            (
                ORDER_ID_FIELD_KEY,
                ORDER_ID_FIELD_RAW_KEY,
                ORDER_ID_FIELD_NAME,
                "string",
                True,
            )
        ]

        result: List[Dict[str, Any]] = []
        for field_key, raw_key, field_name, data_type, required in specs:
            status = await self._ensure_field(
                api=api,
                key=field_key,
                raw_key=raw_key,
                name=field_name,
                data_type=data_type,
            )
            result.append(
                {
                    "key": field_key,
                    "name": field_name,
                    "data_type": data_type,
                    "required": required,
                    "status": status,
                }
            )
        return result

    async def _ensure_field(
        self,
        api: RegosAPI,
        key: str,
        raw_key: str,
        name: str,
        data_type: str,
    ) -> str:
        response = await api.references.field.get(
            FieldGetRequest(entity_type=DEAL_ENTITY_TYPE, keys=[key], limit=1, offset=0)
        )
        if not response.ok:
            raise RegosPayDealsError(f"Field/Get failed for {key}")
        expected = key.strip().lower()
        rows = response.result if isinstance(response.result, list) else []
        for row in rows:
            if _text(getattr(row, "key", None)).lower() == expected:
                return "exists"
        add_response = await api.references.field.add(
            FieldAddRequest(
                key=raw_key,
                name=name,
                entity_type=DEAL_ENTITY_TYPE,
                data_type=data_type,
                required=False,
            )
        )
        if not add_response.ok:
            raise RegosPayDealsError(
                f"Field/Add failed for {key}: {_payload_dict(add_response.result)}"
            )
        return "created"

    def _deal_pipeline_matches(self, deal: Deal, runtime: RuntimeConfig) -> bool:
        return _to_int(getattr(deal, "pipeline_id", None)) == runtime.pipeline_id

    def _deal_checkout_stage_matches(self, deal: Deal, runtime: RuntimeConfig) -> bool:
        return _to_int(getattr(deal, "stage_id", None)) == runtime.checkout_stage_id

    def _expected_amount(self, deal: Deal) -> Optional[Decimal]:
        return _to_decimal(getattr(deal, "amount", None))

    def _verify_callback_sign(
        self,
        runtime: RuntimeConfig,
        method: str,
        sign: str,
        params: Dict[str, Any],
    ) -> bool:
        if method == "check":
            date = _plain_int_text(_param(params, "date"))
            order_id = _text(_param(params, "order_Id", "order_id"))
            external_id = _text(_param(params, "external_Id", "external_id"))
            amount_minor = _amount_minor_string(_param(params, "amount"))
            source = f"{method}{runtime.secret_key}{date}{order_id}{external_id}{amount_minor}"
            expected = _md5(source)
            return bool(sign) and sign == expected.lower()
        if method == "perform":
            order_id = _text(_param(params, "order_Id", "order_id"))
            source = f"{method}{runtime.secret_key}{order_id}"
            expected = _md5(source)
            return bool(sign) and sign == expected.lower()
        return False

    async def _callback_error(
        self,
        runtime: RuntimeConfig,
        request_id: int,
        method: str,
        description: str,
        **details: Any,
    ) -> Dict[str, Any]:
        await self._trace(
            runtime.connected_integration_id,
            "callback_error",
            method=method,
            request_id=request_id,
            reason=description,
            **details,
        )
        return self._callback_response(request_id, 1, description)

    async def _callback_ok(
        self,
        runtime: RuntimeConfig,
        request_id: int,
        method: str,
        **details: Any,
    ) -> Dict[str, Any]:
        await self._trace(
            runtime.connected_integration_id,
            "callback_ok",
            method=method,
            request_id=request_id,
            **details,
        )
        return self._callback_response(request_id, 0)

    def _callback_response(
        self,
        request_id: int,
        error_code: int,
        error_description: Optional[str] = None,
        data: Any = None,
    ) -> Dict[str, Any]:
        return _drop_none(
            {
                "id": int(request_id or 0),
                "error_code": int(error_code),
                "error_description": error_description if error_code else None,
                "data": data,
            }
        )


__all__ = ["RegosPayDealsIntegration"]
