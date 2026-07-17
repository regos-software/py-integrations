"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocAdditionalExpenses(RegosModel):
    "Модель, описывающая документ дополнительных расходов"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа дополнительных расходов")
    date: int | None = PydField(default=None, description="Дата документа дополнительных расходов в формате unix time в секундах")
    code: str | None = PydField(default=None, description="Код документа дополнительных расходов")
    parent_document: DocShort | None = PydField(default=None, description="Родительский документ")
    partner: Partner | None = PydField(default=None, description="Контрагент")
    stock: Stock | None = PydField(default=None, description="Склад")
    currency: Currency | None = PydField(default=None, description="Валюта документа дополнительных расходов")
    contract: DocContractShort | None = PydField(default=None, description="Договор")
    description: str | None = PydField(default=None, description="Примечание")
    amount: _Decimal | None = PydField(default=None, description="Сумма документа дополнительных расходов")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс к основной валюте")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    blocked: bool | None = PydField(default=None, description="Статус блокировки для редактирования документа дополнительных расходов: true - Заблокирован, false - Разблокирован")
    current_user_blocked: bool | None = PydField(default=None, description="Статус блокировки для редактирования документа дополнительных расходов текущим пользователем: true - Заблокирован\nтекущим пользователем, false - Не заблокирован текущим пользователем")
    performed: bool | None = PydField(default=None, description="Статус проведения документа дополнительных расходов: true - Проведён, false - Не проведён")
    deleted_mark: bool | None = PydField(default=None, description="Статус пометки на удаление документа дополнительных расходов: true - Номечен на удаление, false - Не помечен на удаление")
    last_update: int | None = PydField(default=None, description="Время последнего изменения записи в формате unix time")


class DocAdditionalExpensesAdd(RegosModel):
    "Модель для добавления документа дополнительных расходов"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: int | None = PydField(default=None, description="Дата документа дополнительных расходов в формате Unix time")
    parent_doc_type_id: int | None = PydField(default=None, description="ID типа родительского документа")
    parent_doc_id: int | None = PydField(default=None, description="ID родительского документа")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    stock_id: int | None = PydField(default=None, description="ID склада")
    currency_id: int | None = PydField(default=None, description="ID валюты")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    contract_id: int | None = PydField(default=None, description="ID договора")
    description: str | None = PydField(default=None, description="Коментарий")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")


class DocAdditionalExpensesEdit(RegosModel):
    "Модель для добавления документа дополнительных расходов"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа дополнительных расходов")
    date: int | None = PydField(default=None, description="Дата документа дополнительных расходов в формате Unix time")
    stock_id: int | None = PydField(default=None, description="ID склада")
    currency_id: int | None = PydField(default=None, description="ID валюты")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    contract_id: int | None = PydField(default=None, description="ID договора. Чтобы убрать договор нужно отправить 0 в значении")
    description: str | None = PydField(default=None, description="Коментарий")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")


class DocAdditionalExpensesGet(RegosModel):
    "Модель для получения списка документов дополнительных расходов"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time")
    ids: list[int] | None = PydField(default=None, description="Массив ID документов дополнительных расходов")
    firm_ids: list[int] | None = PydField(default=None, description="Массив ID предприятий")
    stock_ids: list[int] | None = PydField(default=None, description="Массив ID складов")
    partner_ids: list[int] | None = PydField(default=None, description="Массив ID контрагентов")
    contract_ids: list[int] | None = PydField(default=None, description="Массив ID договоров")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    parent_doc_type_id: int | None = PydField(default=None, description="ID типа родительского документа")
    parent_doc_id: int | None = PydField(default=None, description="ID родительского документа")
    search: str | None = PydField(default=None, description="Поиск про значениям параметров: code - Код документа дополнительных расходов, Partner/name - Наименование контрагента,\nPartner/inn - ИНН контрагента, DocContract/code - Код договора, Stock/name - Наименование склада, Firm/name -\nНаименование предприятия, Firm/inn - ИНН предприятия")
    sort_orders: list[BaseSortColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    performed: bool | None = PydField(default=None, description="Статус проведения документа дополнительных расходов: true - Проведён, false - Не проведён")
    blocked: bool | None = PydField(default=None, description="Статус блокировки для редактирования документа дополнительных расходов: true - Заблокирован, false - Разблокирован")
    deleted_mark: bool | None = PydField(default=None, description="Статус пометки на удаление документа дополнительных расходов: true - Номечен на удаление, false - Не помечен на удаление")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocAdditionalExpensesRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocAdditionalExpenses] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class DocShort(RegosModel):
    "Описание сокращённой модели документа"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа")
    doc_type: int | None = PydField(default=None, description="Тип документа")
    date: int | None = PydField(default=None, description="Дата документа в unixtime")
    code: str | None = PydField(default=None, description="Код документа")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import BaseLockAndUnlock, BaseSortColumn, Base_ID, Error, InsertResult, UpdateResult, VatCalculationTypeEnum
