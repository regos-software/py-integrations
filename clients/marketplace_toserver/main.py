from __future__ import annotations

import asyncio
import uuid
import time
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi.encoders import jsonable_encoder

from clients.base import ClientBase
from config.settings import settings
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from core.redis import (
    redis_error_contains,
    redis_acquire_lock,
    redis_delete_keys,
    redis_get_json,
    redis_incr_with_ttl,
    redis_make_key,
    redis_release_lock,
    redis_set_json,
    redis_stream_ack_delete,
    redis_stream_add_with_ttl,
    redis_stream_group_create_with_ttl,
    redis_ops,
)
from core.scheduler import RegosSchedulerClient, SchedulerError
from schemas.api.integrations.connected_integration import ConnectedIntegrationGetRequest
from schemas.api.integrations.connected_integration_setting import ConnectedIntegrationSettingRequest
from schemas.api.references.item import (
    ItemGetCurrentQuantityRequest,
    ItemGetExtImageSize,
    ItemGetExtRequest,
)
from schemas.api.references.stock import StockGetRequest
from schemas.scheduler import (
    AdapterSchedulerRequest,
    AdapterSchedulerUuidRequest,
    ScheduleAddRequest,
    ScheduleTaskSetStatusRequest,
    ScheduleTaskStatus,
)


logger = setup_logger("marketplace_toserver")

_INSTANCE_ID = uuid.uuid4().hex[:12]
_STREAM_WORKER_TASKS: Dict[int, asyncio.Task] = {}
_STREAM_WORKER_LOCK = asyncio.Lock()
_STREAM_TTL_TOUCH_TS: Dict[str, int] = {}
_STREAM_CLAIM_TS: Dict[str, int] = {}
_STREAM_GROUP_READY: set[str] = set()


class MarketplaceToServerError(Exception):
    def __init__(self, code: int, description: str) -> None:
        super().__init__(description)
        self.code = int(code)
        self.description = str(description)


def _to_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        text = str(value).strip()
        if not text:
            return default
        return int(Decimal(text))
    except Exception:
        return default


def _to_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    if value is None:
        return default
    try:
        text = str(value).strip().replace(",", ".")
        if not text:
            return default
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return default


def _text(value: Any, default: str = "") -> str:
    return default if value is None else str(value)


def _nested(data: Any, path: str, default: Any = None) -> Any:
    current = data
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
        if current is None:
            return default
    return current


def _normalize_settings_map(raw: Dict[str, Any]) -> Dict[str, str]:
    normalized: Dict[str, str] = {}
    for key, value in (raw or {}).items():
        normalized_key = str(key or "").strip().lower()
        if normalized_key:
            normalized[normalized_key] = str(value or "").strip()
    return normalized


