"""Сервис пакетного выполнения запросов REGOS API."""

from __future__ import annotations

from typing import Any, Optional, Type, TypeVar

from pydantic import TypeAdapter

from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from schemas.api.base import APIBaseResponse, APIErrorResult
from schemas.api.batch import BatchRequest, BatchResponse


logger = setup_logger("api.BatchService")
T = TypeVar("T")


class RegosAPIError(RuntimeError):
    """Ошибка выполнения отдельного шага batch."""

    def __init__(self, *, step_key: str, status: int, error: int, description: str):
        super().__init__(f"[{step_key}] status={status} error={error}: {description}")
        self.step_key = step_key
        self.status = status
        self.error = error
        self.description = description


class BatchService:
    """Обёртка над /v1/batch с валидацией и вспомогательными методами."""

    PATH = "batch"

    def __init__(self, api: RegosAPI):
        self.api = api

    async def run(self, req: BatchRequest) -> BatchResponse:
        """Выполнить список шагов через POST …/v1/batch."""
        return await self.api.call(self.PATH, req, BatchResponse)

    @staticmethod
    def map(response: BatchResponse) -> dict[str, APIBaseResponse]:
        """Преобразовать результат batch в словарь {key: APIBaseResponse}."""

        return {step.key: step.response for step in response.result}

    @staticmethod
    def response(response: BatchResponse, key: str) -> APIBaseResponse:
        """Получить APIBaseResponse для указанного шага."""

        for step in response.result:
            if step.key == key:
                return step.response
        raise KeyError(f"Шаг '{key}' не найден в batch-ответе")

    @staticmethod
    def result(
        response: BatchResponse, key: str, result_type: Optional[Type[T]] = None
    ) -> T | Any:
        """Вернуть поле result шага и при необходимости провалидировать тип."""

        step = next((item for item in response.result if item.key == key), None)
        if step is None:
            raise KeyError(f"Шаг '{key}' не найден в batch-ответе")

        api_response = step.response
        if not api_response.ok:
            error_payload = APIErrorResult.model_validate(api_response.result)
            raise RegosAPIError(
                step_key=key,
                status=step.status,
                error=error_payload.error,
                description=error_payload.description,
            )

        payload = api_response.result
        if result_type is None:
            return payload

        return TypeAdapter(result_type).validate_python(payload)


__all__ = ["BatchService", "RegosAPIError"]
