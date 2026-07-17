"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocAccountMovement(RegosModel):
    "Модель, описывающая перевод со счёта на счёт"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа перевода")
    code: str | None = PydField(default=None, description="Код документа перевода")
    date: int | None = PydField(default=None, description="Дата документа перевода в формате unix time в секундах")
    firm: Firm | None = PydField(default=None, description="Предприятие")
    account_sender: Account | None = PydField(default=None, description="Счёт отправителя")
    amount_sended: _Decimal | None = PydField(default=None, description="Отправленная сумма")
    account_receiver: Account | None = PydField(default=None, description="Счёт получателя")
    amount_received: _Decimal | None = PydField(default=None, description="Полученная сумма")
    description: str | None = PydField(default=None, description="Примечание")
    attached_user: User | None = PydField(default=None, description="Пользователь, ответственный за перевод")
    fields: list[FieldValue] | None = PydField(default=None, description="Массив значений дополнительных полей")
    performed: bool | None = PydField(default=None, description="Успешность перевода")
    deleted_mark: bool | None = PydField(default=None, description="Пометка на удаление документа перевода")
    last_update: int | None = PydField(default=None, description="Дата последнего обновления в формате unix time в секундах")


class DocAccountMovementAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: int | None = PydField(default=None, description="Дата создания документа перевода в формате unixtime в секундах")
    firm_id: int | None = PydField(default=None, description="ID предприятия")
    account_sender_id: int | None = PydField(default=None, description="ID счёта отправителя")
    account_receiver_id: int | None = PydField(default=None, description="ID счёта получателя")
    amount_sended: _Decimal | None = PydField(default=None, description="Отправленная сумма")
    amount_received: _Decimal | None = PydField(default=None, description="Полученная сумма")
    description: str | None = PydField(default=None, description="Примечание")
    fields: list[FieldValueAdd] | None = PydField(default=None, description="Массив значений дополнительных полей")
    attached_user_id: int | None = PydField(default=None, description="ID пользователя, ответственного за перевод")


class DocAccountMovementColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocAccountMovementColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocAccountMovementColumns(str, Enum):
    default = "default"
    id = "id"
    code = "code"
    date = "date"
    firm_name = "firm.name"
    account_sender_name = "account_sender.name"
    amount_sended = "amount_sended"
    account_receiver_name = "account_receiver.name"
    amount_received = "amount_received"
    attached_user_name = "attached_user.name"
    performed = "performed"
    deleted_mark = "deleted_mark"
    last_update = "last_update"


class DocAccountMovementDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа перевода со счёта на счёт")


class DocAccountMovementDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа перевода со счёта на счёт")


class DocAccountMovementEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа перевода со счёта на счёт")
    date: int | None = PydField(default=None, description="Дата создания перевода")
    amount_sended: _Decimal | None = PydField(default=None, description="Отправленная сумма")
    amount_received: _Decimal | None = PydField(default=None, description="Полученная сумма")
    description: str | None = PydField(default=None, description="Примечание")
    attached_user_id: int | None = PydField(default=None, description="Пользователь, товетственный за перевод")
    fields: list[FieldValueEdit] | None = PydField(default=None, description="Массив значений дополнительных полей")


class DocAccountMovementGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Дата в формате unix time в секундах, начиная с которой будут возвращены документы перевода со счёта на счёт")
    end_date: int | None = PydField(default=None, description="Дата в формате unix time в секундах, по которую будут возвращены документы перевода со счёта на счёт")
    ids: list[int] | None = PydField(default=None, description="Массив ID документов перевода со счёта на счёт")
    firm_ids: list[int] | None = PydField(default=None, description="Массив ID предприятий")
    attached_user_ids: list[int] | None = PydField(default=None, description="Массив ID пользователей")
    sort_orders: list[DocAccountMovementColumn] | None = PydField(default=None, description="Сортировка выходных параметров")
    search: str | None = PydField(default=None, description="Поиск про значениям параметров: code - Код документа, Firm/name - Наименование предприятия, Firm/inn - ИНН предприятия,\nsender_account_name - Наименование счёта отправителя, receiver_account_name - Наименование счёта получателя, User/name -\nФИО ответственного лица")
    filters: list[Filter] | None = PydField(default=None, description="Фильтры по основным и дополнительным полям")
    performed: bool | None = PydField(default=None, description="Состояние проведение документа: true - Проведён, false - Не проведён")
    deleted_mark: bool | None = PydField(default=None, description="Состояние пометки на удаление: true - Помечен на удаление, false - Не помечен на удаление")
    limit: int | None = PydField(default=None, description="Ограничение по количеству возвращаемых объектов")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки на сервере")


class DocAccountMovementPerformAndCancel(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа перевода со счёта на счёт")


class DocAccountMovementRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocAccountMovement] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult
from schemas.api.common.filter import Filter
from schemas.api.rbac.user import User
from schemas.api.references.account import Account
from schemas.api.references.field import FieldValue, FieldValueAdd, FieldValueEdit
from schemas.api.references.firm import Firm


DocAccountMovementAddRequest: TypeAlias = DocAccountMovementAdd
DocAccountMovementAddResponse: TypeAlias = InsertResult
DocAccountMovementDeleteMarkRequest: TypeAlias = DocAccountMovementDeleteMark
DocAccountMovementDeleteMarkResponse: TypeAlias = UpdateResult
DocAccountMovementDeleteRequest: TypeAlias = DocAccountMovementDelete
DocAccountMovementDeleteResponse: TypeAlias = UpdateResult
DocAccountMovementEditRequest: TypeAlias = DocAccountMovementEdit
DocAccountMovementEditResponse: TypeAlias = UpdateResult
DocAccountMovementGetRequest: TypeAlias = DocAccountMovementGet
DocAccountMovementGetResponse: TypeAlias = DocAccountMovementRegosOffsettedArrayResult
DocAccountMovementPerformCancelRequest: TypeAlias = DocAccountMovementPerformAndCancel
DocAccountMovementPerformCancelResponse: TypeAlias = UpdateResult
DocAccountMovementPerformRequest: TypeAlias = DocAccountMovementPerformAndCancel
DocAccountMovementPerformResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocAccountMovement', 'DocAccountMovementAdd', 'DocAccountMovementColumn', 'DocAccountMovementDelete', 'DocAccountMovementDeleteMark', 'DocAccountMovementEdit', 'DocAccountMovementGet', 'DocAccountMovementPerformAndCancel', 'DocAccountMovementRegosOffsettedArrayResult']


__all__ = [
    'DocAccountMovement',
    'DocAccountMovementAdd',
    'DocAccountMovementColumn',
    'DocAccountMovementColumns',
    'DocAccountMovementDelete',
    'DocAccountMovementDeleteMark',
    'DocAccountMovementEdit',
    'DocAccountMovementGet',
    'DocAccountMovementPerformAndCancel',
    'DocAccountMovementRegosOffsettedArrayResult',
    'DocAccountMovementGetRequest',
    'DocAccountMovementGetResponse',
    'DocAccountMovementAddRequest',
    'DocAccountMovementAddResponse',
    'DocAccountMovementEditRequest',
    'DocAccountMovementEditResponse',
    'DocAccountMovementDeleteMarkRequest',
    'DocAccountMovementDeleteMarkResponse',
    'DocAccountMovementDeleteRequest',
    'DocAccountMovementDeleteResponse',
    'DocAccountMovementPerformRequest',
    'DocAccountMovementPerformResponse',
    'DocAccountMovementPerformCancelRequest',
    'DocAccountMovementPerformCancelResponse'
]
