"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class OperatingCash(RegosModel):
    "Модель, описывающая кассы розничной торговли"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="id розничной кассы")
    stock: Stock | None = PydField(default=None, description="склад, к которому относится касса")
    key: str | None = PydField(default=None, description="Ключ безопастности розничной кассы")
    price_type: PriceType | None = PydField(default=None, description="Вид цены")
    description: str | None = PydField(default=None, description="Дополнительно описание")
    virtual: bool | None = PydField(default=None, description="Метка о том, что касса виртуальная")
    auto_close: bool | None = PydField(default=None, description="Автоматическое закрытие смены при достижении максимального кол-ва чеков за смену")
    max_cheque_quantity_in_session: int | None = PydField(default=None, description="Максимальное количество чеков за смену")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")
    UserAccept: User | None = PydField(default=None, description="Пользователь, который принял кассу в работу")


class OperatingCashAccept(RegosModel):
    "модель для принятия кассы в работу"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    operating_cash_id: int | None = PydField(default=None, description="ID кассы")


class OperatingCashAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    stock_id: int | None = PydField(default=None, description="ID склада, к которому относится касса")
    key: str | None = PydField(default=None, description="Ключ безопастности розничной кассы")
    price_type_id: int | None = PydField(default=None, description="ID вида цены")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    virtual: bool | None = PydField(default=None, description="Метка о том, что касса виртуальная")
    auto_close: bool | None = PydField(default=None, description="Автоматическое закрытие смены при достижении максимального кол-ва чеков за смену")
    max_cheque_quantity_in_session: int | None = PydField(default=None, description="Максимальное количество чеков за смену")


class OperatingCashChequeTemplate(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None)
    type_id: int | None = PydField(default=None)
    operating_cash_id: int | None = PydField(default=None)
    template: str | None = PydField(default=None)
    logo: int | None = PydField(default=None, description="id файла, которое используется в качестве логотипа")
    logo_width: int | None = PydField(default=None, description="ширина логотипа при выводе")
    logo_height: int | None = PydField(default=None, description="высота логотипа при выводе")
    last_update: int | None = PydField(default=None)


class OperatingCashChequeTemplateEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID шаблона чека")
    logo: int | None = PydField(default=None, description="ID файла логотипа шаблона чека")
    logo_width: int | None = PydField(default=None, description="Ширина логотипа при выводе")
    logo_height: int | None = PydField(default=None, description="Высота логотипа при выводе")
    template: str | None = PydField(default=None, description="Шаблон чека (строка в формате json)")


class OperatingCashChequeTemplateGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id чеков")
    operating_cash_ids: list[int] | None = PydField(default=None, description="Массив id касс")
    cheque_type_ids: list[int] | None = PydField(default=None, description="Массив id типов чека")


class OperatingCashChequeTemplateRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[OperatingCashChequeTemplate] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class OperatingCashDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id кассы розничной торговли")


class OperatingCashDiscard(RegosModel):
    "модель для сдачи кассы"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    operating_cash_id: int | None = PydField(default=None, description="ID кассы")
    description: str | None = PydField(default=None, description="Дополнительное описание")


class OperatingCashEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID кассы")
    stock_id: int | None = PydField(default=None, description="ID склада, к которому относится касса")
    key: str | None = PydField(default=None, description="Ключ безопастности розничной кассы")
    price_type_id: int | None = PydField(default=None, description="ID вида цены")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    auto_close: bool | None = PydField(default=None, description="Автоматическое закрытие смены при достижении максимального кол-ва чеков за смену")
    max_cheque_quantity_in_session: int | None = PydField(default=None, description="Максимальное количество чеков за смену")


class OperatingCashGet(RegosModel):
    "модель для получения списка касс"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id касс")
    firm_ids: list[int] | None = PydField(default=None, description="Массив id предприятий")
    stock_ids: list[int] | None = PydField(default=None, description="Массив id складов")
    price_type_ids: list[int] | None = PydField(default=None, description="массив id видов цен")
    is_virtual: bool | None = PydField(default=None, description="Метка о том, что касса виртуальная: true - виртуальная, false - не виртуальная")
    accepted_user_id: int | None = PydField(default=None, description="Id пользователя, который принял кассу в работу")
    sort_orders: list[OperatingCash_SortOrder] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: id - ID кассы, key - Ключ безопасности, stock_name - Наимнование склада, user_accept_name - Имя пользователя на кассе")
    limit: int | None = PydField(default=None, description="Количество элементов выборки, возвращаемых при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class OperatingCashImage(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    operating_cash_id: int | None = PydField(default=None)
    id: int | None = PydField(default=None)
    width: int | None = PydField(default=None)
    height: int | None = PydField(default=None)
    size: int | None = PydField(default=None)
    file: str | None = PydField(default=None)
    url: str | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


class OperatingCashImageDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)


class OperatingCashImageGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    operating_cash_id: int | None = PydField(default=None, description="ID кассы")
    ids: list[int] | None = PydField(default=None)
    include_data: bool | None = PydField(default=None)
    compress_data: bool | None = PydField(default=None)


class OperatingCashImageRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[OperatingCashImage] | Error | None = PydField(default=None, description="Массив результата.")


class OperatingCashRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[OperatingCash] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class OperatingCash_Setting(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None)
    key: str | None = PydField(default=None)
    name: str | None = PydField(default=None)
    name_var: str | None = PydField(default=None)
    value: str | None = PydField(default=None)


class OperatingCash_SettingArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[OperatingCash_Setting] | Error | None = PydField(default=None, description="Объект результата.")


class OperatingCash_SettingEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID настройки кассы")
    value: str | None = PydField(default=None, description="Значение настройки кассы")


