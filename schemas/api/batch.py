# schemas/api/batch.py
from __future__ import annotations
from typing import Any, List, Optional
from pydantic import Field, field_validator
from .base import BaseSchema, APIBaseResponse

class BatchStep(BaseSchema):
    key: str = Field(..., description="Уникальный ключ шага")
    path: str = Field(..., description="Напр. 'Producer/Add'")
    payload: Optional[Any] = Field(default=None)

    @field_validator("key")
    @classmethod
    def _v_key(cls, v: str) -> str:
        if not v or " " in v or "." in v:
            raise ValueError("key должен быть непустым и без пробелов/точек")
        return v

    @field_validator("path")
    @classmethod
    def _v_path(cls, v: str) -> str:
        if "batch" in v.lower():
            raise ValueError("Нельзя вызывать batch изнутри batch")
        return v

class BatchRequest(BaseSchema):
    stop_on_error: bool = False
    requests: List[BatchStep]

class BatchStepResponse(BaseSchema):
    key: str
    status: int
    response: APIBaseResponse

class BatchResponse(BaseSchema):
    ok: bool
    # Сервер возвращает массив результатов шагов
    result: List[BatchStepResponse]

def ph(step_key: str, *path: str) -> str:
    """Плейсхолдер вида ${StepKey.result.some.path}"""
    tail = ".".join(path)
    return f"${{{step_key}.{tail}}}"
