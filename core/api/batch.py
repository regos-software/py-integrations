# core/api/batch_service.py
from __future__ import annotations
from typing import Any, Optional, Type, TypeVar
from pydantic import TypeAdapter

from schemas.api.base import APIBaseResponse, APIErrorResult
from schemas.api.batch import BatchRequest, BatchResponse, BatchStep

T = TypeVar("T")


class RegosAPIError(Exception):
    def __init__(self, *, step_key: str, status: int, error: int, description: str):
        self.step_key = step_key
        self.status = status
        self.error = error
        self.description = description
        super().__init__(f"[{step_key}] status={status} error={error}: {description}")


class BatchService:
    """
    Обёртка над /v1/batch с удобными хелперами.
    Не хранит состояния, использует переданный APIClient.
    """

    def __init__(self, api_client):
        self._client = api_client

    async def run(
        self, steps: list[BatchStep], *, stop_on_error: bool = False
    ) -> BatchResponse:
        """
        Выполнить пакет запросов (POST …/v1/batch).
        ВАЖНО: передаём method_path="batch", т.к. APIClient сам добавляет префикс /v1/
        """
        if not steps:
            raise ValueError("Список шагов пуст")
        if len(steps) > 50:
            raise ValueError("Количество шагов в пакете не должно превышать 50")

        keys = [s.key for s in steps]
        if len(set(keys)) != len(keys):
            raise ValueError(f"Дубликаты ключей в steps: {keys}")

        req = BatchRequest(stop_on_error=stop_on_error, requests=steps)
        return await self._client.post(
            method_path="batch", data=req, response_model=BatchResponse
        )

    # ------- Хелперы разбора ответа -------
    @staticmethod
    def map(resp: BatchResponse) -> dict[str, APIBaseResponse]:
        return {s.key: s.response for s in resp.result}

    @staticmethod
    def response(resp: BatchResponse, key: str) -> APIBaseResponse:
        for s in resp.result:
            if s.key == key:
                return s.response
        raise KeyError(f"Шаг '{key}' не найден")

    @staticmethod
    def result(
        resp: BatchResponse, key: str, result_type: Optional[Type[T]] = None
    ) -> T | Any:
        """
        Достаёт .result из шага, валидирует ok, опционально приводит к модели.
        Если ok=False — бросает RegosAPIError.
        """
        step = next((s for s in resp.result if s.key == key), None)
        if not step:
            raise KeyError(f"Шаг '{key}' не найден")

        api_resp = step.response
        if not api_resp.ok:
            err = APIErrorResult.model_validate(api_resp.result)
            raise RegosAPIError(
                step_key=key,
                status=step.status,
                error=err.error,
                description=err.description,
            )

        data = api_resp.result
        if result_type is None:
            return data
        return TypeAdapter(result_type).validate_python(data)


# ------- Пример использования -------
# from schemas.api.batch import BatchStep, ph
# from core.api.regos_api import RegosAPI

# async with RegosAPI(connected_integration_id="...") as api:
#    steps = [
#        BatchStep(key="ProducerAdd", path="Producer/Add", payload={"name": "Coca-Cola"}),
#        BatchStep(key="ProducerGet", path="Producer/Get",
#                  payload={"ids": [ph("ProducerAdd", "result", "new_id")]}),
#    ]

#    resp = await api.batch.run(steps, stop_on_error=False)

#    # быстрые хелперы
#    from core.api.batch_service import BatchService

#    new_id = BatchService.result(resp, "ProducerAdd", result_type=dict)["new_id"]
#    producers = BatchService.result(resp, "ProducerGet", result_type=list[dict])
