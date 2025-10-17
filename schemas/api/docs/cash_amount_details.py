"""Схемы детализированного отчёта по денежным средствам."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import BaseSchema


class CashAmountDetails(BaseSchema):
    """Рид-модель деталей по кассовым средствам."""

    model_config = ConfigDict(extra="ignore")

    current_amount: Optional[Decimal] = PydField(
        default=None, description="Текущая сумма в кассе."
    )
    start_amount: Optional[Decimal] = PydField(
        default=None, description="Сумма на начало периода."
    )
    income: Optional[Decimal] = PydField(
        default=None, description="Поступления за период."
    )
    outcome: Optional[Decimal] = PydField(
        default=None, description="Списания за период."
    )
    end_amount: Optional[Decimal] = PydField(
        default=None, description="Сумма на конец периода."
    )


class CashAmountDetailsGetRequest(BaseSchema):
    """Фильтры получения детализации денежных средств."""

    model_config = ConfigDict(extra="forbid")

    start_date: int = PydField(..., ge=0, description="Дата начала периода (Unix).")
    end_date: int = PydField(..., ge=0, description="Дата окончания периода (Unix).")
    operating_cash_id: Optional[int] = PydField(
        default=None, ge=1, description="ID кассы."
    )


__all__ = [
    "CashAmountDetails",
    "CashAmountDetailsGetRequest",
]
