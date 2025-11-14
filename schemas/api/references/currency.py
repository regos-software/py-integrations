from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator

from schemas.api.base import APIBaseResponse, BaseSchema
from schemas.api.common.sort_orders import SortOrders


class Currency(BaseSchema):
    """Рид-модель валюты."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., ge=1, description="ID валюты.")
    code_num: Optional[int] = PydField(
        default=None, description="Числовой код валюты (ISO 4217)."
    )
    code_chr: Optional[str] = PydField(
        default=None, description="Символьный код валюты (ISO 4217)."
    )
    name: Optional[str] = PydField(default=None, description="Наименование валюты.")
    exchange_rate: Decimal = PydField(
        ..., description="Текущий курс валюты по отношению к базовой."
    )
    is_base: bool = PydField(..., description="Флаг базовой валюты.")
    deleted: bool = PydField(..., description="Флаг удаления валюты.")
    last_update: int = PydField(
        ..., ge=0, description="Метка последнего обновления (unixtime, сек)."
    )

    @field_validator("code_chr", mode="before")
    @classmethod
    def _normalize_code_chr(cls, value: Optional[str]) -> Optional[str]:
        if isinstance(value, str):
            trimmed = value.strip().upper()
            return trimmed or None
        return value

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


class CurrencyGetRequest(BaseSchema):
    """Параметры выборки валют."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по списку идентификаторов валют."
    )
    code_chr_list: Optional[List[str]] = PydField(
        default=None, description="Фильтр по символьным кодам валют."
    )
    code_num_list: Optional[List[int]] = PydField(
        default=None, description="Фильтр по числовым кодам валют."
    )
    deleted: Optional[bool] = PydField(
        default=None, description="Фильтр по признаку удаления."
    )
    is_base: Optional[bool] = PydField(
        default=None, description="Только базовая / только небазовая валюта."
    )
    sort_orders: Optional[SortOrders] = PydField(
        default=None, description="Набор правил сортировки результата."
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

    @field_validator("code_chr_list", mode="before")
    @classmethod
    def _normalize_code_list(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return None
        normalized = []
        for item in value:
            if isinstance(item, str) and item.strip():
                normalized.append(item.strip().upper())
        return normalized or None


class CurrencyGetResponse(APIBaseResponse[List[Currency]]):
    """Ответ на запрос списка валют."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "Currency",
    "CurrencyGetRequest",
    "CurrencyGetResponse",
]
