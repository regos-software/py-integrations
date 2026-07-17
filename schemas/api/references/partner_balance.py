"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class PartnerBalance(RegosModel):
    "Модель, описывающая акты сверок взаиморасчетов с контрагентами"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    currency: Currency | None = PydField(default=None, description="Валюта")
    currency_amount: _Decimal | None = PydField(default=None, description="Сальдо в валюте на дату акта сверки")
    id: int | None = PydField(default=None)
    date: int | None = PydField(default=None)
    document_code: str | None = PydField(default=None)
    document_id: int | None = PydField(default=None)
    start_amount: _Decimal | None = PydField(default=None)
    debit: _Decimal | None = PydField(default=None)
    credit: _Decimal | None = PydField(default=None)
    firm: Firm | None = PydField(default=None, description="Модель, описывающая предприятия")
    document_type: DocumentType | None = PydField(default=None, description="Модель, описывающая типы документов в системе")


class PartnerBalanceBase(RegosModel):
    "Модель данных акта сверки взаиморасчётов с контрагентом в базовой валюте"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None)
    date: int | None = PydField(default=None)
    document_code: str | None = PydField(default=None)
    document_id: int | None = PydField(default=None)
    start_amount: _Decimal | None = PydField(default=None)
    debit: _Decimal | None = PydField(default=None)
    credit: _Decimal | None = PydField(default=None)
    firm: Firm | None = PydField(default=None, description="Модель, описывающая предприятия")
    document_type: DocumentType | None = PydField(default=None, description="Модель, описывающая типы документов в системе")


class PartnerBalanceBaseGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unixtime в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unixtime в секундах")
    partner_id: int | None = PydField(default=None, description="Id контрагента")
    firm_id: int | None = PydField(default=None, description="Id предприятия")


class PartnerBalanceBaseRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[PartnerBalanceBase] | Error | None = PydField(default=None, description="Массив результата.")


class PartnerBalanceGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    currency_id: int | None = PydField(default=None, description="ID валюты")
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unixtime в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unixtime в секундах")
    partner_id: int | None = PydField(default=None, description="Id контрагента")
    firm_id: int | None = PydField(default=None, description="Id предприятия")


class PartnerBalanceRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[PartnerBalance] | Error | None = PydField(default=None, description="Массив результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error
from schemas.api.docs.document_type import DocumentType
from schemas.api.references.currency import Currency
from schemas.api.references.firm import Firm


PartnerBalanceGetInBaseCurrencyRequest: TypeAlias = PartnerBalanceBaseGet
PartnerBalanceGetInBaseCurrencyResponse: TypeAlias = PartnerBalanceBaseRegosArrayResult
PartnerBalanceGetRequest: TypeAlias = PartnerBalanceGet
PartnerBalanceGetResponse: TypeAlias = PartnerBalanceRegosArrayResult


_MODEL_NAMES = ['PartnerBalance', 'PartnerBalanceBase', 'PartnerBalanceBaseGet', 'PartnerBalanceBaseRegosArrayResult', 'PartnerBalanceGet', 'PartnerBalanceRegosArrayResult']


__all__ = [
    'PartnerBalance',
    'PartnerBalanceBase',
    'PartnerBalanceBaseGet',
    'PartnerBalanceBaseRegosArrayResult',
    'PartnerBalanceGet',
    'PartnerBalanceRegosArrayResult',
    'PartnerBalanceGetRequest',
    'PartnerBalanceGetResponse',
    'PartnerBalanceGetInBaseCurrencyRequest',
    'PartnerBalanceGetInBaseCurrencyResponse'
]
