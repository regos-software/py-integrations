"""Схемы справочника цен номенклатуры."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import APIBaseResponse, BaseSchema
from schemas.api.references.price_type import PriceType


class ItemPrice(BaseSchema):
    """Модель цены номенклатуры."""

    model_config = ConfigDict(extra="ignore")

    item_id: int = PydField(..., ge=1, description="ID номенклатуры.")
    price_type: Optional[PriceType] = PydField(
        None, description="Тип цены, к которому относится значение."
    )
    value: Optional[Decimal] = PydField(
        None, description="Значение цены (в валюте вида цены)."
    )
    last_update: Optional[int] = PydField(
        None, ge=0, description="Метка последнего обновления (unixtime, сек)."
    )


class ItemPriceGetRequest(BaseSchema):
    """Параметры запроса /v1/ItemPrice/Get."""

    model_config = ConfigDict(extra="forbid")

    item_ids: Optional[List[int]] = PydField(
        None, description="Фильтр по массиву ID номенклатуры."
    )
    price_type_ids: Optional[List[int]] = PydField(
        None, description="Фильтр по массиву ID видов цен."
    )


class ItemPriceGetResponse(APIBaseResponse[List[ItemPrice]]):
    """Ответ на запрос /v1/ItemPrice/Get."""

    model_config = ConfigDict(extra="ignore")


class ItemPreCost(BaseSchema):
    """Модель себестоимости номенклатуры."""

    model_config = ConfigDict(extra="ignore")

    item_id: int = PydField(..., ge=1, description="ID номенклатуры.")
    value: Optional[Decimal] = PydField(
        None, description="Значение себестоимости (в базовой валюте)."
    )
    cost_date: int = PydField(
        ..., ge=1, description="Дата, на которую рассчитана себестоимость."
    )


class ItemPriceGetPreCostRequest(BaseSchema):
    """Параметры запроса /v1/ItemPrice/GetPreCost."""

    model_config = ConfigDict(extra="forbid")

    item_ids: List[int] = PydField(
        ..., min_length=1, description="Массив ID номенклатуры."
    )
    cost_date: int = PydField(
        ..., ge=0, description="Дата расчёта себестоимости (unixtime, сек)."
    )
    firm_id: Optional[int] = PydField(
        None, ge=1, description="ID предприятия (если требуется детализация)."
    )
    price_type_ids: Optional[List[int]] = PydField(
        None,
        description=("Дополнительный фильтр по видам цен (если поддерживается API)."),
    )


class ItemPriceGetPreCostResponse(APIBaseResponse[List[ItemPreCost]]):
    """Ответ на запрос /v1/ItemPrice/GetPreCost."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "ItemPrice",
    "ItemPriceGetRequest",
    "ItemPriceGetResponse",
    "ItemPreCost",
    "ItemPriceGetPreCostRequest",
    "ItemPriceGetPreCostResponse",
]
