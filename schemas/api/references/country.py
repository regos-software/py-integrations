"""Схемы справочника стран."""

from __future__ import annotations

from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator

from schemas.api.base import BaseSchema
from schemas.api.common.sort_orders import SortOrders


class Country(BaseSchema):
    """Рид-модель страна."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., description="ID страна.")
    name: Optional[str] = PydField(default=None, description="Наименование страна.")
    last_update: int = PydField(
        ..., ge=0, description="Метка последнего обновления (unixtime)."
    )


class CountryGetRequest(BaseSchema):
    """Параметры выборки странов."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по списку идентификаторов странов."
    )
    sort_orders: Optional[SortOrders] = PydField(
        default=None, description="Правила сортировки результата."
    )
    search: Optional[str] = PydField(
        default=None, description="Поиск по названию страна."
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


class CountryAddRequest(BaseSchema):
    """Создание нового страна."""

    model_config = ConfigDict(extra="forbid")

    name: str = PydField(..., min_length=1, description="Наименование страна.")

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        return value.strip()


class CountryEditRequest(BaseSchema):
    """Обновление существующего страна."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="ID страна.")
    name: str = PydField(..., min_length=1, description="Новое название страна.")

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        return value.strip()


class CountryDeleteRequest(BaseSchema):
    """Удаление страна."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="ID страна.")


__all__ = [
    "Country",
    "CountryAddRequest",
    "CountryDeleteRequest",
    "CountryEditRequest",
    "CountryGetRequest",
]
