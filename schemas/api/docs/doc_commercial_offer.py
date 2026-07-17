"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocCommercialOffer(RegosModel):
    "Модель, описывающая документ коммерческого предложения"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id документа коммерческого предложения")
    date: int | None = PydField(default=None, description="Дата документа коммерческого предложения в формате unix time в секундах")
    code: str | None = PydField(default=None, description="Код документа коммерческого предложения")
    partner: Partner | None = PydField(default=None, description="Контрагент")
    currency: Currency | None = PydField(default=None, description="Валюта документа коммерческого предложения")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    amount: _Decimal | None = PydField(default=None, description="Сумма документа коммерческого предложения")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    attached_user: User | None = PydField(default=None, description="Ответственный пользователь")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocCommercialOfferAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: int | None = PydField(default=None, description="Дата документа коммерческого предложения в формате unixtime в секундах")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    currency_id: int | None = PydField(default=None, description="ID валюты документа коммерческого предложения")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")


class DocCommercialOfferColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocCommercialOfferColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocCommercialOfferColumns(str, Enum):
    Default = "Default"
    Code = "Code"
    Date = "Date"
    ContractName = "ContractName"
    PartnerName = "PartnerName"
    OrderStatusName = "OrderStatusName"
    Amount = "Amount"
    CurrencyName = "CurrencyName"


class DocCommercialOfferDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id документа коммерческого предложения")


class DocCommercialOfferDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа")


class DocCommercialOfferEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа коммерческого предложения")
    date: int | None = PydField(default=None, description="Дата документа коммерческого предложения в формате unix time в секундах")
    partner_id: int | None = PydField(default=None, description="Id контрагента")
    currency_id: int | None = PydField(default=None, description="Id валюты документа коммерческого предложения")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    attached_user_id: int | None = PydField(default=None, description="Id ответственного пользователя")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")


class DocCommercialOfferGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате Unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате Unix time в секундах")
    ids: list[int] | None = PydField(default=None, description="Массив ID документов коммерческого предложения")
    partner_ids: list[int] | None = PydField(default=None, description="Массив ID контрагентов")
    currency_ids: list[int] | None = PydField(default=None, description="Массив ID валют")
    attached_user_ids: list[int] | None = PydField(default=None, description="Массив ID ответственных пользователей")
    sort_orders: list[DocCommercialOfferColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    search: str | None = PydField(default=None, description="Строка поиска по полям: code - Код документа, partner_name - ФИО контрагента, partner_inn - ИНН контрагента, attached_user_name - ФИО ответственного пользователя")
    blocked: bool | None = PydField(default=None, description="Состояние блокировки документа для редактирования: true - Заблокирован, false - Разблокировин")
    deleted_mark: bool | None = PydField(default=None, description="Состояние пометки на удаление: true - Помечен на удаление, false - Не помечен на удаление")
    limit: int | None = PydField(default=None, description="Количество возвращаемых элементов выборки")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocCommercialOfferLockAndUnlock(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив Id документов коммерческого предложения")


class DocCommercialOfferRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocCommercialOffer] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult, VatCalculationTypeEnum
from schemas.api.rbac.user import User
from schemas.api.references.currency import Currency
from schemas.api.references.partner import Partner


DocCommercialOfferAddRequest: TypeAlias = DocCommercialOfferAdd
DocCommercialOfferAddResponse: TypeAlias = InsertResult
DocCommercialOfferDeleteMarkRequest: TypeAlias = DocCommercialOfferDeleteMark
DocCommercialOfferDeleteMarkResponse: TypeAlias = UpdateResult
DocCommercialOfferDeleteRequest: TypeAlias = DocCommercialOfferDelete
DocCommercialOfferDeleteResponse: TypeAlias = UpdateResult
DocCommercialOfferEditRequest: TypeAlias = DocCommercialOfferEdit
DocCommercialOfferEditResponse: TypeAlias = UpdateResult
DocCommercialOfferGetRequest: TypeAlias = DocCommercialOfferGet
DocCommercialOfferGetResponse: TypeAlias = DocCommercialOfferRegosOffsettedArrayResult
DocCommercialOfferLockRequest: TypeAlias = DocCommercialOfferLockAndUnlock
DocCommercialOfferLockResponse: TypeAlias = UpdateResult
DocCommercialOfferUnlockRequest: TypeAlias = DocCommercialOfferLockAndUnlock
DocCommercialOfferUnlockResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocCommercialOffer', 'DocCommercialOfferAdd', 'DocCommercialOfferColumn', 'DocCommercialOfferDelete', 'DocCommercialOfferDeleteMark', 'DocCommercialOfferEdit', 'DocCommercialOfferGet', 'DocCommercialOfferLockAndUnlock', 'DocCommercialOfferRegosOffsettedArrayResult']


__all__ = [
    'DocCommercialOffer',
    'DocCommercialOfferAdd',
    'DocCommercialOfferColumn',
    'DocCommercialOfferColumns',
    'DocCommercialOfferDelete',
    'DocCommercialOfferDeleteMark',
    'DocCommercialOfferEdit',
    'DocCommercialOfferGet',
    'DocCommercialOfferLockAndUnlock',
    'DocCommercialOfferRegosOffsettedArrayResult',
    'DocCommercialOfferGetRequest',
    'DocCommercialOfferGetResponse',
    'DocCommercialOfferAddRequest',
    'DocCommercialOfferAddResponse',
    'DocCommercialOfferEditRequest',
    'DocCommercialOfferEditResponse',
    'DocCommercialOfferDeleteMarkRequest',
    'DocCommercialOfferDeleteMarkResponse',
    'DocCommercialOfferDeleteRequest',
    'DocCommercialOfferDeleteResponse',
    'DocCommercialOfferLockRequest',
    'DocCommercialOfferLockResponse',
    'DocCommercialOfferUnlockRequest',
    'DocCommercialOfferUnlockResponse'
]
