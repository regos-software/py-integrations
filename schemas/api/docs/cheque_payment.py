"""Схемы документов розничных платежей."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import BaseSchema
from schemas.api.references.payment_type import PaymentType


class DocChequePayment(BaseSchema):
    """Рид-модель платежа розничного документа."""

    model_config = ConfigDict(extra="ignore")

    uuid: str = PydField(..., description="UUID платежа.")
    has_storno: bool = PydField(
        ..., description="Признак, что платеж является сторнированием."
    )
    storno_uuid: Optional[str] = PydField(
        default=None, description="UUID сторнируемого платежа."
    )
    document: str = PydField(..., description="UUID документа розничной продажи.")
    order: int = PydField(..., ge=0, description="Порядковый номер платежа.")
    type: PaymentType = PydField(..., description="Форма оплаты.")
    value: Decimal = PydField(..., description="Сумма платежа.")
    has_change: bool = PydField(..., description="Есть ли сдача по платежу.")
    change_uuid: Optional[str] = PydField(
        default=None, description="UUID платежа со сдачей."
    )


class DocChequePaymentGetRequest(BaseSchema):
    """Фильтры получения платежей розничных документов."""

    model_config = ConfigDict(extra="forbid")

    doc_sale_uuid: Optional[str] = PydField(
        default=None, description="UUID документа розничной продажи."
    )
    uuids: Optional[List[str]] = PydField(
        default=None, description="Список UUID платежей."
    )
    payment_type_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по ID форм оплаты."
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
    "DocChequePayment",
    "DocChequePaymentGetRequest",
]
