"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocPayment(RegosModel):
    "Модель, описывающая документ платежа"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа платежа")
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    code: str | None = PydField(default=None, description="Код документа")
    type: PaymentType | None = PydField(default=None, description="Форма оплаты")
    document_id: int | None = PydField(default=None, description="ID документа, на основании которого производится оплата")
    document_type_id: int | None = PydField(default=None, description="ID типа документа, на основании которого производится оплата")
    contract: DocContractShort | None = PydField(default=None, description="Документ договора")
    firm: Firm | None = PydField(default=None, description="Предприятие")
    partner: Partner | None = PydField(default=None, description="Контрагент")
    category: AccountOperationCategory | None = PydField(default=None, description="Статья дохода или расхода")
    amount: _Decimal | None = PydField(default=None, description="Сумма документа оплаты")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    attached_user: User | None = PydField(default=None, description="Ответственное лицо")
    fields: list[FieldValue] | None = PydField(default=None, description="Массив значений дополнительных полей")
    performed: bool | None = PydField(default=None, description="Метка о проведении документа")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocPaymentAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    type_id: int | None = PydField(default=None, description="ID типа оплаты")
    document: int | None = PydField(default=None, description="ID документа, на основании которого производится оплата")
    document_type_id: int | None = PydField(default=None, description="ID типа документа, на основании которого производится оплата")
    firm_id: int | None = PydField(default=None, description="ID предприятия, которое участвует в оплате")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    category_id: int | None = PydField(default=None, description="ID категории операции со счетом")
    contract_id: int | None = PydField(default=None, description="ID документа договора")
    amount: _Decimal | None = PydField(default=None, description="Сумма документа оплаты")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    fields: list[FieldValueAdd] | None = PydField(default=None, description="Массив значений дополнительных полей")


class DocPaymentColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocPaymentColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocPaymentColumns(str, Enum):
    default = "default"
    id = "id"
    date = "date"
    code = "code"
    type_name = "type.name"
    contract_name = "contract.name"
    firm_name = "firm.name"
    partner_name = "partner.name"
    category_name = "category.name"
    amount = "amount"
    attached_user_first_name = "attached_user.first_name"
    performed = "performed"
    deleted_mark = "deleted_mark"
    last_update = "last_update"
    category_positive = "category.positive"


class DocPaymentDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа платежа")


class DocPaymentDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа платежа")


class DocPaymentEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа платежа")
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    type_id: int | None = PydField(default=None, description="ID типа оплаты")
    contract_id: int | None = PydField(default=None, description="ID документа договора")
    firm_id: int | None = PydField(default=None, description="ID предприятия, которое участвует в оплате")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    category_id: int | None = PydField(default=None, description="ID категории операции со счетом")
    amount: _Decimal | None = PydField(default=None, description="Сумма документа оплаты")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    fields: list[FieldValueEdit] | None = PydField(default=None, description="Массив значений дополнительных полей")


class DocPaymentGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    payment_direction: PaymentDirection | None = PydField(default=None, description="Тип направления оплаты документа: <Income | 1> - Входящий платёж, <Outcome | 2> - Исходящий платёж")
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате Unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате Unix time в секундах")
    ids: list[int] | None = PydField(default=None, description="Массив ID документов оплаты")
    partner_ids: list[int] | None = PydField(default=None, description="Массив ID контрагентов")
    firm_ids: list[int] | None = PydField(default=None, description="Массив ID предприятий")
    category_ids: list[int] | None = PydField(default=None, description="Массив ID статей дохода или расхода")
    contract_ids: list[int] | None = PydField(default=None, description="Массив ID договоров")
    document_type_ids: list[int] | None = PydField(default=None, description="Массив ID типов документов")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов")
    attached_user_ids: list[int] | None = PydField(default=None, description="Массив ID ответственных пользователей")
    sort_orders: list[DocPaymentColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    filters: list[Filter] | None = PydField(default=None, description="Фильтры по основным и дополнительным полям")
    search: str | None = PydField(default=None, description="Поиск про значениям параметров: code - Код документа, DocContract/code - Код договора, Partner/name - Наименование\nконтрагента, Partner/inn - ИНН контрагента, User/name - ФИО ответственного лица, Firm/name - Наименование предприятия,\nFirm/inn - ИНН предприятия")
    performed: bool | None = PydField(default=None, description="Состояние проведение документа: true - Проведён, false - Не проведён")
    deleted_mark: bool | None = PydField(default=None, description="Состояние пометки на удаление: true - Помечен на удаление, false - Не помечен на удаление")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocPaymentPerformAndCancel(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа платежа")


class DocPaymentRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocPayment] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class PaymentDirection(str, Enum):
    All = "All"
    Income = "Income"
    Outcome = "Outcome"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult
from schemas.api.common.filter import Filter
from schemas.api.docs.doc_contract import DocContractShort
from schemas.api.rbac.user import User
from schemas.api.references.account_operation_category import AccountOperationCategory
from schemas.api.references.field import FieldValue, FieldValueAdd, FieldValueEdit
from schemas.api.references.firm import Firm
from schemas.api.references.partner import Partner
from schemas.api.references.payment_type import PaymentType


DocPaymentAddRequest: TypeAlias = DocPaymentAdd
DocPaymentAddResponse: TypeAlias = InsertResult
DocPaymentDeleteMarkRequest: TypeAlias = DocPaymentDeleteMark
DocPaymentDeleteMarkResponse: TypeAlias = UpdateResult
DocPaymentDeleteRequest: TypeAlias = DocPaymentDelete
DocPaymentDeleteResponse: TypeAlias = UpdateResult
DocPaymentEditRequest: TypeAlias = DocPaymentEdit
DocPaymentEditResponse: TypeAlias = UpdateResult
DocPaymentGetRequest: TypeAlias = DocPaymentGet
DocPaymentGetResponse: TypeAlias = DocPaymentRegosOffsettedArrayResult
DocPaymentPerformCancelRequest: TypeAlias = DocPaymentPerformAndCancel
DocPaymentPerformCancelResponse: TypeAlias = UpdateResult
DocPaymentPerformRequest: TypeAlias = DocPaymentPerformAndCancel
DocPaymentPerformResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocPayment', 'DocPaymentAdd', 'DocPaymentColumn', 'DocPaymentDelete', 'DocPaymentDeleteMark', 'DocPaymentEdit', 'DocPaymentGet', 'DocPaymentPerformAndCancel', 'DocPaymentRegosOffsettedArrayResult']


__all__ = [
    'DocPayment',
    'DocPaymentAdd',
    'DocPaymentColumn',
    'DocPaymentColumns',
    'DocPaymentDelete',
    'DocPaymentDeleteMark',
    'DocPaymentEdit',
    'DocPaymentGet',
    'DocPaymentPerformAndCancel',
    'DocPaymentRegosOffsettedArrayResult',
    'PaymentDirection',
    'DocPaymentGetRequest',
    'DocPaymentGetResponse',
    'DocPaymentAddRequest',
    'DocPaymentAddResponse',
    'DocPaymentEditRequest',
    'DocPaymentEditResponse',
    'DocPaymentDeleteMarkRequest',
    'DocPaymentDeleteMarkResponse',
    'DocPaymentDeleteRequest',
    'DocPaymentDeleteResponse',
    'DocPaymentPerformRequest',
    'DocPaymentPerformResponse',
    'DocPaymentPerformCancelRequest',
    'DocPaymentPerformCancelResponse'
]
