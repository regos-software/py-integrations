"""Схемы справочника складов."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator

from schemas.api.base import APIBaseResponse, BaseSchema
from schemas.api.references.firm import Firm


class SortColumn(str, Enum):
    """Колонки сортировки списка складов."""

    ID = "Id"
    NAME = "Name"
    LAST_UPDATE = "LastUpdate"


class SortDirection(str, Enum):
    """Направление сортировки."""

    ASC = "asc"
    DESC = "desc"


class SortOrder(BaseSchema):
    """Правило сортировки складов."""

    model_config = ConfigDict(extra="forbid")

    column: SortColumn = PydField(..., description="Колонка сортировки.")
    direction: SortDirection = PydField(
        ..., description="Направление сортировки (asc|desc)."
    )


class Stock(BaseSchema):
    """Рид-модель склада."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., ge=1, description="ID склада.")
    name: Optional[str] = PydField(default=None, description="Наименование склада.")
    address: Optional[str] = PydField(default=None, description="Адрес склада.")
    firm: Firm = PydField(..., description="Предприятие, к которому относится склад.")
    area: Decimal = PydField(..., ge=0, description="Площадь склада.")
    description: Optional[str] = PydField(
        default=None, description="Дополнительное описание."
    )
    deleted_mark: bool = PydField(..., description="Метка удаления.")
    last_update: int = PydField(
        ..., ge=0, description="Метка последнего изменения (unixtime)."
    )

    @field_validator("name", "address", "description", mode="before")
    @classmethod
    def _strip_strings(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


class StockGetRequest(BaseSchema):
    """Фильтры получения складов."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(
        default=None, description="Список ID складов для выборки."
    )
    firm_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по ID предприятий."
    )
    sort_orders: Optional[List[SortOrder]] = PydField(
        default=None, description="Набор правил сортировки."
    )
    search: Optional[str] = PydField(
        default=None, description="Поиск по названию склада."
    )
    deleted_mark: Optional[bool] = PydField(
        default=None, description="Фильтр по метке удаления."
    )
    limit: Optional[int] = PydField(
        default=None,
        ge=1,
        le=10000,
        description="Лимит возвращаемых записей (максимум 10000).",
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


class StockGetResponse(APIBaseResponse[List[Stock]]):
    """Ответ на запрос списка складов."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "SortColumn",
    "SortDirection",
    "SortOrder",
    "Stock",
    "StockGetRequest",
    "StockGetResponse",
]
