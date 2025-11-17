"""Схемы операций розничных чеков."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import BaseSchema
from schemas.api.references.item import Item


class DocChequeOperation(BaseSchema):
    """Рид-модель операции в розничном чеке."""

    model_config = ConfigDict(extra="ignore")

    uuid: str = PydField(..., description="UUID операции.")
    has_storno: bool = PydField(
        ..., description="Признак, что операция является сторно."
    )
    storno_uuid: Optional[str] = PydField(
        default=None, description="UUID сторнирующей операции."
    )
    document: str = PydField(..., description="UUID документа продажи.")
    stock_id: int = PydField(..., ge=1, description="ID склада.")
    item: Optional[Item] = PydField(default=None, description="Позиция номенклатуры.")
    order: int = PydField(..., ge=0, description="Порядковый номер в документе.")
    quantity: Decimal = PydField(..., description="Количество товара.")
    price: Decimal = PydField(..., description="Цена продажи (с учётом скидок).")
    price2: Decimal = PydField(..., description="Цена без скидки")
    promo_id: Optional[int] = PydField(
        default=None, description="ID применённой акции."
    )
    vat_value: Decimal = PydField(..., description="Значение НДС.")
    last_update: int = PydField(
        ..., ge=0, description="Метка последнего изменения (Unix)."
    )


class DocChequeOperationGetRequest(BaseSchema):
    """Фильтры получения операций чеков."""

    model_config = ConfigDict(extra="forbid")

    doc_sale_uuid: Optional[str] = PydField(
        default=None, description="UUID документа продажи."
    )
    uuids: Optional[List[str]] = PydField(
        default=None, description="Список UUID операций."
    )
    item_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по ID номенклатуры."
    )
    stock_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по ID складов."
    )
    firm_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по ID фирм."
    )
    operating_cash_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по ID касс."
    )


__all__ = [
    "DocChequeOperation",
    "DocChequeOperationGetRequest",
]
