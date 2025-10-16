"""Схемы кассовых операций."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import BaseSchema
from schemas.api.docs.cash_operation_type import CashOperationType


class CashOperation(BaseSchema):
    """Рид-модель кассовой операции."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, ge=1, description="ID операции.")
    date: Optional[int] = PydField(
        default=None, ge=0, description="Дата операции (Unix time, сек)."
    )
    type: Optional[CashOperationType] = PydField(
        default=None, description="Тип кассовой операции."
    )
    payment_type_id: Optional[int] = PydField(
        default=None, ge=1, description="ID формы оплаты."
    )
    payment_type_name: Optional[str] = PydField(
        default=None, description="Наименование формы оплаты."
    )
    session_uuid: Optional[str] = PydField(
        default=None, description="UUID кассовой смены."
    )
    document_uuid: Optional[str] = PydField(
        default=None, description="UUID связанного документа."
    )
    operating_cash_id: Optional[int] = PydField(
        default=None, ge=1, description="ID кассы."
    )
    value: Optional[Decimal] = PydField(default=None, description="Сумма операции.")
    description: Optional[str] = PydField(
        default=None, description="Комментарий к операции."
    )
    user_id: Optional[int] = PydField(
        default=None, ge=1, description="ID пользователя, выполнившего операцию."
    )
    user_full_name: Optional[str] = PydField(
        default=None, description="ФИО пользователя."
    )
    last_update: Optional[int] = PydField(
        default=None, ge=0, description="Время обновления записи (Unix time, сек)."
    )


class CashOperationGetRequest(BaseSchema):
    """Фильтры получения кассовых операций."""

    model_config = ConfigDict(extra="forbid")

    start_date: int = PydField(..., ge=0, description="Дата начала периода (Unix).")
    end_date: int = PydField(..., ge=0, description="Дата окончания периода (Unix).")
    operating_cash_id: Optional[int] = PydField(
        default=None, ge=1, description="ID кассы."
    )
    limit: Optional[int] = PydField(
        default=None, ge=1, description="Количество записей в выдаче."
    )
    offset: Optional[int] = PydField(
        default=None, ge=0, description="Смещение для пагинации."
    )


__all__ = [
    "CashOperation",
    "CashOperationGetRequest",
]
