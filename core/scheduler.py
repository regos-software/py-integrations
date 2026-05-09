from __future__ import annotations

import asyncio
import json
from typing import Any, Optional, TypeVar

import httpx
from pydantic import BaseModel

from config.settings import settings
from schemas.scheduler import (
    Schedule,
    ScheduleAddRequest,
    ScheduleIdRequest,
    ScheduleTask,
    ScheduleTaskIdRequest,
    ScheduleTaskSetStatusRequest,
)


TModel = TypeVar("TModel", bound=BaseModel)


class SchedulerError(RuntimeError):
    def __init__(self, code: int, description: str) -> None:
        super().__init__(description)
        self.code = int(code)
        self.description = str(description)


class RegosSchedulerClient:
    def __init__(
        self,
        *,
        hostname: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[int] = None,
        verify_ssl: Optional[bool] = None,
        retries: int = 3,
    ) -> None:
        self.hostname = str(hostname if hostname is not None else settings.scheduler_hostname).strip()
        self.token = str(token if token is not None else settings.scheduler_token).strip()
        self.timeout = int(timeout if timeout is not None else settings.scheduler_timeout)
        self.verify_ssl = bool(settings.scheduler_verify_ssl if verify_ssl is None else verify_ssl)
        self.retries = max(1, int(retries))

    async def schedule_add(self, request: ScheduleAddRequest) -> Any:
        return await self._request("api/Schedule/Add", request)

    async def schedule_get_by_id(self, request: ScheduleIdRequest | str) -> Optional[Schedule]:
        req = request if isinstance(request, ScheduleIdRequest) else ScheduleIdRequest(id=request)
        result = await self._request("api/Schedule/GetById", req)
        return self._validate_optional(Schedule, result)

    async def schedule_delete(self, request: ScheduleIdRequest | str) -> Any:
        req = request if isinstance(request, ScheduleIdRequest) else ScheduleIdRequest(id=request)
        return await self._request("api/Schedule/Delete", req)

    async def task_get_info(self, request: ScheduleTaskIdRequest | str) -> Optional[ScheduleTask]:
        req = request if isinstance(request, ScheduleTaskIdRequest) else ScheduleTaskIdRequest(uuid=request)
        result = await self._request("api/Task/GetInfo", req)
        return self._validate_optional(ScheduleTask, result)

    async def task_set_status(self, request: ScheduleTaskSetStatusRequest) -> Any:
        return await self._request("api/Task/SetStatus", request)

    async def _request(self, path: str, payload: BaseModel | dict[str, Any]) -> Any:
        self._ensure_configured()
        url = self._url(path)
        request_payload = self._serialize_payload(payload)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

        last_error: Optional[SchedulerError] = None
        async with httpx.AsyncClient(timeout=self.timeout, verify=self.verify_ssl) as client:
            for attempt in range(self.retries):
                try:
                    response = await client.post(url, json=request_payload, headers=headers)
                except httpx.RequestError as error:
                    last_error = SchedulerError(111320, str(error))
                else:
                    last_error = self._response_error(response)
                    if last_error is None:
                        return self._scheduler_result(response)

                if attempt < self.retries - 1:
                    await asyncio.sleep(attempt + 1)

        if last_error is not None:
            raise last_error
        raise SchedulerError(111320, "Scheduler request failed")

    def _ensure_configured(self) -> None:
        if not self.hostname:
            raise SchedulerError(111320, "SCHEDULER_HOSTNAME is not set")
        if not self.token:
            raise SchedulerError(111320, "SCHEDULER_TOKEN is not set")

    def _url(self, path: str) -> str:
        return f"{self.hostname.rstrip('/')}/{path.lstrip('/')}"

    @staticmethod
    def _serialize_payload(payload: BaseModel | dict[str, Any]) -> dict[str, Any]:
        if isinstance(payload, BaseModel):
            return payload.model_dump(mode="json", exclude_none=True)
        return payload

    @staticmethod
    def _response_error(response: httpx.Response) -> Optional[SchedulerError]:
        if response.status_code == 200:
            return None
        reason = response.reason_phrase or "Scheduler HTTP error"
        return SchedulerError(111321, f"{response.status_code} - {reason}")

    def _scheduler_result(self, response: httpx.Response) -> Any:
        if not response.content:
            raise SchedulerError(111322, "Response content empty")
        try:
            parsed = response.json()
        except json.JSONDecodeError as error:
            raise SchedulerError(111322, f"Invalid JSON response: {error}") from error
        if not isinstance(parsed, dict):
            raise SchedulerError(111322, "Invalid Scheduler response envelope")
        if parsed.get("ok") is True:
            return parsed.get("result")
        raise self._api_error(parsed.get("result"))

    @staticmethod
    def _api_error(result: Any) -> SchedulerError:
        if isinstance(result, dict):
            code = result.get("error") or 111321
            description = result.get("description") or str(result)
            try:
                code = int(code)
            except (TypeError, ValueError):
                code = 111321
            return SchedulerError(code, str(description))
        if isinstance(result, str) and result.strip():
            return SchedulerError(111321, result.strip())
        return SchedulerError(111321, "Scheduler API error")

    @staticmethod
    def _validate_optional(model: type[TModel], result: Any) -> Optional[TModel]:
        if result is None:
            return None
        if isinstance(result, model):
            return result
        if isinstance(result, dict):
            return model.model_validate(result)
        raise SchedulerError(111322, "Invalid Scheduler result")


__all__ = ["RegosSchedulerClient", "SchedulerError"]
