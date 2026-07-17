from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time as dt_time, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import httpx

from clients.base import ClientBase
from config.settings import settings as app_settings
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from core.redis import (
    redis_error_contains,
    redis_acquire_lock,
    redis_delete_keys,
    redis_get_json,
    redis_is_enabled,
    redis_make_key,
    redis_release_lock,
    redis_set_json,
    redis_stream_ack_delete,
    redis_stream_add_with_ttl,
    redis_stream_group_create_with_ttl,
    redis_ops,
)
from core.scheduler import RegosSchedulerClient, SchedulerError
from schemas.api.common.base import LegalStatus
from schemas.api.common.filters import Filter, FilterOperator
from schemas.api.docs.doc_payment import (
    DocPaymentAddRequest,
    DocPaymentGetRequest,
    DocPaymentPerformRequest,
)
from schemas.api.integrations.connected_integration import ConnectedIntegrationGetRequest
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingRequest,
)
from schemas.api.references.account_operation_category import (
    AccountOperationCategoryGetRequest,
)
from schemas.api.references.field import (
    FieldAddRequest,
    FieldEntityTypeEnum,
    FieldGetRequest,
    FieldValueAdd,
)
from schemas.api.references.firm import FirmGetRequest
from schemas.api.references.partner import PartnerAddRequest, PartnerGetRequest
from schemas.api.references.partner_group import PartnerGroupGetRequest
from schemas.api.references.payment_type import PaymentTypeGetRequest
from schemas.scheduler import (
    AdapterSchedulerRequest,
    AdapterSchedulerUuidRequest,
    ScheduleAddRequest,
    ScheduleTaskSetStatusRequest,
    ScheduleTaskStatus,
)


logger = setup_logger("bank_ipak_yuli")

_INSTANCE_ID = uuid.uuid4().hex[:12]
_STREAM_WORKER_TASKS: Dict[int, asyncio.Task] = {}
_STREAM_WORKER_LOCK = asyncio.Lock()
_STREAM_TTL_TOUCH_TS: Dict[str, int] = {}
_STREAM_CLAIM_TS: Dict[str, int] = {}
_STREAM_GROUP_READY: set[str] = set()


BANK_HTTP_TIMEOUT = 30.0
BANK_DATE_FORMAT = "%d.%m.%Y"
DEFAULT_BANK_BASE_URL = "https://mb.ipakyulibank.uz:2713"
PAYMENT_ID_FIELD_RAW_KEY = "ipak_yuli_payment_id"
PAYMENT_ID_FIELD_KEY = f"field_{PAYMENT_ID_FIELD_RAW_KEY}"
PAYMENT_ID_FIELD_NAME = "Ipak Yuli payment ID"
PAYMENT_ID_FIELD_TYPE = "string"
DOCPAYMENT_DESCRIPTION_MAX_LENGTH = 300
SCHEDULER_HANDLER_ID = 7
REDIS_PREFIX = "biy"
SETTINGS_TTL_SEC = max(int(app_settings.redis_cache_ttl or 60), 60)
SETTINGS_LOCK_TTL_SEC = 30
SETTINGS_LOCK_WAIT_SEC = 5.0
RUN_LOCK_TTL_SEC = 30 * 60
RUN_LOCK_WAIT_SEC = 1.0
LOCAL_TZ = timezone(timedelta(hours=5))
SYNC_DIRECTIONS_ALL = "all"
SYNC_DIRECTIONS_INCOME = "income"
SYNC_DIRECTIONS_OUTCOME = "outcome"
SYNC_DIRECTIONS_VALUES = {
    SYNC_DIRECTIONS_ALL,
    SYNC_DIRECTIONS_INCOME,
    SYNC_DIRECTIONS_OUTCOME,
}


class BankIpakYuliError(Exception):
    def __init__(self, code: int, description: str) -> None:
        super().__init__(description)
        self.code = int(code)
        self.description = str(description)


@dataclass(frozen=True)
class RuntimeConfig:
    connected_integration_id: str
    bank_api_base_url: str
    bank_login: str
    bank_password: str
    bank_branch: str
    bank_account: str
    firm_id: int
    sync_payment_directions: str
    income_purpose_keywords: List[str]
    outcome_purpose_keywords: List[str]
    income_excluded_counterparty_inns: List[str]
    outcome_excluded_counterparty_inns: List[str]
    payment_type_id: int
    partner_group_id: int
    income_category_id: int
    outcome_category_id: int
    perform_after_create: bool
    lookback_days: int
    poll_from_time: Optional[str]
    poll_to_time: Optional[str]
    attached_user_id: Optional[int]


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _digits(value: Any) -> str:
    return "".join(ch for ch in _text(value) if ch.isdigit())


def _to_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(Decimal(str(value).strip()))
    except Exception:
        return default


def _to_optional_int(value: Any) -> Optional[int]:
    parsed = _to_int(value, 0)
    return parsed if parsed > 0 else None


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if not text:
        return default
    if text in {"1", "true", "yes", "y", "on", "да", "ha"}:
        return True
    if text in {"0", "false", "no", "n", "off", "нет", "yoq", "yo'q"}:
        return False
    return default