from schemas.api.docs.doc_contract import DocContractShort
from schemas.api.references.currency import Currency
from schemas.api.references.partner import Partner
from schemas.api.references.stock import Stock


DocAdditionalExpensesAddRequest: TypeAlias = DocAdditionalExpensesAdd
DocAdditionalExpensesAddResponse: TypeAlias = InsertResult
DocAdditionalExpensesDeleteMarkRequest: TypeAlias = Base_ID
DocAdditionalExpensesDeleteMarkResponse: TypeAlias = UpdateResult
DocAdditionalExpensesDeleteRequest: TypeAlias = Base_ID
DocAdditionalExpensesDeleteResponse: TypeAlias = UpdateResult
DocAdditionalExpensesEditRequest: TypeAlias = DocAdditionalExpensesEdit
DocAdditionalExpensesEditResponse: TypeAlias = UpdateResult
DocAdditionalExpensesGetRequest: TypeAlias = DocAdditionalExpensesGet
DocAdditionalExpensesGetResponse: TypeAlias = DocAdditionalExpensesRegosOffsettedArrayResult
DocAdditionalExpensesLockRequest: TypeAlias = BaseLockAndUnlock
DocAdditionalExpensesLockResponse: TypeAlias = UpdateResult
DocAdditionalExpensesPerformCancelRequest: TypeAlias = Base_ID
DocAdditionalExpensesPerformCancelResponse: TypeAlias = UpdateResult
DocAdditionalExpensesPerformRequest: TypeAlias = Base_ID
DocAdditionalExpensesPerformResponse: TypeAlias = UpdateResult
DocAdditionalExpensesUnlockRequest: TypeAlias = BaseLockAndUnlock
DocAdditionalExpensesUnlockResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocAdditionalExpenses', 'DocAdditionalExpensesAdd', 'DocAdditionalExpensesEdit', 'DocAdditionalExpensesGet', 'DocAdditionalExpensesRegosOffsettedArrayResult', 'DocShort']


__all__ = [
    'DocAdditionalExpenses',
    'DocAdditionalExpensesAdd',
    'DocAdditionalExpensesEdit',
    'DocAdditionalExpensesGet',
    'DocAdditionalExpensesRegosOffsettedArrayResult',
    'DocShort',
    'DocAdditionalExpensesGetRequest',
    'DocAdditionalExpensesGetResponse',
    'DocAdditionalExpensesAddRequest',
    'DocAdditionalExpensesAddResponse',
    'DocAdditionalExpensesEditRequest',
    'DocAdditionalExpensesEditResponse',
    'DocAdditionalExpensesDeleteMarkRequest',
    'DocAdditionalExpensesDeleteMarkResponse',
    'DocAdditionalExpensesDeleteRequest',
    'DocAdditionalExpensesDeleteResponse',
    'DocAdditionalExpensesLockRequest',
    'DocAdditionalExpensesLockResponse',
    'DocAdditionalExpensesUnlockRequest',
    'DocAdditionalExpensesUnlockResponse',
    'DocAdditionalExpensesPerformRequest',
    'DocAdditionalExpensesPerformResponse',
    'DocAdditionalExpensesPerformCancelRequest',
    'DocAdditionalExpensesPerformCancelResponse'
]