class OperatingCash_SettingGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    operating_cash_id: int | None = PydField(default=None, description="id кассы")


class OperatingCash_SortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: OperatingCash_SortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class OperatingCash_SortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    StockName = "StockName"
    Key = "Key"
    PriceTypeName = "PriceTypeName"
    Virtual = "Virtual"
    AutoClose = "AutoClose"
    UserAcceptName = "UserAcceptName"
    LastUpdate = "LastUpdate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, ObjectRegosObjectResult, UpdateResult
from schemas.api.rbac.user import User
from schemas.api.references.price_type import PriceType
from schemas.api.references.stock import Stock


OperatingCashAcceptRequest: TypeAlias = OperatingCashAccept
OperatingCashAcceptResponse: TypeAlias = ObjectRegosObjectResult
OperatingCashAddImageResponse: TypeAlias = UpdateResult
OperatingCashAddRequest: TypeAlias = OperatingCashAdd
OperatingCashAddResponse: TypeAlias = InsertResult
OperatingCashDeleteImageRequest: TypeAlias = OperatingCashImageDelete
OperatingCashDeleteImageResponse: TypeAlias = UpdateResult
OperatingCashDeleteRequest: TypeAlias = OperatingCashDelete
OperatingCashDeleteResponse: TypeAlias = UpdateResult
OperatingCashDiscardRequest: TypeAlias = OperatingCashDiscard
OperatingCashDiscardResponse: TypeAlias = ObjectRegosObjectResult
OperatingCashEditChequeTemplateRequest: TypeAlias = OperatingCashChequeTemplateEdit
OperatingCashEditChequeTemplateResponse: TypeAlias = UpdateResult
OperatingCashEditRequest: TypeAlias = OperatingCashEdit
OperatingCashEditResponse: TypeAlias = UpdateResult
OperatingCashEditSettingsRequest: TypeAlias = list[OperatingCash_SettingEdit]
OperatingCashEditSettingsResponse: TypeAlias = UpdateResult
OperatingCashGetChequeTemplateRequest: TypeAlias = OperatingCashChequeTemplateGet
OperatingCashGetChequeTemplateResponse: TypeAlias = OperatingCashChequeTemplateRegosOffsettedArrayResult
OperatingCashGetImageRequest: TypeAlias = OperatingCashImageGet
OperatingCashGetImageResponse: TypeAlias = OperatingCashImageRegosArrayResult
OperatingCashGetRequest: TypeAlias = OperatingCashGet
OperatingCashGetResponse: TypeAlias = OperatingCashRegosOffsettedArrayResult
OperatingCashGetSettingsRequest: TypeAlias = OperatingCash_SettingGet
OperatingCashGetSettingsResponse: TypeAlias = OperatingCash_SettingArrayRegosObjectResult


_MODEL_NAMES = ['OperatingCash', 'OperatingCashAccept', 'OperatingCashAdd', 'OperatingCashChequeTemplate', 'OperatingCashChequeTemplateEdit', 'OperatingCashChequeTemplateGet', 'OperatingCashChequeTemplateRegosOffsettedArrayResult', 'OperatingCashDelete', 'OperatingCashDiscard', 'OperatingCashEdit', 'OperatingCashGet', 'OperatingCashImage', 'OperatingCashImageDelete', 'OperatingCashImageGet', 'OperatingCashImageRegosArrayResult', 'OperatingCashRegosOffsettedArrayResult', 'OperatingCash_Setting', 'OperatingCash_SettingArrayRegosObjectResult', 'OperatingCash_SettingEdit', 'OperatingCash_SettingGet', 'OperatingCash_SortOrder']


__all__ = [
    'OperatingCash',
    'OperatingCashAccept',
    'OperatingCashAdd',
    'OperatingCashChequeTemplate',
    'OperatingCashChequeTemplateEdit',
    'OperatingCashChequeTemplateGet',
    'OperatingCashChequeTemplateRegosOffsettedArrayResult',
    'OperatingCashDelete',
    'OperatingCashDiscard',
    'OperatingCashEdit',
    'OperatingCashGet',
    'OperatingCashImage',
    'OperatingCashImageDelete',
    'OperatingCashImageGet',
    'OperatingCashImageRegosArrayResult',
    'OperatingCashRegosOffsettedArrayResult',
    'OperatingCash_Setting',
    'OperatingCash_SettingArrayRegosObjectResult',
    'OperatingCash_SettingEdit',
    'OperatingCash_SettingGet',
    'OperatingCash_SortOrder',
    'OperatingCash_SortOrderColumn',
    'OperatingCashGetRequest',
    'OperatingCashGetResponse',
    'OperatingCashAddRequest',
    'OperatingCashAddResponse',
    'OperatingCashEditRequest',
    'OperatingCashEditResponse',
    'OperatingCashDeleteRequest',
    'OperatingCashDeleteResponse',
    'OperatingCashAcceptRequest',
    'OperatingCashAcceptResponse',
    'OperatingCashDiscardRequest',
    'OperatingCashDiscardResponse',
    'OperatingCashGetSettingsRequest',
    'OperatingCashGetSettingsResponse',
    'OperatingCashEditSettingsRequest',
    'OperatingCashEditSettingsResponse',
    'OperatingCashGetChequeTemplateRequest',
    'OperatingCashGetChequeTemplateResponse',
    'OperatingCashEditChequeTemplateRequest',
    'OperatingCashEditChequeTemplateResponse',
    'OperatingCashGetImageRequest',
    'OperatingCashGetImageResponse',
    'OperatingCashAddImageResponse',
    'OperatingCashDeleteImageRequest',
    'OperatingCashDeleteImageResponse'
]
