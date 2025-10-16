"""Схемы справочника брендов."""

from __future__ import annotations

from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator

from schemas.api.base import BaseSchema
from schemas.api.common.sort_orders import SortOrders


class Brand(BaseSchema):
    """Рид-модель бренда."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., description="ID бренда.")
    name: Optional[str] = PydField(default=None, description="Наименование бренда.")
    last_update: int = PydField(
        ..., ge=0, description="Метка последнего обновления (unixtime)."
    )


class BrandGetRequest(BaseSchema):
    """Параметры выборки брендов."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по списку идентификаторов брендов."
    )
    sort_orders: Optional[SortOrders] = PydField(
        default=None, description="Правила сортировки результата."
    )
    search: Optional[str] = PydField(
        default=None, description="Поиск по названию бренда."
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


class BrandAddRequest(BaseSchema):
    """Создание нового бренда."""

    model_config = ConfigDict(extra="forbid")

    name: str = PydField(..., min_length=1, description="Наименование бренда.")

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        return value.strip()


class BrandEditRequest(BaseSchema):
    """Обновление существующего бренда."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="ID бренда.")
    name: str = PydField(..., min_length=1, description="Новое название бренда.")

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        return value.strip()


class BrandDeleteRequest(BaseSchema):
    """Удаление бренда."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="ID бренда.")


__all__ = [
    "Brand",
    "BrandAddRequest",
    "BrandDeleteRequest",
    "BrandEditRequest",
    "BrandGetRequest",
]
