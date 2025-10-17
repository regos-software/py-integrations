"""Схемы справочника цветов."""

from __future__ import annotations

from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator

from schemas.api.base import BaseSchema
from schemas.api.common.sort_orders import SortOrders


class Color(BaseSchema):
    """Рид-модель цвета."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., description="ID цвета.")
    name: Optional[str] = PydField(default=None, description="Наименование цвета.")
    last_update: int = PydField(
        ..., ge=0, description="Метка последнего обновления (unixtime)."
    )


class ColorGetRequest(BaseSchema):
    """Параметры выборки цветов."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по списку идентификаторов цветов."
    )
    sort_orders: Optional[SortOrders] = PydField(
        default=None, description="Правила сортировки результата."
    )
    search: Optional[str] = PydField(
        default=None, description="Поиск по названию цвета."
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


class ColorAddRequest(BaseSchema):
    """Создание нового цвета."""

    model_config = ConfigDict(extra="forbid")

    name: str = PydField(..., min_length=1, description="Наименование цвета.")

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        return value.strip()


class ColorEditRequest(BaseSchema):
    """Обновление существующего цвета."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="ID цвета.")
    name: str = PydField(..., min_length=1, description="Новое название цвета.")

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        return value.strip()


class ColorDeleteRequest(BaseSchema):
    """Удаление цвета."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="ID цвета.")


__all__ = [
    "Color",
    "ColorAddRequest",
    "ColorDeleteRequest",
    "ColorEditRequest",
    "ColorGetRequest",
]
