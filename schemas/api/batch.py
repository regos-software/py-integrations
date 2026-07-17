"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel, field_validator

from schemas.api.common.base import RegosModel


class BatchRequest(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    stop_on_error: bool | None = PydField(default=None, description="Если true, пакет прерывается на первом неуспешном шаге")
    requests: list[BatchStep] | None = PydField(default=None, description="Список шагов пакета. Максимум 50 элементов")


class BatchStep(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    Key: str | None = PydField(default=None, description="Уникальный ключ шага")
    path: str | None = PydField(default=None, description="Имя метода в формате Controller/Method")
    payload: Any = PydField(default=None, description="Параметры запроса (object или array)")


class BatchStepResponse(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    key: str | None = PydField(default=None)
    status: int | None = PydField(default=None)
    response: Any = PydField(default=None)


class BatchResponse(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    responses: list[BatchStepResponse] | None = PydField(default=None)


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error


class BatchResponseRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: BatchResponse | Error | None = PydField(
        default=None,
        description="Batch result.",
    )

    @field_validator("result", mode="before")
    @classmethod
    def _normalize_result(cls, value: Any) -> Any:
        if isinstance(value, list):
            return {"responses": value}
        return value


BatchBatchRequest: TypeAlias = BatchRequest
BatchBatchResponse: TypeAlias = BatchResponseRegosObjectResult


_MODEL_NAMES = ['BatchRequest', 'BatchResponse', 'BatchResponseRegosObjectResult', 'BatchStep', 'BatchStepResponse']


__all__ = [
    'BatchRequest',
    'BatchResponse',
    'BatchResponseRegosObjectResult',
    'BatchStep',
    'BatchStepResponse',
    'BatchBatchRequest',
    'BatchBatchResponse'
]