def _money_from_minor(value: Any) -> Decimal:
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        amount = Decimal("0")
    return (amount / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _normalize_settings(rows: Any) -> Dict[str, str]:
    result: Dict[str, str] = {}
    if not isinstance(rows, list):
        return result
    for row in rows:
        key = _text(getattr(row, "key", None)).lower()
        if key:
            result[key] = _text(getattr(row, "value", None))
    return result


def _setting(settings_map: Dict[str, str], key: str) -> str:
    return _text(settings_map.get(str(key).lower()))


def _parse_keywords(value: Any) -> List[str]:
    text = _text(value)
    if not text:
        return []
    raw_parts = []
    for line in text.replace(";", "\n").replace(",", "\n").splitlines():
        part = line.strip().casefold()
        if part:
            raw_parts.append(part)
    return sorted(set(raw_parts))


def _parse_identifiers(value: Any) -> List[str]:
    text = _text(value)
    if not text:
        return []
    raw_parts = []
    for line in text.replace(";", "\n").replace(",", "\n").splitlines():
        identifier = _digits(line)
        if identifier:
            raw_parts.append(identifier)
    return sorted(set(raw_parts))


def _truncate_text(value: Any, max_length: int) -> str:
    text = _text(value)
    if len(text) <= max_length:
        return text
    if max_length <= 3:
        return text[:max_length]
    return f"{text[: max_length - 3]}..."


def _normalize_sync_payment_directions(value: Any) -> str:
    text = _text(value, "All").casefold()
    aliases = {
        "all": SYNC_DIRECTIONS_ALL,
        "все": SYNC_DIRECTIONS_ALL,
        "income": SYNC_DIRECTIONS_INCOME,
        "incoming": SYNC_DIRECTIONS_INCOME,
        "in": SYNC_DIRECTIONS_INCOME,
        "входящие": SYNC_DIRECTIONS_INCOME,
        "outcome": SYNC_DIRECTIONS_OUTCOME,
        "outgoing": SYNC_DIRECTIONS_OUTCOME,
        "out": SYNC_DIRECTIONS_OUTCOME,
        "исходящие": SYNC_DIRECTIONS_OUTCOME,
    }
    return aliases.get(text, text)


def _parse_bank_date(value: Any, *, fallback: Optional[date] = None) -> date:
    parsed = _try_parse_bank_date(value)
    if parsed is not None:
        return parsed
    return fallback or datetime.now(LOCAL_TZ).date()


def _try_parse_bank_date(value: Any) -> Optional[date]:
    if isinstance(value, datetime):
        return value.astimezone(LOCAL_TZ).date() if value.tzinfo else value.date()
    if isinstance(value, date):
        return value
    text = _text(value)
    if text:
        try:
            return datetime.strptime(text[:10], BANK_DATE_FORMAT).date()
        except ValueError:
            pass
    return None


def _parse_bank_datetime(day_value: Any, time_value: Any = None) -> int:
    payment_date = _parse_bank_date(day_value)
    time_text = _text(time_value)
    parsed_time = dt_time(0, 0, 0)
    if time_text:
        for fmt in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M"):
            try:
                parsed = datetime.strptime(time_text[: len(fmt)], fmt)
                return int(parsed.replace(tzinfo=LOCAL_TZ).timestamp())
            except ValueError:
                pass
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                parsed_time = datetime.strptime(time_text[: len(fmt)], fmt).time()
                break
            except ValueError:
                pass
    return int(datetime.combine(payment_date, parsed_time, tzinfo=LOCAL_TZ).timestamp())


def _day_bounds_ts(value: date) -> Tuple[int, int]:
    start = datetime.combine(value, dt_time(0, 0, 0), tzinfo=LOCAL_TZ)
    end = start + timedelta(days=1) - timedelta(seconds=1)
    return int(start.timestamp()), int(end.timestamp())


def _format_bank_date(value: date) -> str:
    return value.strftime(BANK_DATE_FORMAT)


def _today() -> date:
    return datetime.now(LOCAL_TZ).date()


def _stable_json_hash(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _is_access_forbidden(value: Any) -> bool:
    text = _text(value).casefold()
    return "доступ запрещ" in text or "access denied" in text or "forbidden" in text


def _headers_for_log(headers: Any) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for key, value in dict(headers).items():
        key_text = str(key)
        value_text = _text(value)
        if key_text.lower() == "authorization":
            scheme = value_text.split(" ", 1)[0] if value_text else ""
            result[key_text] = f"{scheme} <redacted>" if scheme else "<redacted>"
        else:
            result[key_text] = value_text
    return result


def _result_new_id(response: Any, method: str) -> int:
    if not getattr(response, "ok", False):
        raise BankIpakYuliError(111321, f"{method} rejected: {getattr(response, 'result', None)}")
    result = getattr(response, "result", None)
    new_id = _to_int(getattr(result, "new_id", None), 0)
    if new_id <= 0:
        raise BankIpakYuliError(111322, f"{method} did not return new_id")
    return new_id


def _partner_legal_status(identifier: str) -> LegalStatus:
    return LegalStatus.Natural if len(identifier) == 14 else LegalStatus.Legal


def _counterparty_inn(row: Dict[str, Any], direction: int) -> str:
    if direction == 2:
        return _digits(row.get("inn_dt"))
    return _digits(row.get("inn_ct"))


def _direction_filter_key(direction: int) -> str:
    return SYNC_DIRECTIONS_INCOME if direction == 2 else SYNC_DIRECTIONS_OUTCOME


class IpakYuliBankClient:
    def __init__(self, runtime: RuntimeConfig) -> None:
        self.runtime = runtime
        self.base_url = runtime.bank_api_base_url.rstrip("/")

    async def get_account(self) -> List[Dict[str, Any]]:
        result = await self._post(
            "GetAcc1C",
            {
                "branch": self.runtime.bank_branch,
                "account": self.runtime.bank_account,
            },
        )
        return result if isinstance(result, list) else []

    async def get_statement(
        self,
        *,
        statement_date: date,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "branch": self.runtime.bank_branch,
            "account": self.runtime.bank_account,
            "date": _format_bank_date(statement_date),
        }
        if self.runtime.poll_from_time:
            payload["from_time"] = self.runtime.poll_from_time
        if self.runtime.poll_to_time:
            payload["to_time"] = self.runtime.poll_to_time
        result = await self._post("GetDoc1C", payload)
        return result if isinstance(result, dict) else {}

    async def _post(self, method: str, payload: Dict[str, Any]) -> Any:
        url = f"{self.base_url}/Mobile.svc/{method}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self._basic_token()}",
        }
        async with httpx.AsyncClient(timeout=BANK_HTTP_TIMEOUT) as client:
            response = await client.post(url, json=payload, headers=headers)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                if error.response.status_code in {401, 403}:
                    self._log_bank_access_forbidden(method, error.response, url, headers)
                raise
        try:
            data = response.json()
        except ValueError as error:
            raise BankIpakYuliError(111322, f"Ipak Yuli {method} returned invalid JSON") from error
        if not isinstance(data, dict):
            raise BankIpakYuliError(111322, f"Ipak Yuli {method} response must be an object")
        bank_error = data.get("error")
        if bank_error:
            code = _to_int(bank_error.get("code") if isinstance(bank_error, dict) else None, 111321)
            message = (
                _text(bank_error.get("message"))
                if isinstance(bank_error, dict)
                else _text(bank_error)
            )
            if _is_access_forbidden(message):
                self._log_bank_access_forbidden(method, response, url, headers)
            raise BankIpakYuliError(code, message or f"Ipak Yuli {method} failed")
        return data.get("result")

    def _basic_token(self) -> str:
        raw = f"{self.runtime.bank_login}:{self.runtime.bank_password}"
        return base64.b64encode(raw.encode("utf-8")).decode("ascii")

    def _log_bank_access_forbidden(
        self,
        method: str,
        response: httpx.Response,
        fallback_url: str,
        fallback_headers: Dict[str, str],
    ) -> None:
        request = response.request
        request_url = str(request.url) if request else fallback_url
        request_headers = _headers_for_log(request.headers if request else fallback_headers)
        logger.warning(
            "Ipak Yuli access forbidden: method=%s status_code=%s url=%s headers=%s",
            method,
            response.status_code,
            request_url,
            request_headers,
        )


class BankIpakYuliIntegration(ClientBase):
    integration_key = "bank_ipak_yuli"
    stream_group = "biyw"
    stream_read_block_ms = 5000
    stream_min_idle_ms = 60_000
    stream_claim_interval_sec = 30

    _local_run_lock = asyncio.Lock()

    def __init__(self) -> None:
        self.connected_integration_id: Optional[str] = None
        self._settings: Optional[Dict[str, str]] = None

    def _ci(self) -> str:
        return _text(self.connected_integration_id)

    def _redis_key(self, *parts: Any) -> str:
        return redis_make_key(REDIS_PREFIX, self._ci(), *parts)

    def _settings_cache_key(self) -> str:
        return self._redis_key("settings")

    def _settings_lock_key(self) -> str:
        return self._redis_key("settings_lock")

    def _run_lock_key(self) -> str:
        return self._redis_key("run")

    @classmethod
    def _stream_key(cls) -> str:
        return redis_make_key(REDIS_PREFIX, "scheduler")

    @classmethod
    def _stream_workers_count(cls) -> int:
        return max(int(app_settings.bank_ipak_yuli_stream_workers or 0), 1)

    @classmethod
    def _stream_batch_size(cls) -> int:
        return max(int(app_settings.bank_ipak_yuli_stream_batch_size or 0), 1)

    @classmethod
    def _stream_ttl_sec(cls) -> int:
        return max(int(app_settings.bank_ipak_yuli_stream_ttl or 0), 60)

    @classmethod
    async def _ensure_stream_group(cls, *, force: bool = False) -> None:
        stream_key = cls._stream_key()
        if not force and stream_key in _STREAM_GROUP_READY:
            return
        now_ts = int(time.time())
        await redis_stream_group_create_with_ttl(
            stream_key,
            cls.stream_group,
            ttl_sec=cls._stream_ttl_sec(),
            touch_ts_by_key=_STREAM_TTL_TOUCH_TS,
            now_ts=now_ts,
        )
        _STREAM_GROUP_READY.add(stream_key)

    @classmethod
    async def _enqueue_scheduler_task(cls, task_uuid: str) -> None:
        await cls._ensure_stream_group()
        now_ts = int(time.time())
        await redis_stream_add_with_ttl(
            cls._stream_key(),
            {
                "task_uuid": str(task_uuid),
                "enqueued_at": str(now_ts),
            },
            maxlen=max(int(app_settings.bank_ipak_yuli_stream_maxlen or 0), 1000),
            ttl_sec=cls._stream_ttl_sec(),
            touch_ts_by_key=_STREAM_TTL_TOUCH_TS,
            now_ts=now_ts,
        )
        await cls._ensure_stream_workers(ensure_group=False)

    @classmethod
    async def _ensure_stream_workers(cls, *, ensure_group: bool = True) -> None:
        if ensure_group:
            await cls._ensure_stream_group()
        async with _STREAM_WORKER_LOCK:
            for index in range(cls._stream_workers_count()):
                task = _STREAM_WORKER_TASKS.get(index)
                if task and not task.done():
                    continue
                _STREAM_WORKER_TASKS[index] = asyncio.create_task(cls._stream_worker_loop(index))

    @classmethod
    async def shutdown_all(cls) -> None:
        async with _STREAM_WORKER_LOCK:
            tasks = list(_STREAM_WORKER_TASKS.values())
            _STREAM_WORKER_TASKS.clear()
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        _STREAM_GROUP_READY.clear()
        _STREAM_TTL_TOUCH_TS.clear()
        _STREAM_CLAIM_TS.clear()

    @classmethod
    async def restore_active_connections(cls) -> Dict[str, int]:
        if not redis_is_enabled():
            return {"workers": 0}
        await cls._ensure_stream_workers()
        return {"workers": len(_STREAM_WORKER_TASKS)}

    async def connect(self, **_: Any) -> Dict[str, Any]:
        runtime = await self._runtime()
        async with RegosAPI(runtime.connected_integration_id) as api:
            field_status = await self._ensure_payment_id_field(api)
            await self._validate_regos_references(api, runtime)
        await IpakYuliBankClient(runtime).get_account()
        return {
            "status": "connected",
            "field": field_status,
            "bank_account": runtime.bank_account,
        }

    async def reconnect(self, **kwargs: Any) -> Dict[str, Any]:
        return await self.connect(**kwargs)

    async def update_settings(self, settings: Optional[dict] = None, **_: Any) -> Dict[str, Any]:
        self._settings = None
        if redis_is_enabled():
            await redis_delete_keys(self._settings_cache_key())
        return {"status": "settings updated", "settings": bool(settings)}

    async def disconnect(self, **_: Any) -> Dict[str, Any]:
        return {"status": "disconnected"}

    async def check(self, **_: Any) -> Dict[str, Any]:
        runtime = await self._runtime()
        accounts = await IpakYuliBankClient(runtime).get_account()
        async with RegosAPI(runtime.connected_integration_id) as api:
            await self._validate_regos_references(api, runtime)
        return {
            "status": "ok",
            "bank_account": runtime.bank_account,
            "accounts": len(accounts),
        }

    async def run(self, **_: Any) -> Dict[str, Any]:
        return await self.do_work()

    async def do_task(self, **_: Any) -> Dict[str, Any]:
        return await self.do_work()

    async def do_work(self) -> Dict[str, Any]:
        runtime = await self._runtime()
        return await self._with_run_lock(lambda: self._import_payments(runtime))

    async def schedule(self, **kwargs: Any) -> Any:
        request = AdapterSchedulerRequest.model_validate(kwargs)
        scheduler = RegosSchedulerClient()
        try:
            if request.uuid:
                await scheduler.schedule_delete(request.uuid)
            return await scheduler.schedule_add(
                ScheduleAddRequest(
                    handler_id=SCHEDULER_HANDLER_ID,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    api_login=request.api_login,
                    connected_integration_id=self._ci(),
                    data=request.data,
                    period_type=request.period_type,
                    period_value=request.period_value,
                    run_immediately=False,
                )
            )
        except SchedulerError as error:
            raise BankIpakYuliError(error.code, error.description) from error

    async def schedule_get(self, **kwargs: Any) -> Optional[Dict[str, Any]]:
        request = AdapterSchedulerUuidRequest.model_validate(kwargs)
        scheduler = RegosSchedulerClient()
        try:
            schedule = await scheduler.schedule_get_by_id(request.uuid)
        except SchedulerError as error:
            raise BankIpakYuliError(error.code, error.description) from error
        if schedule is None:
            return None
        return schedule.model_dump(mode="json", exclude_none=True)

    async def schedule_delete(self, **kwargs: Any) -> Dict[str, Any]:
        request = AdapterSchedulerUuidRequest.model_validate(kwargs)
        scheduler = RegosSchedulerClient()
        try:
            await scheduler.schedule_delete(request.uuid)
        except SchedulerError as error:
            raise BankIpakYuliError(error.code, error.description) from error
        return {"status": "deleted"}

    async def handle_external(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        method = _text(envelope.get("method")).upper()
        if method and method != "POST":
            raise BankIpakYuliError(111350, "POST method is required")

        body = envelope.get("body")
        if not isinstance(body, dict):
            raise BankIpakYuliError(111350, "JSON body is required")

        task_uuid = _text(body.get("uuid") or body.get("Uuid") or body.get("UUID")).strip()
        if not task_uuid:
            raise BankIpakYuliError(111350, "task uuid is required")

        await self._enqueue_scheduler_task(task_uuid)
        return {"status": "queued", "task_uuid": task_uuid}

    async def _process_scheduler_task(self, task_uuid: str) -> Dict[str, Any]:
        scheduler = RegosSchedulerClient()
        try:
            task = await scheduler.task_get_info(task_uuid)
        except SchedulerError as error:
            raise BankIpakYuliError(error.code, error.description) from error
        if task is None:
            raise BankIpakYuliError(111350, "scheduler task not found")
        task_ci = _text(task.connected_integration_id)
        if not task_ci:
            raise BankIpakYuliError(100, "connected_integration_id is required")
        self.connected_integration_id = task_ci

        await self._set_task_status(scheduler, task_uuid, ScheduleTaskStatus.Processing)
        try:
            result = await self.do_work()
        except Exception as error:
            logger.exception(
                "Ipak Yuli scheduler task failed before status Error: task_uuid=%s connected_integration_id=%s error=%s",
                task_uuid,
                task_ci,
                error,
            )
            await self._set_task_status_best_effort(scheduler, task_uuid, ScheduleTaskStatus.Error)
            raise
        await self._set_task_status(scheduler, task_uuid, ScheduleTaskStatus.Finished)
        return {
            "status": "ok",
            "task_uuid": task_uuid,
            "connected_integration_id": task_ci,
            "result": result,
        }

    async def _set_task_status(
        self,
        scheduler: RegosSchedulerClient,
        task_uuid: str,
        status: ScheduleTaskStatus,
    ) -> Any:
        try:
            return await scheduler.task_set_status(
                ScheduleTaskSetStatusRequest(uuid=task_uuid, status=status)
            )
        except SchedulerError as error:
            raise BankIpakYuliError(error.code, error.description) from error

    async def _set_task_status_best_effort(
        self,
        scheduler: RegosSchedulerClient,
        task_uuid: str,
        status: ScheduleTaskStatus,
    ) -> None:
        try:
            await self._set_task_status(scheduler, task_uuid, status)
        except Exception as error:
            logger.warning("Failed to set scheduler task status: uuid=%s error=%s", task_uuid, error)

    @classmethod
    async def _stream_worker_loop(cls, worker_index: int) -> None:
        stream_key = cls._stream_key()
        consumer = f"{_INSTANCE_ID}:biy:{worker_index}"
        logger.info("Ipak Yuli stream worker started: index=%s", worker_index)
        try:
            while True:
                try:
                    await cls._ensure_stream_group()
                    now_ts = int(time.time())
                    last_claim_ts = int(_STREAM_CLAIM_TS.get(stream_key) or 0)
                    if now_ts - last_claim_ts >= cls.stream_claim_interval_sec:
                        _STREAM_CLAIM_TS[stream_key] = now_ts
                        for entry_id, fields in await cls._process_claimed_entries(stream_key, consumer):
                            await cls._process_stream_entry(stream_key, entry_id, fields)

                    records = await redis_ops.xreadgroup(
                        groupname=cls.stream_group,
                        consumername=consumer,
                        streams={stream_key: ">"},
                        count=cls._stream_batch_size(),
                        block=cls.stream_read_block_ms,
                    )
                    if not records:
                        continue
                    for _, entries in records:
                        for entry_id, fields in entries:
                            await cls._process_stream_entry(stream_key, str(entry_id), fields)
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    if redis_error_contains(error, "NOGROUP"):
                        _STREAM_GROUP_READY.discard(stream_key)
                        await cls._ensure_stream_group(force=True)
                        continue
                    logger.exception(
                        "Ipak Yuli stream worker error: index=%s error=%s",
                        worker_index,
                        error,
                    )
                    await asyncio.sleep(1)
        finally:
            logger.info("Ipak Yuli stream worker stopped: index=%s", worker_index)
            async with _STREAM_WORKER_LOCK:
                current = _STREAM_WORKER_TASKS.get(worker_index)
                if current is asyncio.current_task():
                    _STREAM_WORKER_TASKS.pop(worker_index, None)

    @classmethod
    async def _process_claimed_entries(
        cls,
        stream_key: str,
        consumer: str,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        try:
            claimed_raw = await redis_ops.xautoclaim(
                stream_key,
                cls.stream_group,
                consumer,
                min_idle_time=cls.stream_min_idle_ms,
                start_id="0-0",
                count=cls._stream_batch_size(),
            )
        except Exception as error:
            if redis_error_contains(error, "NOGROUP"):
                _STREAM_GROUP_READY.discard(stream_key)
                await cls._ensure_stream_group(force=True)
                return []
            logger.warning("Ipak Yuli stream xautoclaim failed: stream=%s error=%s", stream_key, error)
            return []

        entries: List[Tuple[str, Dict[str, Any]]] = []
        if isinstance(claimed_raw, (list, tuple)) and len(claimed_raw) >= 2:
            entries = claimed_raw[1] or []
        return [
            (str(entry_id), fields if isinstance(fields, dict) else {})
            for entry_id, fields in entries
        ]

    @classmethod
    async def _process_stream_entry(
        cls,
        stream_key: str,
        entry_id: str,
        fields: Dict[str, Any],
    ) -> None:
        task_uuid = _text(fields.get("task_uuid") or fields.get("uuid")).strip()
        if not task_uuid:
            await redis_stream_ack_delete(stream_key, cls.stream_group, entry_id)
            return

        worker = cls()
        try:
            result = await worker._process_scheduler_task(task_uuid)
            logger.info("Ipak Yuli scheduler task processed: task_uuid=%s result=%s", task_uuid, result)
        except Exception as error:
            logger.exception("Ipak Yuli scheduler task failed: task_uuid=%s error=%s", task_uuid, error)
        finally:
            await redis_stream_ack_delete(stream_key, cls.stream_group, entry_id)

    async def _with_run_lock(self, work: Callable[[], Awaitable[Dict[str, Any]]]) -> Dict[str, Any]:
        if redis_is_enabled():
            token = await redis_acquire_lock(
                self._run_lock_key(),
                RUN_LOCK_TTL_SEC,
                wait_timeout_sec=RUN_LOCK_WAIT_SEC,
            )
            if not token:
                return {"status": "skipped", "reason": "already_running"}
            try:
                return await work()
            finally:
                await redis_release_lock(self._run_lock_key(), token)

        if self._local_run_lock.locked():
            return {"status": "skipped", "reason": "already_running"}
        async with self._local_run_lock:
            return await work()

    async def _import_payments(self, runtime: RuntimeConfig) -> Dict[str, Any]:
        bank = IpakYuliBankClient(runtime)
        dates = [
            _today() - timedelta(days=offset)
            for offset in range(max(int(runtime.lookback_days), 0) + 1)
        ]
        stats = {
            "status": "ok",
            "dates": [_format_bank_date(item) for item in dates],
            "received": 0,
            "matched": 0,
            "duplicates": 0,
            "excluded": 0,
            "created": 0,
            "performed": 0,
            "skipped": 0,
            "errors": 0,
        }

        async with RegosAPI(runtime.connected_integration_id) as api:
            await self._ensure_payment_id_field(api)
            logger.info(
                "Ipak Yuli import started: connected_integration_id=%s "
                "sync_payment_directions=%s lookback_days=%s dates=%s bank_account=%s "
                "perform_after_create=%s",
                runtime.connected_integration_id,
                runtime.sync_payment_directions,
                runtime.lookback_days,
                stats["dates"],
                runtime.bank_account,
                runtime.perform_after_create,
            )
            for statement_date in dates:
                statement = await bank.get_statement(statement_date=statement_date)
                operation_day = _try_parse_bank_date(
                    statement.get("oper_day") if isinstance(statement, dict) else None
                ) or statement_date
                if operation_day != statement_date:
                    logger.info(
                        "Ipak Yuli statement oper_day differs from requested date: requested_date=%s oper_day=%s",
                        _format_bank_date(statement_date),
                        _format_bank_date(operation_day),
                    )
                rows = statement.get("content") if isinstance(statement, dict) else None
                if not isinstance(rows, list):
                    continue
                stats["received"] += len(rows)
                for row in rows:
                    if not isinstance(row, dict):
                        stats["skipped"] += 1
                        continue
                    try:
                        outcome = await self._import_payment_row(
                            api=api,
                            runtime=runtime,
                            row=row,
                            statement_date=operation_day,
                        )
                    except Exception as error:
                        stats["errors"] += 1
                        logger.exception("Failed to import Ipak Yuli payment: error=%s row=%s", error, row)
                        continue
                    if outcome not in {"skipped", "excluded"}:
                        stats["matched"] += 1
                    if outcome == "performed":
                        stats["created"] += 1
                        stats["performed"] += 1
                    else:
                        stats[outcome] = int(stats.get(outcome, 0)) + 1
        stats["finished_at"] = int(time.time())
        return stats

    async def _import_payment_row(
        self,
        *,
        api: RegosAPI,
        runtime: RuntimeConfig,
        row: Dict[str, Any],
        statement_date: date,
    ) -> str:
        if _to_int(row.get("state"), 0) != 3:
            return "skipped"
        row_value_date = _try_parse_bank_date(row.get("vdate"))
        if row_value_date and row_value_date != statement_date:
            logger.info(
                "Skipping Ipak Yuli payment by value date mismatch: statement_date=%s "
                "vdate=%s ddate=%s bank_dir=%s num=%s general_id=%s",
                _format_bank_date(statement_date),
                _format_bank_date(row_value_date),
                _text(row.get("ddate")),
                _text(row.get("dir")),
                _text(row.get("num")),
                _text(row.get("general_id")),
            )
            return "skipped"
        direction = _to_int(row.get("dir"), 0)
        if direction not in {1, 2}:
            return "skipped"
        if not self._direction_enabled(runtime, direction):
            logger.info(
                "Skipping Ipak Yuli payment by direction: sync_payment_directions=%s "
                "direction=%s bank_dir=%s account=%s acc_dt=%s acc_ct=%s num=%s general_id=%s",
                runtime.sync_payment_directions,
                direction,
                _text(row.get("dir")),
                runtime.bank_account,
                _text(row.get("acc_dt")),
                _text(row.get("acc_ct")),
                _text(row.get("num")),
                _text(row.get("general_id")),
            )
            return "skipped"
        purpose = _text(row.get("purpose"))
        if not self._purpose_matches(runtime, direction, purpose):
            return "skipped"
        counterparty_inn = _counterparty_inn(row, direction)
        if counterparty_inn and counterparty_inn in self._excluded_inns(runtime, direction):
            logger.info(
                "Skipping Ipak Yuli payment by excluded counterparty inn: direction=%s inn=%s",
                direction,
                counterparty_inn,
            )
            return "excluded"

        external_payment_id = self._external_payment_id(runtime, row, statement_date)
        if await self._payment_exists(api, runtime, external_payment_id, statement_date):
            return "duplicates"

        partner_id = await self._resolve_partner(api, runtime, row, direction)
        category_id = runtime.income_category_id if direction == 2 else runtime.outcome_category_id
        amount = _money_from_minor(row.get("amount"))
        if amount <= 0:
            return "skipped"

        payment_date = (
            _try_parse_bank_date(row.get("vdate"))
            or _try_parse_bank_date(row.get("ddate"))
            or statement_date
        )
        description = self._payment_description(row, external_payment_id)
        add_response = await api.docs.doc_payment.add(
            DocPaymentAddRequest(
                date=_parse_bank_datetime(payment_date, row.get("time")),
                type_id=runtime.payment_type_id,
                firm_id=runtime.firm_id,
                partner_id=partner_id,
                category_id=category_id,
                amount=amount,
                exchange_rate=Decimal("1"),
                description=description,
                attached_user_id=runtime.attached_user_id,
                fields=[
                    FieldValueAdd(
                        key=PAYMENT_ID_FIELD_KEY,
                        value=external_payment_id,
                    )
                ],
            )
        )
        payment_id = _result_new_id(add_response, "DocPayment/Add")
        if runtime.perform_after_create:
            perform_response = await api.docs.doc_payment.perform(
                DocPaymentPerformRequest(id=payment_id)
            )
            if not getattr(perform_response, "ok", False):
                raise BankIpakYuliError(
                    111321,
                    f"DocPayment/Perform rejected: {getattr(perform_response, 'result', None)}",
                )
            return "performed"
        return "created"

    async def _payment_exists(
        self,
        api: RegosAPI,
        runtime: RuntimeConfig,
        external_payment_id: str,
        statement_date: date,
    ) -> bool:
        start_date, end_date = _day_bounds_ts(statement_date)
        response = await api.docs.doc_payment.get(
            DocPaymentGetRequest(
                start_date=start_date,
                end_date=end_date,
                firm_ids=[runtime.firm_id],
                filters=[
                    Filter(
                        field=PAYMENT_ID_FIELD_KEY,
                        operator=FilterOperator.Equal,
                        value=external_payment_id,
                    )
                ],
                deleted_mark=False,
                limit=1,
                offset=0,
            )
        )
        if not getattr(response, "ok", False):
            raise BankIpakYuliError(111321, "DocPayment/Get by Ipak Yuli payment id failed")
        return bool(getattr(response, "result", None) or [])

    async def _resolve_partner(
        self,
        api: RegosAPI,
        runtime: RuntimeConfig,
        row: Dict[str, Any],
        direction: int,
    ) -> int:
        inn = _counterparty_inn(row, direction)
        if direction == 2:
            name = _text(row.get("name_dt"), inn or "Ipak Yuli payer")
            account = _text(row.get("acc_dt"))
            mfo = _text(row.get("mfo_dt"))
        else:
            name = _text(row.get("name_ct"), inn or "Ipak Yuli recipient")
            account = _text(row.get("acc_ct"))
            mfo = _text(row.get("mfo_ct"))

        search = inn or name
        response = await api.references.partner.get(
            PartnerGetRequest(
                search=search,
                deleted_mark=False,
                limit=10,
                offset=0,
            )
        )
        if not getattr(response, "ok", False):
            raise BankIpakYuliError(111321, "Partner/Get failed")
        rows = getattr(response, "result", None) or []
        if inn:
            for partner in rows:
                if _digits(getattr(partner, "inn", "")) == inn:
                    partner_id = _to_int(getattr(partner, "id", None), 0)
                    if partner_id > 0:
                        return partner_id
        if not inn and rows:
            partner_id = _to_int(getattr(rows[0], "id", None), 0)
            if partner_id > 0:
                return partner_id

        add_response = await api.references.partner.add(
            PartnerAddRequest(
                group_id=runtime.partner_group_id,
                legal_status=_partner_legal_status(inn),
                name=name,
                fullname=name,
                inn=inn or None,
                rs=account or None,
                mfo=mfo or None,
            )
        )
        return _result_new_id(add_response, "Partner/Add")

    async def _runtime(self) -> RuntimeConfig:
        ci = self._ci()
        if not ci:
            raise BankIpakYuliError(100, "connected_integration_id is required")
        settings_map = await self._load_settings()
        missing = [
            key
            for key in (
                "bank_login",
                "bank_password",
                "bank_branch",
                "bank_account",
                "firm_id",
                "payment_type_id",
                "partner_group_id",
                "income_category_id",
                "outcome_category_id",
                "perform_after_create",
            )
            if not _setting(settings_map, key)
        ]
        if missing:
            raise BankIpakYuliError(111350, f"Missing settings: {', '.join(missing)}")
        income_keywords = _parse_keywords(_setting(settings_map, "income_purpose_keywords"))
        outcome_keywords = _parse_keywords(_setting(settings_map, "outcome_purpose_keywords"))
        income_exclusions = _parse_identifiers(
            _setting(settings_map, "income_excluded_counterparty_inns")
        )
        outcome_exclusions = _parse_identifiers(
            _setting(settings_map, "outcome_excluded_counterparty_inns")
        )
        runtime = RuntimeConfig(
            connected_integration_id=ci,
            bank_api_base_url=_setting(settings_map, "bank_api_base_url") or DEFAULT_BANK_BASE_URL,
            bank_login=_setting(settings_map, "bank_login"),
            bank_password=_setting(settings_map, "bank_password"),
            bank_branch=_setting(settings_map, "bank_branch"),
            bank_account=_setting(settings_map, "bank_account"),
            firm_id=_to_int(_setting(settings_map, "firm_id")),
            sync_payment_directions=_normalize_sync_payment_directions(
                _setting(settings_map, "sync_payment_directions")
            ),
            income_purpose_keywords=income_keywords,
            outcome_purpose_keywords=outcome_keywords,
            income_excluded_counterparty_inns=income_exclusions,
            outcome_excluded_counterparty_inns=outcome_exclusions,
            payment_type_id=_to_int(_setting(settings_map, "payment_type_id")),
            partner_group_id=_to_int(_setting(settings_map, "partner_group_id")),
            income_category_id=_to_int(_setting(settings_map, "income_category_id")),
            outcome_category_id=_to_int(_setting(settings_map, "outcome_category_id")),
            perform_after_create=_to_bool(_setting(settings_map, "perform_after_create"), False),
            lookback_days=max(_to_int(_setting(settings_map, "lookback_days"), 1), 0),
            poll_from_time=_text(_setting(settings_map, "poll_from_time")) or None,
            poll_to_time=_text(_setting(settings_map, "poll_to_time")) or None,
            attached_user_id=_to_optional_int(_setting(settings_map, "attached_user_id")),
        )
        self._validate_runtime(runtime)
        return runtime

    def _validate_runtime(self, runtime: RuntimeConfig) -> None:
        if runtime.sync_payment_directions not in SYNC_DIRECTIONS_VALUES:
            raise BankIpakYuliError(
                111350,
                "sync_payment_directions must be one of: All, Income, Outcome",
            )
        if runtime.firm_id <= 0:
            raise BankIpakYuliError(111350, "firm_id must be positive")
        for key, value in (
            ("payment_type_id", runtime.payment_type_id),
            ("partner_group_id", runtime.partner_group_id),
            ("income_category_id", runtime.income_category_id),
            ("outcome_category_id", runtime.outcome_category_id),
        ):
            if value <= 0:
                raise BankIpakYuliError(111350, f"{key} must be positive")

    async def _load_settings(self) -> Dict[str, str]:
        if self._settings is not None:
            return self._settings
        if not redis_is_enabled():
            self._settings = await self._load_settings_from_api()
            return self._settings

        cached = await redis_get_json(self._settings_cache_key())
        if isinstance(cached, dict):
            self._settings = {str(k).lower(): _text(v) for k, v in cached.items()}
            return self._settings

        lock_token = await redis_acquire_lock(
            self._settings_lock_key(),
            SETTINGS_LOCK_TTL_SEC,
            wait_timeout_sec=SETTINGS_LOCK_WAIT_SEC,
        )
        if not lock_token:
            raise BankIpakYuliError(111350, "settings cache lock timeout")
        try:
            cached = await redis_get_json(self._settings_cache_key())
            if isinstance(cached, dict):
                self._settings = {str(k).lower(): _text(v) for k, v in cached.items()}
                return self._settings

            self._settings = await self._load_settings_from_api()
            await redis_set_json(self._settings_cache_key(), self._settings, SETTINGS_TTL_SEC)
            return self._settings
        finally:
            await redis_release_lock(self._settings_lock_key(), lock_token)

    async def _load_settings_from_api(self) -> Dict[str, str]:
        async with RegosAPI(self._ci()) as api:
            response = await api.integrations.connected_integration_setting.get(
                ConnectedIntegrationSettingRequest(connected_integration_id=self._ci())
            )
        if not getattr(response, "ok", False):
            raise BankIpakYuliError(111350, "ConnectedIntegrationSetting/Get failed")
        return _normalize_settings(getattr(response, "result", None))

    async def _validate_regos_references(self, api: RegosAPI, runtime: RuntimeConfig) -> None:
        connected_response = await api.integrations.connected_integration.get(
            ConnectedIntegrationGetRequest(
                connected_integration_ids=[runtime.connected_integration_id],
                include_name=False,
                include_schedule=False,
            )
        )
        if not getattr(connected_response, "ok", False):
            raise BankIpakYuliError(111350, "ConnectedIntegration/Get failed")
        connected_rows = getattr(connected_response, "result", None) or []
        if connected_rows and getattr(connected_rows[0], "is_active", None) is False:
            raise BankIpakYuliError(111350, "connected integration is inactive")

        await self._ensure_exists(
            "Firm/Get",
            api.references.firm.get(FirmGetRequest(ids=[runtime.firm_id], limit=1)),
        )
        await self._ensure_exists(
            "PaymentType/Get",
            api.references.payment_type.get(PaymentTypeGetRequest(ids=[runtime.payment_type_id])),
        )
        await self._ensure_exists(
            "PartnerGroup/Get",
            api.references.partner_group.get(PartnerGroupGetRequest(ids=[runtime.partner_group_id])),
        )
        income = await self._ensure_exists(
            "AccountOperationCategory/Get income",
            api.references.account_operation_category.get(
                AccountOperationCategoryGetRequest(ids=[runtime.income_category_id], limit=1)
            ),
        )
        outcome = await self._ensure_exists(
            "AccountOperationCategory/Get outcome",
            api.references.account_operation_category.get(
                AccountOperationCategoryGetRequest(ids=[runtime.outcome_category_id], limit=1)
            ),
        )
        if getattr(income[0], "positive", None) is False:
            raise BankIpakYuliError(111350, "income_category_id must point to income category")
        if getattr(outcome[0], "positive", None) is True:
            raise BankIpakYuliError(111350, "outcome_category_id must point to expense category")

    async def _ensure_exists(self, method: str, awaitable: Any) -> List[Any]:
        response = await awaitable
        if not getattr(response, "ok", False):
            raise BankIpakYuliError(111350, f"{method} failed")
        rows = getattr(response, "result", None) or []
        if not rows:
            raise BankIpakYuliError(111350, f"{method} returned no rows")
        return rows

    async def _ensure_payment_id_field(self, api: RegosAPI) -> Dict[str, str]:
        response = await api.references.field.get(
            FieldGetRequest(
                entity_type=FieldEntityTypeEnum.DocPayment,
                keys=[PAYMENT_ID_FIELD_KEY],
            )
        )
        if not getattr(response, "ok", False):
            raise BankIpakYuliError(111350, "Field/Get failed")
        expected = PAYMENT_ID_FIELD_KEY.lower()
        for row in getattr(response, "result", None) or []:
            if _text(getattr(row, "key", None)).lower() == expected:
                return {"key": PAYMENT_ID_FIELD_KEY, "status": "exists"}
        add_response = await api.references.field.add(
            FieldAddRequest(
                key=PAYMENT_ID_FIELD_RAW_KEY,
                name=PAYMENT_ID_FIELD_NAME,
                entity_type=FieldEntityTypeEnum.DocPayment,
                data_type=PAYMENT_ID_FIELD_TYPE,
                required=False,
            )
        )
        if not getattr(add_response, "ok", False):
            raise BankIpakYuliError(111350, f"Field/Add failed: {getattr(add_response, 'result', None)}")
        return {"key": PAYMENT_ID_FIELD_KEY, "status": "created"}

    def _direction_enabled(self, runtime: RuntimeConfig, direction: int) -> bool:
        direction_key = _direction_filter_key(direction)
        return runtime.sync_payment_directions in {SYNC_DIRECTIONS_ALL, direction_key}

    def _keywords(self, runtime: RuntimeConfig, direction: int) -> List[str]:
        if direction == 2:
            return runtime.income_purpose_keywords
        return runtime.outcome_purpose_keywords

    def _excluded_inns(self, runtime: RuntimeConfig, direction: int) -> List[str]:
        if direction == 2:
            return runtime.income_excluded_counterparty_inns
        return runtime.outcome_excluded_counterparty_inns

    def _purpose_matches(self, runtime: RuntimeConfig, direction: int, purpose: str) -> bool:
        keywords = self._keywords(runtime, direction)
        if not keywords:
            return True
        normalized = " ".join(_text(purpose).casefold().split())
        if not normalized:
            return False
        return any(keyword in normalized for keyword in keywords)

    def _external_payment_id(
        self,
        runtime: RuntimeConfig,
        row: Dict[str, Any],
        statement_date: date,
    ) -> str:
        b2_id = _text(row.get("b2_id"))
        if b2_id:
            return f"b2:{b2_id}"
        general_id = _text(row.get("general_id"))
        branch = _text(row.get("branch"), runtime.bank_branch)
        if general_id:
            return f"nci:{branch}:{general_id}"
        payload = {
            "account": runtime.bank_account,
            "date": _format_bank_date(statement_date),
            "time": _text(row.get("time")),
            "num": _text(row.get("num")),
            "amount": _text(row.get("amount")),
            "dir": _text(row.get("dir")),
            "inn_ct": _digits(row.get("inn_ct")),
            "inn_dt": _digits(row.get("inn_dt")),
        }
        return f"hash:{_stable_json_hash(payload)}"

    def _payment_description(
        self,
        row: Dict[str, Any],
        external_payment_id: str,
    ) -> str:
        purpose = _text(row.get("purpose"))
        if purpose:
            return _truncate_text(purpose, DOCPAYMENT_DESCRIPTION_MAX_LENGTH)
        return _truncate_text(
            f"Ipak Yuli payment {external_payment_id}",
            DOCPAYMENT_DESCRIPTION_MAX_LENGTH,
        )


__all__ = ["BankIpakYuliIntegration"]