class MarketplaceToServerIntegration(ClientBase):
    integration_key = "marketplace_toserver"
    redis_prefix = "mp:ts"
    stream_group = "mtsw"
    stream_read_block_ms = 5000
    stream_min_idle_ms = 60_000
    stream_claim_interval_sec = 30

    def __init__(self) -> None:
        self.connected_integration_id: Optional[str] = None
        self._settings: Optional[Dict[str, str]] = None

    def _ci(self) -> str:
        return str(self.connected_integration_id or "").strip()

    def _redis_key(self, *parts: Any) -> str:
        return redis_make_key(self.redis_prefix, self._ci(), *parts)

    def _active_cache_key(self) -> str:
        return self._redis_key("a")

    def _settings_cache_key(self) -> str:
        return self._redis_key("s")

    def _settings_lock_key(self) -> str:
        return self._redis_key("sl")

    def _run_lock_key(self) -> str:
        return self._redis_key("rl")

    def _schedule_auth_error_key(self, schedule_uuid: str) -> str:
        return self._redis_key("sae", schedule_uuid)

    @classmethod
    def _stream_key(cls) -> str:
        return redis_make_key(cls.redis_prefix, "scheduler")

    @classmethod
    def _stream_workers_count(cls) -> int:
        return max(int(settings.marketplace_toserver_stream_workers or 0), 1)

    @classmethod
    def _stream_batch_size(cls) -> int:
        return max(int(settings.marketplace_toserver_stream_batch_size or 0), 1)

    @classmethod
    def _stream_ttl_sec(cls) -> int:
        return max(int(settings.marketplace_toserver_stream_ttl or 0), 60)

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
            maxlen=max(int(settings.marketplace_toserver_stream_maxlen or 0), 1000),
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
        await cls._ensure_stream_workers()
        return {"workers": len(_STREAM_WORKER_TASKS)}

    async def check(self) -> Dict[str, Any]:
        await self._ensure_active()
        settings_map = await self._load_settings()
        endpoint = _text(settings_map.get("endpoint")).strip()
        if not endpoint:
            raise MarketplaceToServerError(111350, "ENDPOINT is not set")

        async with httpx.AsyncClient(timeout=settings.marketplace_external_timeout) as client:
            response = await client.post(
                endpoint,
                json=[],
                auth=self._basic_auth(settings_map),
            )
        if response.status_code == 400:
            return {"status": "reachable_bad_request"}
        response.raise_for_status()
        return {"status": "ok"}

    async def update_settings(self, settings: Optional[dict] = None, **kwargs: Any) -> Dict[str, Any]:
        if not self._ci():
            return {"status": "error", "error": "connected_integration_id is required"}
        self._settings = None
        await redis_delete_keys(self._active_cache_key(), self._settings_cache_key())
        return {"status": "settings updated"}

    async def do_work(self) -> Dict[str, Any]:
        await self._ensure_active()
        lock_token = await redis_acquire_lock(self._run_lock_key(), settings.marketplace_toserver_lock_ttl)
        if not lock_token:
            return {"status": "skipped", "reason": "already_running"}
        try:
            settings_map = await self._load_settings()
            if str(settings_map.get("unload_enabled", "1")).strip() == "0":
                return {"status": "skipped", "reason": "unload_disabled"}

            endpoint = _text(settings_map.get("endpoint")).strip()
            if not endpoint:
                raise MarketplaceToServerError(111350, "ENDPOINT is not set")

            firm_id = _to_int(settings_map.get("firm"), -1)
            price_type_id = _to_int(settings_map.get("price_type"), -1)
            stock_ids = self._parse_ids(settings_map.get("stock_id") or settings_map.get("stock_ids"))

            stocks = await self._get_stocks(firm_id=firm_id, stock_ids=stock_ids)
            if not stocks:
                raise MarketplaceToServerError(111422, f"{self.integration_key} stocks is not specified")
            if not stock_ids:
                stock_ids = sorted({_to_int(stock.get("id")) for stock in stocks if _to_int(stock.get("id")) > 0})
            if not stock_ids:
                raise MarketplaceToServerError(111422, f"{self.integration_key} stock_ids is not specified")

            sent_items = 0
            offset = 0
            total = 0
            image_size = self._image_size(settings_map.get("image_size"))
            async with httpx.AsyncClient(timeout=settings.marketplace_external_timeout) as client:
                await self._preflight(client, endpoint, settings_map)
                while True:
                    item_ext_rows, next_offset, response_total = await self._item_ext_page(
                        price_type_id=price_type_id,
                        image_size=image_size,
                        offset=offset,
                    )
                    if not item_ext_rows:
                        break

                    item_ids = [_to_int(_nested(row, "item.id")) for row in item_ext_rows]
                    item_ids = [item_id for item_id in item_ids if item_id > 0]
                    qty_rows = await self._current_quantities(item_ids=item_ids, stock_ids=stock_ids)
                    payload = self._build_payload(item_ext_rows, qty_rows, stocks)
                    if payload:
                        post_response = await client.post(
                            endpoint,
                            json=jsonable_encoder(payload),
                            auth=self._basic_auth(settings_map),
                        )
                        post_response.raise_for_status()
                        sent_items += len(payload)

                    total = _to_int(response_total, total)
                    if next_offset == 0 or next_offset == offset or (total > 0 and next_offset >= total):
                        break
                    offset = next_offset

            return {
                "status": "ok",
                "items_sent": sent_items,
                "finished_at": int(time.time()),
            }
        finally:
            await redis_release_lock(self._run_lock_key(), lock_token)

    async def do_task(self, **_: Any) -> Dict[str, Any]:
        return await self.do_work()

    async def run(self, **_: Any) -> Dict[str, Any]:
        return await self.do_work()

    async def schedule(self, **kwargs: Any) -> Any:
        request = AdapterSchedulerRequest.model_validate(kwargs)
        await self._ensure_scheduled()
        scheduler = RegosSchedulerClient()
        try:
            if request.uuid:
                await scheduler.schedule_delete(request.uuid)
            return await scheduler.schedule_add(
                ScheduleAddRequest(
                    handler_id=1,
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
            raise MarketplaceToServerError(error.code, error.description) from error

    async def schedule_get(self, **kwargs: Any) -> Optional[Dict[str, Any]]:
        request = AdapterSchedulerUuidRequest.model_validate(kwargs)
        await self._ensure_scheduled()
        scheduler = RegosSchedulerClient()
        try:
            schedule = await scheduler.schedule_get_by_id(request.uuid)
        except SchedulerError as error:
            raise MarketplaceToServerError(error.code, error.description) from error
        if schedule is None:
            return None
        return schedule.model_dump(mode="json", exclude_none=True)

    async def schedule_delete(self, **kwargs: Any) -> Dict[str, Any]:
        request = AdapterSchedulerUuidRequest.model_validate(kwargs)
        await self._ensure_scheduled()
        scheduler = RegosSchedulerClient()
        try:
            await scheduler.schedule_delete(request.uuid)
        except SchedulerError as error:
            raise MarketplaceToServerError(error.code, error.description) from error
        return {"status": "deleted"}

    async def handle_external(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        method = str(envelope.get("method") or "").upper()
        if method and method != "POST":
            raise MarketplaceToServerError(111350, "POST method is required")

        body = envelope.get("body")
        if not isinstance(body, dict):
            raise MarketplaceToServerError(111350, "JSON body is required")

        task_uuid = _text(body.get("uuid") or body.get("Uuid") or body.get("UUID")).strip()
        if not task_uuid:
            raise MarketplaceToServerError(111350, "task uuid is required")

        await self._enqueue_scheduler_task(task_uuid)
        return {"status": "queued", "task_uuid": task_uuid}

    async def _process_scheduler_task(
        self,
        scheduler: RegosSchedulerClient,
        task_uuid: str,
    ) -> Dict[str, Any]:
        try:
            task = await scheduler.task_get_info(task_uuid)
        except SchedulerError as error:
            raise MarketplaceToServerError(error.code, error.description) from error
        if task is None:
            raise MarketplaceToServerError(111350, "scheduler task not found")

        task_ci = _text(task.connected_integration_id).strip()
        if not task_ci:
            raise MarketplaceToServerError(100, "connected_integration_id is required")

        self.connected_integration_id = task_ci
        schedule_uuid = _text(task.schedule_uuid).strip()
        await self._set_scheduler_task_status(scheduler, task_uuid, ScheduleTaskStatus.Processing)
        try:
            result = await self.do_work()
        except Exception as error:
            try:
                await self._set_scheduler_task_status(scheduler, task_uuid, ScheduleTaskStatus.Error)
            except Exception as status_error:
                logger.warning("Failed to mark scheduler task as Error: uuid=%s error=%s", task_uuid, status_error)
            disabled = await self._disable_broken_schedule_if_needed(
                scheduler=scheduler,
                task_uuid=task_uuid,
                schedule_uuid=schedule_uuid,
                error=error,
            )
            if disabled is not None:
                return disabled
            return {
                "status": "error",
                "task_uuid": task_uuid,
                "schedule_uuid": schedule_uuid,
                "connected_integration_id": task_ci,
                "error": str(error),
            }

        if schedule_uuid:
            await redis_delete_keys(self._schedule_auth_error_key(schedule_uuid))
        await self._set_scheduler_task_status(scheduler, task_uuid, ScheduleTaskStatus.Finished)
        return {
            "status": "ok",
            "task_uuid": task_uuid,
            "connected_integration_id": task_ci,
            "result": result,
        }

    async def _set_scheduler_task_status(
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
            raise MarketplaceToServerError(error.code, error.description) from error

    @classmethod
    async def _stream_worker_loop(cls, worker_index: int) -> None:
        stream_key = cls._stream_key()
        consumer = f"{_INSTANCE_ID}:mts:{worker_index}"
        logger.info("Marketplace toserver stream worker started: index=%s", worker_index)
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
                        "Marketplace toserver stream worker error: index=%s error=%s",
                        worker_index,
                        error,
                    )
                    await asyncio.sleep(1)
        finally:
            logger.info("Marketplace toserver stream worker stopped: index=%s", worker_index)
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
            logger.warning("Marketplace toserver stream xautoclaim failed: stream=%s error=%s", stream_key, error)
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

        scheduler = RegosSchedulerClient()
        worker = cls()
        try:
            result = await worker._process_scheduler_task(scheduler, task_uuid)
            logger.info("Marketplace toserver scheduler task processed: task_uuid=%s result=%s", task_uuid, result)
        except Exception as error:
            logger.warning("Marketplace toserver scheduler task failed: task_uuid=%s error=%s", task_uuid, error)
        finally:
            await redis_stream_ack_delete(stream_key, cls.stream_group, entry_id)

    async def _disable_broken_schedule_if_needed(
        self,
        *,
        scheduler: RegosSchedulerClient,
        task_uuid: str,
        schedule_uuid: str,
        error: Exception,
    ) -> Optional[Dict[str, Any]]:
        if not schedule_uuid or not self._is_regos_auth_error(error):
            return None

        threshold = max(
            int(settings.marketplace_toserver_disable_schedule_after_auth_errors or 1),
            1,
        )
        counter_key = self._schedule_auth_error_key(schedule_uuid)
        try:
            failures = await redis_incr_with_ttl(
                counter_key,
                settings.marketplace_toserver_auth_error_ttl,
            )
        except Exception as counter_error:
            logger.warning(
                "Failed to increment scheduler auth error counter: ci=%s schedule_uuid=%s task_uuid=%s error=%s",
                self._ci(),
                schedule_uuid,
                task_uuid,
                counter_error,
            )
            return None

        if failures < threshold:
            logger.warning(
                "Scheduler task failed with REGOS auth error: ci=%s schedule_uuid=%s task_uuid=%s failures=%s/%s error=%s",
                self._ci(),
                schedule_uuid,
                task_uuid,
                failures,
                threshold,
                error,
            )
            return None

        try:
            await scheduler.schedule_delete(schedule_uuid)
        except SchedulerError as delete_error:
            logger.warning(
                "Failed to delete broken scheduler schedule: ci=%s schedule_uuid=%s task_uuid=%s error=%s",
                self._ci(),
                schedule_uuid,
                task_uuid,
                delete_error.description,
            )
            return None

        await redis_delete_keys(counter_key)
        logger.warning(
            "Deleted broken scheduler schedule after REGOS auth errors: ci=%s schedule_uuid=%s task_uuid=%s failures=%s error=%s",
            self._ci(),
            schedule_uuid,
            task_uuid,
            failures,
            error,
        )
        return {
            "status": "disabled",
            "reason": "regos_auth_error",
            "task_uuid": task_uuid,
            "schedule_uuid": schedule_uuid,
            "connected_integration_id": self._ci(),
            "failures": failures,
        }

    @staticmethod
    def _is_regos_auth_error(error: Exception) -> bool:
        if not isinstance(error, httpx.HTTPStatusError):
            return False
        response = error.response
        if response is None or response.status_code not in {401, 403}:
            return False
        url = str(response.request.url) if response.request is not None else ""
        return "/gateway/out/" in url

    async def _ensure_scheduled(self) -> None:
        state = await self._load_integration_state(require_scheduled=True)
        if not bool(state.get("scheduled")):
            raise MarketplaceToServerError(111350, "not scheduled")

    async def _ensure_active(self) -> str:
        state = await self._load_integration_state()
        return str(state.get("key") or self.integration_key)

    async def _load_integration_state(self, *, require_scheduled: bool = False) -> Dict[str, Any]:
        ci = self._ci()
        if not ci:
            raise MarketplaceToServerError(100, "connected_integration_id is required")

        cached = await redis_get_json(self._active_cache_key())
        if isinstance(cached, dict):
            if not bool(cached.get("active")):
                raise MarketplaceToServerError(111350, "inactive")
            if not require_scheduled:
                return {
                    "active": True,
                    "key": str(cached.get("key") or self.integration_key),
                }

        async with RegosAPI(ci) as api:
            response = await api.integrations.connected_integration.get(
                ConnectedIntegrationGetRequest(
                    connected_integration_ids=[ci],
                    include_schedule=require_scheduled,
                    include_name=False,
                )
            )
        rows = response.result if response.ok and isinstance(response.result, list) else []
        row = rows[0] if rows else None
        if row is None:
            raise MarketplaceToServerError(111350, "not found")

        state = {
            "active": bool(getattr(row, "is_active", False)),
            "key": str(getattr(row, "key", "") or "").strip() or self.integration_key,
        }
        scheduled = getattr(row, "scheduled", None)
        if require_scheduled or scheduled is not None:
            state["scheduled"] = bool(scheduled)
        if not state["active"]:
            await redis_set_json(
                self._active_cache_key(),
                {"active": False, "key": self.integration_key, "scheduled": False},
                settings.marketplace_cache_ttl,
            )
            raise MarketplaceToServerError(111350, "inactive")
        if state["key"] != self.integration_key:
            logger.warning("Unexpected integration key for toserver: ci=%s key=%s", ci, state["key"])
        await redis_set_json(self._active_cache_key(), state, settings.marketplace_cache_ttl)
        return state

    async def _load_settings(self) -> Dict[str, str]:
        if self._settings is not None:
            return self._settings
        cached = await redis_get_json(self._settings_cache_key())
        if isinstance(cached, dict):
            self._settings = _normalize_settings_map(cached)
            return self._settings

        lock_token = await redis_acquire_lock(
            self._settings_lock_key(),
            settings.marketplace_lock_ttl,
            wait_timeout_sec=settings.marketplace_lock_wait_timeout,
        )
        if not lock_token:
            raise MarketplaceToServerError(111350, "settings cache lock timeout")
        try:
            cached = await redis_get_json(self._settings_cache_key())
            if isinstance(cached, dict):
                self._settings = _normalize_settings_map(cached)
                return self._settings

            await self._ensure_active()
            async with RegosAPI(self._ci()) as api:
                response = await api.integrations.connected_integration_setting.get(
                    ConnectedIntegrationSettingRequest(connected_integration_id=self._ci())
                )
            if not response.ok or not isinstance(response.result, list):
                raise MarketplaceToServerError(111350, "settings not found")
            self._settings = _normalize_settings_map(
                {
                    getattr(row, "key", ""): getattr(row, "value", "")
                    for row in response.result
                    if getattr(row, "key", None)
                }
            )
            await redis_set_json(self._settings_cache_key(), self._settings, settings.marketplace_cache_ttl)
            return self._settings
        finally:
            await redis_release_lock(self._settings_lock_key(), lock_token)

    async def _get_stocks(self, *, firm_id: int, stock_ids: List[int]) -> List[Dict[str, Any]]:
        async with RegosAPI(self._ci()) as api:
            response = await api.references.stock.get(
                StockGetRequest(
                    firm_ids=[firm_id] if firm_id > 0 else None,
                    ids=stock_ids or None,
                    offset=0,
                    limit=250,
                )
            )
        if not response.ok:
            raise MarketplaceToServerError(111321, "REGOS stocks request rejected")
        return [
            row.model_dump(mode="json", by_alias=True)
            for row in (response.result or [])
        ]

    async def _item_ext_page(
        self,
        *,
        price_type_id: int,
        image_size: Optional[ItemGetExtImageSize],
        offset: int,
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        async with RegosAPI(self._ci()) as api:
            response = await api.references.item.get_ext(
                ItemGetExtRequest(
                    price_type_id=price_type_id if price_type_id > 0 else None,
                    offset=offset,
                    limit=settings.marketplace_unload_page_size,
                    deleted_mark=False,
                    image_size=image_size,
                    zero_price=False,
                )
            )
        if not response.ok:
            raise MarketplaceToServerError(111321, "REGOS item ext request rejected")
        return (
            [
                row.model_dump(mode="json", by_alias=True)
                for row in (response.result or [])
            ],
            _to_int(response.next_offset),
            _to_int(response.total),
        )

    async def _current_quantities(self, *, item_ids: List[int], stock_ids: List[int]) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        async with RegosAPI(self._ci()) as api:
            for start in range(0, len(item_ids), 250):
                chunk_ids = item_ids[start : start + 250]
                if not chunk_ids:
                    continue
                response = await api.references.item.get_current_quantity(
                    ItemGetCurrentQuantityRequest(item_ids=chunk_ids, stock_ids=stock_ids)
                )
                if not response.ok:
                    raise MarketplaceToServerError(111321, "REGOS item quantity request rejected")
                result.extend(
                    row.model_dump(mode="json", by_alias=True)
                    for row in (response.result or [])
                )
        return result

    async def _preflight(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        settings_map: Dict[str, str],
    ) -> None:
        response = await client.post(endpoint, json=[], auth=self._basic_auth(settings_map))
        if response.status_code == 400:
            return
        response.raise_for_status()

    @staticmethod
    def _basic_auth(settings_map: Dict[str, str]) -> Optional[Tuple[str, str]]:
        if _to_int(settings_map.get("authorization_required")) != 1:
            return None
        return _text(settings_map.get("user_login")), _text(settings_map.get("user_password"))

    @staticmethod
    def _image_size(value: Any) -> Optional[ItemGetExtImageSize]:
        text = str(value or "").strip().lower()
        if text in {"1", "large"}:
            return ItemGetExtImageSize.Large
        if text in {"2", "medium"}:
            return ItemGetExtImageSize.Medium
        if text in {"3", "small"}:
            return ItemGetExtImageSize.Small
        return None

    @staticmethod
    def _parse_ids(raw: Any) -> List[int]:
        result = []
        for part in str(raw or "").split(","):
            value = _to_int(part)
            if value > 0:
                result.append(value)
        return sorted(set(result))

    @staticmethod
    def _build_payload(
        item_ext_rows: List[Dict[str, Any]],
        qty_rows: List[Dict[str, Any]],
        stocks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        stock_template = {
            _to_int(stock.get("id")): {"stock_id": _to_int(stock.get("id")), "value": Decimal("0")}
            for stock in stocks
            if _to_int(stock.get("id")) > 0
        }
        qty_by_item: Dict[int, Dict[int, Decimal]] = {}
        for row in qty_rows:
            item_id = _to_int(row.get("item_id"))
            stock_id = _to_int(row.get("stock_id"))
            if item_id <= 0 or stock_id <= 0:
                continue
            qty_by_item.setdefault(item_id, {})
            qty_by_item[item_id][stock_id] = qty_by_item[item_id].get(stock_id, Decimal("0")) + _to_decimal(row.get("quantity"))

        result = []
        for ext in item_ext_rows:
            item = ext.get("item") if isinstance(ext, dict) else None
            if not isinstance(item, dict):
                continue
            item_id = _to_int(item.get("id"))
            quantities = {stock_id: dict(row) for stock_id, row in stock_template.items()}
            for stock_id, quantity in qty_by_item.get(item_id, {}).items():
                if stock_id in quantities:
                    quantities[stock_id]["value"] = quantities[stock_id].get("value", Decimal("0")) + quantity

            result.append(
                {
                    "id": item_id,
                    "code": _to_int(item.get("code")),
                    "name": _text(item.get("name")),
                    "articul": _text(item.get("articul")),
                    "icps": _text(item.get("icps")),
                    "package_code": _text(item.get("package_code")),
                    "base_barcode": _text(item.get("base_barcode")),
                    "price": _to_decimal(ext.get("price")),
                    "image_url": _text(ext.get("image_url")),
                    "quantity": list(quantities.values()),
                }
            )
        return result
