"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocOpeningBalance(RegosModel):
    "Модель, описывающая документы начальных взаиморасчётов с контрагентом"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа")
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    code: str | None = PydField(default=None, description="Код документа")
    partner: Partner | None = PydField(default=None, description="Контрагент")
    firm: Firm | None = PydField(default=None, description="Предприятие")
    debit: _Decimal | None = PydField(default=None, description="Значение суммы дебета")
    credit: _Decimal | None = PydField(default=None, description="Значение суммы кредита")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты по отношению к основной")
    currency: Currency | None = PydField(default=None, description="Валюта")
    performed: bool | None = PydField(default=None, description="Метка о проведении документа")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unixtime в секундах")


class DocOpeningBalanceAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: int | None = PydField(default=None, description="Дата в формате unix time в секундах")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    firm_id: int | None = PydField(default=None, description="ID предприятия")
    debit: _Decimal | None = PydField(default=None, description="Значение суммы дебета")
    credit: _Decimal | None = PydField(default=None, description="Значение суммы кредита")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты по отношению к основной")
    currency_id: int | None = PydField(default=None, description="ID валюты")


class DocOpeningBalanceColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocOpeningBalanceColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocOpeningBalanceColumns(str, Enum):
    Default = "Default"
    Id = "Id"
    Date = "Date"
    Code = "Code"
    PartnerName = "PartnerName"
    FirmName = "FirmName"
    Debit = "Debit"
    Credit = "Credit"
    CurrencyName = "CurrencyName"
    Performed = "Performed"
    DeletedMark = "DeletedMark"
    LastUpdate = "LastUpdate"


class DocOpeningBalanceDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа начальных взаиморасчётов с контрагентом")


class DocOpeningBalanceDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа")


class DocOpeningBalanceEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа установки цен")
    date: int | None = PydField(default=None, description="Дата в формате unix time в секундах")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    firm_id: int | None = PydField(default=None, description="ID предприятия")
    debit: _Decimal | None = PydField(default=None, description="Значение суммы дебета")
    credit: _Decimal | None = PydField(default=None, description="Значение суммы кредита")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты по отношению к основной")
    currency_id: int | None = PydField(default=None, description="ID валюты")


class DocOpeningBalanceGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    ids: list[int] | None = PydField(default=None, description="Массив ID документов начальных взаиморасчётов с контрагентом")
    partner_ids: list[int] | None = PydField(default=None, description="Массив ID контрагентов")
    firm_ids: list[int] | None = PydField(default=None, description="Массив ID предприятий")
    sort_orders: list[DocOpeningBalanceColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Поиск про значениям параметров: code - Код документа, Firm/name - Наименование предприятия, Firm/inn - ИНН предприятия,\nPartner/name - Наименование контрагента, Partner/inn - ИНН контрагента")
    performed: bool | None = PydField(default=None, description="Состояние проведение документа: true - Проведён, false - Не проведён")
    deleted_mark: bool | None = PydField(default=None, description="Состояние пометки на удаление: true - Помечен на удаление, false - Не помечен на удаление")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocOpeningBalancePerformAndCancel(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа начальных взаиморасчётов с контрагентом")


class DocOpeningBalanceRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocOpeningBalance] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult
from schemas.api.references.currency import Currency
from schemas.api.references.firm import Firm
from schemas.api.references.partner import Partner


DocOpeningBalanceAddRequest: TypeAlias = DocOpeningBalanceAdd
DocOpeningBalanceAddResponse: TypeAlias = InsertResult
DocOpeningBalanceDeleteMarkRequest: TypeAlias = DocOpeningBalanceDeleteMark
DocOpeningBalanceDeleteMarkResponse: TypeAlias = UpdateResult
DocOpeningBalanceDeleteRequest: TypeAlias = DocOpeningBalanceDelete
DocOpeningBalanceDeleteResponse: TypeAlias = UpdateResult
DocOpeningBalanceEditRequest: TypeAlias = DocOpeningBalanceEdit
DocOpeningBalanceEditResponse: TypeAlias = UpdateResult
DocOpeningBalanceGetRequest: TypeAlias = DocOpeningBalanceGet
DocOpeningBalanceGetResponse: TypeAlias = DocOpeningBalanceRegosOffsettedArrayResult
DocOpeningBalancePerformCancelRequest: TypeAlias = DocOpeningBalancePerformAndCancel
DocOpeningBalancePerformCancelResponse: TypeAlias = UpdateResult
DocOpeningBalancePerformRequest: TypeAlias = DocOpeningBalancePerformAndCancel
DocOpeningBalancePerformResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocOpeningBalance', 'DocOpeningBalanceAdd', 'DocOpeningBalanceColumn', 'DocOpeningBalanceDelete', 'DocOpeningBalanceDeleteMark', 'DocOpeningBalanceEdit', 'DocOpeningBalanceGet', 'DocOpeningBalancePerformAndCancel', 'DocOpeningBalanceRegosOffsettedArrayResult']


__all__ = [
    'DocOpeningBalance',
    'DocOpeningBalanceAdd',
    'DocOpeningBalanceColumn',
    'DocOpeningBalanceColumns',
    'DocOpeningBalanceDelete',
    'DocOpeningBalanceDeleteMark',
    'DocOpeningBalanceEdit',
    'DocOpeningBalanceGet',
    'DocOpeningBalancePerformAndCancel',
    'DocOpeningBalanceRegosOffsettedArrayResult',
    'DocOpeningBalanceGetRequest',
    'DocOpeningBalanceGetResponse',
    'DocOpeningBalanceAddRequest',
    'DocOpeningBalanceAddResponse',
    'DocOpeningBalanceEditRequest',
    'DocOpeningBalanceEditResponse',
    'DocOpeningBalanceDeleteMarkRequest',
    'DocOpeningBalanceDeleteMarkResponse',
    'DocOpeningBalanceDeleteRequest',
    'DocOpeningBalanceDeleteResponse',
    'DocOpeningBalancePerformRequest',
    'DocOpeningBalancePerformResponse',
    'DocOpeningBalancePerformCancelRequest',
    'DocOpeningBalancePerformCancelResponse'
]
