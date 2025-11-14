"""Базовые схемы API по конвенциям проекта."""

from __future__ import annotations

from decimal import Decimal
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field as PydField


class BaseSchema(BaseModel):
    """Базовая модель со стандартными JSON-энкодерами."""

    model_config = ConfigDict(json_encoders={Decimal: float})


T = TypeVar("T")


class APIBaseResponse(BaseSchema, Generic[T]):
    """Универсальный ответ REST-эндпоинта REGOS."""

    model_config = ConfigDict(extra="ignore")

    ok: bool = PydField(..., description="Признак успешного ответа.")
    result: Optional[T] = PydField(
        default=None,
        description="Полезная нагрузка ответа (dict, list, scalar и др.).",
    )
    next_offset: Optional[int] = PydField(
        default=None,
        ge=0,
        description="Следующий offset для постраничной выборки.",
    )
    total: Optional[int] = PydField(
        default=None,
        ge=0,
        description="Общее количество записей в выборке.",
    )


class APIErrorResult(BaseSchema):
    """Структура ошибки, возвращаемой REST-эндпоинтом."""

    model_config = ConfigDict(extra="ignore")

    error: int = PydField(..., description="Код ошибки.")
    description: str = PydField(..., description="Описание ошибки.")


class ArrayResult(BaseSchema):
    """Ответ методов Add/Edit/Delete с массивом идентификаторов."""

    model_config = ConfigDict(extra="ignore")

    row_affected: int = PydField(
        ..., ge=0, description="Количество обработанных записей."
    )
    ids: Optional[list[int]] = PydField(
        default_factory=list, description="Идентификаторы затронутых сущностей."
    )


class AddResult(BaseSchema):
    """Ответ методов Add с идентификатором добавленной записи."""

    model_config = ConfigDict(extra="ignore")

    new_id: int = PydField(..., ge=1, description="Идентификатор добавленной записи.")


class IDRequest(BaseSchema):
    """Запрос на работу с одной записью по идентификатору."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="ID записи.")


__all__ = [
    "APIBaseResponse",
    "APIErrorResult",
    "ArrayResult",
    "BaseSchema",
    "IDRequest",
]
