from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import BaseSchema
from schemas.api.common.sort_orders import SortOrders


class RetailCardGroup(BaseSchema):
    """Группа карт покупателей."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, ge=1, description="ID группы карт.")
    name: Optional[str] = PydField(
        default=None, description="Наименование группы карт."
    )


class RetailCustomer(BaseSchema):
    """Покупатель (сокращенная модель)."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, ge=1, description="ID покупателя.")
    full_name: Optional[str] = PydField(
        default=None, description="ФИО покупателя."
    )


class BarcodeType(BaseSchema):
    """Тип штрих-кода."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, ge=1, description="ID типа штрих-кода.")
    name: Optional[str] = PydField(
        default=None, description="Наименование типа штрих-кода."
    )


class PromoProgram(BaseSchema):
    """Промоакция."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, ge=1, description="ID промоакции.")
    name: Optional[str] = PydField(
        default=None, description="Наименование промоакции."
    )


class RetailCard(BaseSchema):
    """Карта покупателя."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., ge=1, description="ID карты покупателя.")
    group: Optional[RetailCardGroup] = PydField(
        default=None, description="Группа карт покупателей."
    )
    customer: Optional[RetailCustomer] = PydField(
        default=None, description="Покупатель."
    )
    barcode_value: str = PydField(..., description="Штрих-код карты.")
    barcode_type: Optional[BarcodeType] = PydField(
        default=None, description="Тип штрих-кода."
    )
    promo: Optional[PromoProgram] = PydField(
        default=None, description="Промоакция."
    )
    bonus_amount: Decimal = PydField(
        ..., description="Сумма бонусов."
    )
    date: int = PydField(..., ge=0, description="Дата создания (unix time, сек).")
    unlimited: bool = PydField(..., description="Срок действия неограничен.")
    expiry_date: Optional[str] = PydField(
        default=None, description="Дата истечения срока действия."
    )
    last_purchase: Optional[int] = PydField(
        default=None, description="Дата последней покупки (unix time, сек)."
    )
    enabled: bool = PydField(..., description="Карта активна.")
    last_update: int = PydField(
        ..., ge=0, description="Дата последнего изменения (unix time, сек)."
    )


class RetailCardGetRequest(BaseSchema):
    """Запрос на получение карт покупателей."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(default=None, description="ID карт.")
    group_ids: Optional[List[int]] = PydField(
        default=None, description="ID групп карт."
    )
    customer_ids: Optional[List[int]] = PydField(
        default=None, description="ID покупателей."
    )
    promo_ids: Optional[List[int]] = PydField(
        default=None, description="ID промоакций."
    )
    barcode_value: Optional[str] = PydField(
        default=None, description="Штрих-код карты."
    )
    sort_orders: Optional[SortOrders] = PydField(
        default=None, description="Сортировка выходных данных."
    )
    search: Optional[str] = PydField(
        default=None, description="Строка поиска."
    )
    limit: Optional[int] = PydField(default=None, ge=1, description="Лимит.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Смещение.")


__all__ = [
    "BarcodeType",
    "PromoProgram",
    "RetailCard",
    "RetailCardGetRequest",
    "RetailCardGroup",
    "RetailCustomer",
]
