from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator

from schemas.api.base import APIBaseResponse, BaseSchema
from .currency import Currency


class PriceType(BaseSchema):
    """Модель вида цены."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., ge=1, description="ID вида цены.")
    name: Optional[str] = PydField(default=None, description="Наименование вида цены.")
    round_to: Optional[Decimal] = PydField(
        default=None, description="Предел округления."
    )
    markup: Optional[Decimal] = PydField(
        default=None, description="Наценка для вида цены."
    )
    max_discount: Optional[Decimal] = PydField(
        default=None, description="Максимальная скидка."
    )
    currency: Optional[Currency] = PydField(
        default=None, description="Основная валюта вида цены."
    )
    currency_additional: Optional[Currency] = PydField(
        default=None, description="Дополнительная валюта."
    )
    last_update: int = PydField(
        ..., ge=0, description="Метка последнего изменения (unixtime, сек)."
    )

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


class PriceTypeSortColumn(str, Enum):
    """Колонки сортировки списка видов цен."""

    ID = "Id"
    NAME = "Name"
    ROUND_TO = "RoundTo"
    MARK_UP = "MarkUp"
    MAX_DISCOUNT = "MaxDiscount"
    LAST_UPDATE = "LastUpdate"


class PriceTypeSortDirection(str, Enum):
    """Направление сортировки."""

    ASC = "ASC"
    DESC = "DESC"


class PriceTypeSortOrder(BaseSchema):
    """Правило сортировки для /PriceType/Get."""

    model_config = ConfigDict(extra="forbid")

    column: PriceTypeSortColumn = PydField(..., description="Колонка сортировки.")
    direction: PriceTypeSortDirection = PydField(
        PriceTypeSortDirection.ASC, description="Направление сортировки."
    )

    @field_validator("direction", mode="before")
    @classmethod
    def _normalize_direction(cls, value):
        if isinstance(value, str):
            upper = value.strip().upper()
            if upper in {"ASC", "DESC"}:
                return upper
        return value


class PriceTypeGetRequest(BaseSchema):
    """Параметры запроса /v1/PriceType/Get."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(
        default=None, description="Массив ID видов цен."
    )
    currency_ids: Optional[List[int]] = PydField(
        default=None, description="Массив ID валют."
    )
    sort_orders: Optional[List[PriceTypeSortOrder]] = PydField(
        default=None, description="Правила сортировки результата."
    )
    search: Optional[str] = PydField(
        default=None, description="Поиск по наименованию вида цены."
    )
    limit: Optional[int] = PydField(
        default=None,
        ge=1,
        description="Количество записей в выдаче (пагинация).",
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


class PriceTypeGetResponse(APIBaseResponse[List[PriceType]]):
    """Ответ на запрос /v1/PriceType/Get."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "PriceType",
    "PriceTypeSortColumn",
    "PriceTypeSortDirection",
    "PriceTypeSortOrder",
    "PriceTypeGetRequest",
    "PriceTypeGetResponse",
]
