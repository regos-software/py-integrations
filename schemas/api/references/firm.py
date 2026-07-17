"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Firm(RegosModel):
    "Модель, описывающая предприятия"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="id предприятия")
    group: FirmGroup | None = PydField(default=None, description="id группы предприятия")
    deleted_mark: bool | None = PydField(default=None, description="Метка на удаление")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unixtime в секундах")
    name: str | None = PydField(default=None)
    fullname: str | None = PydField(default=None)
    boss_name: str | None = PydField(default=None)
    address: str | None = PydField(default=None)
    phones: str | None = PydField(default=None)
    description: str | None = PydField(default=None)
    inn: str | None = PydField(default=None)
    bank_name: str | None = PydField(default=None)
    mfo: str | None = PydField(default=None)
    rs: str | None = PydField(default=None)
    oked: str | None = PydField(default=None)
    vat_index: str | None = PydField(default=None)


class FirmAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    group_id: int | None = PydField(default=None, description="id группы предприятия в системе")
    name: str | None = PydField(default=None)
    fullname: str | None = PydField(default=None)
    boss_name: str | None = PydField(default=None)
    address: str | None = PydField(default=None)
    phones: str | None = PydField(default=None)
    description: str | None = PydField(default=None)
    inn: str | None = PydField(default=None)
    bank_name: str | None = PydField(default=None)
    mfo: str | None = PydField(default=None)
    rs: str | None = PydField(default=None)
    oked: str | None = PydField(default=None)
    vat_index: str | None = PydField(default=None)


class FirmDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id предприятия")


class FirmDeleteConfirm(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    confirm_code: str | None = PydField(default=None, description="Код подтверждения")
    id: int | None = PydField(default=None, description="Id предприятия")


class FirmDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id предприятия")


class FirmEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID пердприятия")
    group_id: int | None = PydField(default=None, description="id группы предприятия в системе")
    name: str | None = PydField(default=None)
    fullname: str | None = PydField(default=None)
    boss_name: str | None = PydField(default=None)
    address: str | None = PydField(default=None)
    phones: str | None = PydField(default=None)
    description: str | None = PydField(default=None)
    inn: str | None = PydField(default=None)
    bank_name: str | None = PydField(default=None)
    mfo: str | None = PydField(default=None)
    rs: str | None = PydField(default=None)
    oked: str | None = PydField(default=None)
    vat_index: str | None = PydField(default=None)


class FirmGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    deleted_mark: bool | None = PydField(default=None, description="Помеченные на удаление: null - показывает всё, true - только помеченнае на удаление, false - не помечанные на удаление")
    ids: list[int] | None = PydField(default=None, description="Массив id предприятий")
    group_ids: list[int] | None = PydField(default=None, description="Массив id групп предприятий")
    sort_orders: list[FirmSortOrder] | None = PydField(default=None, description="Сортировка выходных данных")
    search: str | None = PydField(default=None, description="Строка поиска по полям: name, fullname, address, inn, rs")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class FirmImage(RegosModel):
    "Модель, описывающая изображения предприятия"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    firm_id: int | None = PydField(default=None, description="Id предприятия")
    id: int | None = PydField(default=None)
    width: int | None = PydField(default=None)
    height: int | None = PydField(default=None)
    size: int | None = PydField(default=None)
    file: str | None = PydField(default=None)
    url: str | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


class FirmImageDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)


class FirmImageGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    firm_id: int | None = PydField(default=None, description="Id предприятия")
    ids: list[int] | None = PydField(default=None)
    include_data: bool | None = PydField(default=None)
    compress_data: bool | None = PydField(default=None)


class FirmImageRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[FirmImage] | Error | None = PydField(default=None, description="Массив результата.")


class FirmRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Firm] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class FirmSetting(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None)
    key: str | None = PydField(default=None)
    name: str | None = PydField(default=None)
    value: str | None = PydField(default=None)
    name_var: str | None = PydField(default=None, description="Наименование (ключ из переводов)")
    dataType: str | None = PydField(default=None, description="Тип данных")
    last_update: int | None = PydField(default=None)


class FirmSettingArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[FirmSetting] | Error | None = PydField(default=None, description="Объект результата.")


class FirmSortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: FirmSortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class FirmSortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    Name = "Name"
    Fullname = "Fullname"
    Bossname = "Bossname"
    Address = "Address"
    Phones = "Phones"
    Inn = "Inn"
    BankName = "BankName"
    Mfo = "Mfo"
    Rs = "Rs"
    Oked = "Oked"
    VatIndex = "VatIndex"
    LastUpdate = "LastUpdate"


class Firm_SettingEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID настройки пердприятия")
    value: str | None = PydField(default=None, description="значение настройки")


class Firm_SettingGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    firm_id: int | None = PydField(default=None, description="ID предприятия")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ApiResult, ColumnSortOrderDirection, Error, InsertResult, UpdateResult
from schemas.api.references.firm_group import FirmGroup


FirmAddImageResponse: TypeAlias = UpdateResult
FirmAddRequest: TypeAlias = FirmAdd
FirmAddResponse: TypeAlias = InsertResult
FirmDeleteConfirmRequest: TypeAlias = FirmDeleteConfirm
FirmDeleteConfirmResponse: TypeAlias = ApiResult
FirmDeleteImageRequest: TypeAlias = FirmImageDelete
FirmDeleteImageResponse: TypeAlias = UpdateResult
FirmDeleteMarkRequest: TypeAlias = FirmDeleteMark
FirmDeleteMarkResponse: TypeAlias = UpdateResult
FirmDeleteRequest: TypeAlias = FirmDelete
FirmDeleteResponse: TypeAlias = ApiResult
FirmEditRequest: TypeAlias = FirmEdit
FirmEditResponse: TypeAlias = UpdateResult
FirmEditSettingsRequest: TypeAlias = list[Firm_SettingEdit]
FirmEditSettingsResponse: TypeAlias = UpdateResult
FirmGetImageRequest: TypeAlias = FirmImageGet
FirmGetImageResponse: TypeAlias = FirmImageRegosArrayResult
FirmGetRequest: TypeAlias = FirmGet
FirmGetResponse: TypeAlias = FirmRegosOffsettedArrayResult
FirmGetSettingsRequest: TypeAlias = Firm_SettingGet
FirmGetSettingsResponse: TypeAlias = FirmSettingArrayRegosObjectResult


_MODEL_NAMES = ['Firm', 'FirmAdd', 'FirmDelete', 'FirmDeleteConfirm', 'FirmDeleteMark', 'FirmEdit', 'FirmGet', 'FirmImage', 'FirmImageDelete', 'FirmImageGet', 'FirmImageRegosArrayResult', 'FirmRegosOffsettedArrayResult', 'FirmSetting', 'FirmSettingArrayRegosObjectResult', 'FirmSortOrder', 'Firm_SettingEdit', 'Firm_SettingGet']


__all__ = [
    'Firm',
    'FirmAdd',
    'FirmDelete',
    'FirmDeleteConfirm',
    'FirmDeleteMark',
    'FirmEdit',
    'FirmGet',
    'FirmImage',
    'FirmImageDelete',
    'FirmImageGet',
    'FirmImageRegosArrayResult',
    'FirmRegosOffsettedArrayResult',
    'FirmSetting',
    'FirmSettingArrayRegosObjectResult',
    'FirmSortOrder',
    'FirmSortOrderColumn',
    'Firm_SettingEdit',
    'Firm_SettingGet',
    'FirmGetRequest',
    'FirmGetResponse',
    'FirmAddRequest',
    'FirmAddResponse',
    'FirmEditRequest',
    'FirmEditResponse',
    'FirmDeleteMarkRequest',
    'FirmDeleteMarkResponse',
    'FirmDeleteRequest',
    'FirmDeleteResponse',
    'FirmDeleteConfirmRequest',
    'FirmDeleteConfirmResponse',
    'FirmGetImageRequest',
    'FirmGetImageResponse',
    'FirmAddImageResponse',
    'FirmDeleteImageRequest',
    'FirmDeleteImageResponse',
    'FirmGetSettingsRequest',
    'FirmGetSettingsResponse',
    'FirmEditSettingsRequest',
    'FirmEditSettingsResponse'
]
