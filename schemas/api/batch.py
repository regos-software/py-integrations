"""Схемы пакетного выполнения запросов (Batch)."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator

from schemas.api.base import APIBaseResponse, BaseSchema


class BatchStep(BaseSchema):
    """Описание одного шага batch-запроса."""

    model_config = ConfigDict(extra="forbid")

    key: str = PydField(..., description="Уникальный ключ шага в пределах запроса.")
    path: str = PydField(..., description="Путь метода, например 'Producer/Add'.")
    payload: Optional[Any] = PydField(
        default=None, description="Тело запроса, передаваемое в шаге."
    )

    @field_validator("key")
    @classmethod
    def _validate_key(cls, value: str) -> str:
        if not value or " " in value or "." in value:
            raise ValueError("key должен быть непустым и без пробелов/точек")
        return value

    @field_validator("path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        if "batch" in value.lower():
            raise ValueError("Нельзя вызывать batch изнутри batch")
        return value


class BatchRequest(BaseSchema):
    """Запрос на пакетное выполнение шагов."""

    model_config = ConfigDict(extra="forbid")

    stop_on_error: bool = PydField(
        default=False,
        description="Остановить выполнение на первом ошибочном шаге.",
    )
    requests: List[BatchStep] = PydField(
        ..., min_length=1, description="Список шагов batch-запроса."
    )


class BatchStepResponse(BaseSchema):
    """Ответ одного шага batch."""

    model_config = ConfigDict(extra="ignore")

    key: str = PydField(..., description="Ключ шага, совпадает с запросом.")
    status: int = PydField(..., ge=100, description="HTTP-статус, вернувшийся шагом.")
    response: APIBaseResponse = PydField(
        ..., description="Обёртка ответа шага, включая ok/result."
    )


class BatchResponse(BaseSchema):
    """Результат выполнения пакетного запроса."""

    model_config = ConfigDict(extra="ignore")

    ok: bool = PydField(..., description="Признак успеха всего batch-запроса.")
    result: List[BatchStepResponse] = PydField(
        ..., description="Ответы по каждому шагу batch-запроса."
    )


def ph(step_key: str, *path: str) -> str:
    """Вернуть плейсхолдер вида ${StepKey.result.some.path}."""

    tail = ".".join(path)
    return f"${{{step_key}.{tail}}}"


__all__ = [
    "BatchRequest",
    "BatchResponse",
    "BatchStep",
    "BatchStepResponse",
    "ph",
]
