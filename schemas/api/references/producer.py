"""Схемы справочника производитель."""

from __future__ import annotations

from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator

from schemas.api.base import BaseSchema
from schemas.api.common.sort_orders import SortOrders


class Producer(BaseSchema):
    """Рид-модель производительа."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., description="ID производительа.")
    name: Optional[str] = PydField(
        default=None, description="Наименование производительа."
    )
    last_update: int = PydField(
        ..., ge=0, description="Метка последнего обновления (unixtime)."
    )


class ProducerGetRequest(BaseSchema):
    """Параметры выборки производительов."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по списку идентификаторов производительов."
    )
    sort_orders: Optional[SortOrders] = PydField(
        default=None, description="Правила сортировки результата."
    )
    search: Optional[str] = PydField(
        default=None, description="Поиск по названию производительа."
    )
    limit: Optional[int] = PydField(
        default=None,
        ge=1,
        description="Количество записей в выборке (пагинация).",
    )
    offset: Optional[int] = PydField(
        default=None,
        ge=0,
        description="Смещение для пагинации.",
    )

    @field_validator("search", mode="before")
    @classmethod
    def _strip_search(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


class ProducerAddRequest(BaseSchema):
    """Создание нового производительа."""

    model_config = ConfigDict(extra="forbid")

    name: str = PydField(..., min_length=1, description="Наименование производительа.")

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        return value.strip()


class ProducerEditRequest(BaseSchema):
    """Обновление существующего производительа."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="ID производительа.")
    name: str = PydField(
        ..., min_length=1, description="Новое название производительа."
    )

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        return value.strip()


class ProducerDeleteRequest(BaseSchema):
    """Удаление производительа."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="ID производительа.")


__all__ = [
    "Producer",
    "ProducerAddRequest",
    "ProducerDeleteRequest",
    "ProducerEditRequest",
    "ProducerGetRequest",
]
