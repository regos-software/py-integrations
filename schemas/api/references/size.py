"""Схемы справочника размеров."""

from __future__ import annotations

from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator

from schemas.api.base import BaseSchema
from schemas.api.common.sort_orders import SortOrders


class SizeChart(BaseSchema):
    """Рид-модель размера."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., description="ID размера.")
    name: Optional[str] = PydField(default=None, description="Наименование размера.")
    last_update: int = PydField(
        ..., ge=0, description="Метка последнего обновления (unixtime)."
    )


class SizeChartGetRequest(BaseSchema):
    """Параметры выборки размеров."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по списку идентификаторов размеров."
    )
    sort_orders: Optional[SortOrders] = PydField(
        default=None, description="Правила сортировки результата."
    )
    search: Optional[str] = PydField(
        default=None, description="Поиск по названию размера."
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


class SizeChartAddRequest(BaseSchema):
    """Создание нового размера."""

    model_config = ConfigDict(extra="forbid")

    name: str = PydField(..., min_length=1, description="Наименование размера.")

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        return value.strip()


class SizeChartEditRequest(BaseSchema):
    """Обновление существующего размера."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="ID размера.")
    name: str = PydField(..., min_length=1, description="Новое название размера.")

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        return value.strip()


class SizeChartDeleteRequest(BaseSchema):
    """Удаление размера."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="ID размера.")


__all__ = [
    "SizeChart",
    "SizeChartAddRequest",
    "SizeChartDeleteRequest",
    "SizeChartEditRequest",
    "SizeChartGetRequest",
]
