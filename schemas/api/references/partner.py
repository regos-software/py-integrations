"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Partner(RegosModel):
    "Модель, описывающая контрагентов"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="id контрагента")
    group: PartnerGroup | None = PydField(default=None, description="Группа контрагентов")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    fields: list[FieldValue] | None = PydField(default=None, description="Массив значений дополнительных полей")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unixtime в секундах")
    legal_status: LegalStatus | None = PydField(default=None, description="Юридческий статус")
    name: str | None = PydField(default=None)
    fullname: str | None = PydField(default=None)
    boss_name: str | None = PydField(default=None)
    address: str | None = PydField(default=None)
    phones: str | None = PydField(default=None)
    email: str | None = PydField(default=None)
    description: str | None = PydField(default=None)
    inn: str | None = PydField(default=None)
    bank_name: str | None = PydField(default=None)
    mfo: str | None = PydField(default=None)
    rs: str | None = PydField(default=None)
    oked: str | None = PydField(default=None)
    vat_index: str | None = PydField(default=None)


class PartnerAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    group_id: int | None = PydField(default=None, description="id группы контрагента в системе")
    fields: list[FieldValueAdd] | None = PydField(default=None, description="Массив значений дополнительных полей")
    legal_status: LegalStatus | None = PydField(default=None)
    name: str | None = PydField(default=None)
    fullname: str | None = PydField(default=None)
    boss_name: str | None = PydField(default=None)
    address: str | None = PydField(default=None)
    phones: str | None = PydField(default=None)
    email: str | None = PydField(default=None)
    description: str | None = PydField(default=None)
    inn: str | None = PydField(default=None)
    bank_name: str | None = PydField(default=None)
    mfo: str | None = PydField(default=None)
    rs: str | None = PydField(default=None)
    oked: str | None = PydField(default=None)
    vat_index: str | None = PydField(default=None)


class PartnerCurrentBalanceGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id контрагента")
    firm_id: int | None = PydField(default=None, description="Id предприятия")


class PartnerDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id контрагента")


class PartnerDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id контрагента")


class PartnerEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID контрагента")
    group_id: int | None = PydField(default=None, description="ID группы контрагента")
    fields: list[FieldValueEdit] | None = PydField(default=None, description="Массив значений дополнительных полей")
    legal_status: LegalStatus | None = PydField(default=None)
    name: str | None = PydField(default=None)
    fullname: str | None = PydField(default=None)
    boss_name: str | None = PydField(default=None)
    address: str | None = PydField(default=None)
    phones: str | None = PydField(default=None)
    email: str | None = PydField(default=None)
    description: str | None = PydField(default=None)
    inn: str | None = PydField(default=None)
    bank_name: str | None = PydField(default=None)
    mfo: str | None = PydField(default=None)
    rs: str | None = PydField(default=None)
    oked: str | None = PydField(default=None)
    vat_index: str | None = PydField(default=None)


class PartnerGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id контрагентов")
    group_ids: list[int] | None = PydField(default=None, description="Массив id групп контрагентов")
    legal_status: LegalStatus | None = PydField(default=None, description="Юридический статус: <Legal | 1> - юр. лицо, <Natural | 2> - физ. лицо")
    sort_orders: list[PartnerSortOrder] | None = PydField(default=None, description="Сортировка выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по полям: name, fullname, address, inn, rs, phones, email")
    deleted_mark: bool | None = PydField(default=None, description="Пометка на удаление: true - помеченные на удаление, false - не помеченные на удаление")
    filters: list[Filter] | None = PydField(default=None, description="Фильтры по основным и дополнительным полям")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class PartnerRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Partner] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class PartnerSortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: PartnerSortOrderColumnsEnum | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class PartnerSortOrderColumnsEnum(str, Enum):
    default = "default"
    id = "id"
    name = "name"
    legal_status = "legal_status"
    fullname = "fullname"
    boss_name = "boss_name"
    address = "address"
    phones = "phones"
    inn = "inn"
    bank_name = "bank_name"
    mfo = "mfo"
    rs = "rs"
    oked = "oked"
    vat_index = "vat_index"
    last_update = "last_update"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, DecimalRegosObjectResult, Error, InsertResult, LegalStatus, UpdateResult
from schemas.api.common.filter import Filter
from schemas.api.references.field import FieldValue, FieldValueAdd, FieldValueEdit
from schemas.api.references.partner_group import PartnerGroup


LegalStatus: TypeAlias = LegalStatus
PartnerAddRequest: TypeAlias = PartnerAdd
PartnerAddResponse: TypeAlias = InsertResult
PartnerDeleteMarkRequest: TypeAlias = PartnerDeleteMark
PartnerDeleteMarkResponse: TypeAlias = UpdateResult
PartnerDeleteRequest: TypeAlias = PartnerDelete
PartnerDeleteResponse: TypeAlias = UpdateResult
PartnerEditRequest: TypeAlias = PartnerEdit
PartnerEditResponse: TypeAlias = UpdateResult
PartnerGetCurrentBalanceRequest: TypeAlias = PartnerCurrentBalanceGet
PartnerGetCurrentBalanceResponse: TypeAlias = DecimalRegosObjectResult
PartnerGetRequest: TypeAlias = PartnerGet
PartnerGetResponse: TypeAlias = PartnerRegosOffsettedArrayResult


_MODEL_NAMES = ['Partner', 'PartnerAdd', 'PartnerCurrentBalanceGet', 'PartnerDelete', 'PartnerDeleteMark', 'PartnerEdit', 'PartnerGet', 'PartnerRegosOffsettedArrayResult', 'PartnerSortOrder']


__all__ = [
    'Partner',
    'PartnerAdd',
    'PartnerCurrentBalanceGet',
    'PartnerDelete',
    'PartnerDeleteMark',
    'PartnerEdit',
    'PartnerGet',
    'PartnerRegosOffsettedArrayResult',
    'PartnerSortOrder',
    'PartnerSortOrderColumnsEnum',
    'PartnerGetRequest',
    'PartnerGetResponse',
    'PartnerAddRequest',
    'PartnerAddResponse',
    'PartnerEditRequest',
    'PartnerEditResponse',
    'PartnerDeleteMarkRequest',
    'PartnerDeleteMarkResponse',
    'PartnerDeleteRequest',
    'PartnerDeleteResponse',
    'PartnerGetCurrentBalanceRequest',
    'PartnerGetCurrentBalanceResponse',
    'LegalStatus'
]
