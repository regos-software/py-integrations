"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class TargetSetting(RegosModel):
    "Модель, описывающая настройки цели"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID настройки")
    target_id: int | None = PydField(default=None, description="ID цели")
    type: TargetSettingTypeEnum | None = PydField(default=None, description="Тип насторойки цели: <Item | 1> - номенклатура, <ItemGroup | 2> - группа номенклатуры, <Pipeline | 3> - CRM воронка, <DealType | 4> - CRM тип сделки")
    value: str | None = PydField(default=None, description="Значение настройки")
    include: bool | None = PydField(default=None, description="Состояние настройки: true - включена, false - выключена")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class TargetSettingAdd(RegosModel):
    "модель добавления цели"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    target_id: int | None = PydField(default=None, description="ID цели")
    type: TargetSettingTypeEnum | None = PydField(default=None, description="Тип настройки цели: <Item | 1> - номенклатура, <ItemGroup | 2> - группа номенклатуры, <Pipeline | 3> - CRM воронка, <DealType | 4> - CRM тип сделки")
    value: str | None = PydField(default=None, description="Значение настройки")
    include: bool | None = PydField(default=None, description="Состояние настройки: true - включена, false - выключена")


class TargetSettingGet(RegosModel):
    "Получение настроек целей"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    target_id: int | None = PydField(default=None, description="ID цели")
    ids: list[int] | None = PydField(default=None, description="Массив ID настроек")
    type: TargetSettingTypeEnum | None = PydField(default=None, description="Тип настройки цели: <Item | 1> - номенклатура, <ItemGroup | 2> - группа номенклатуры, <Pipeline | 3> - CRM воронка, <DealType | 4> - CRM тип сделки")


class TargetSettingRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[TargetSetting] | Error | None = PydField(default=None, description="Массив результата.")


class TargetSettingTypeEnum(str, Enum):
    "Перечисление типов настроек цели"
    Default = "Default"
    Item = "Item"
    ItemGroup = "ItemGroup"
    Pipeline = "Pipeline"
    DealType = "DealType"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Base_ID, Error, InsertResult, UpdateResult


TargetSettingAddRequest: TypeAlias = list[TargetSettingAdd]
TargetSettingAddResponse: TypeAlias = InsertResult
TargetSettingAddSingleRequest: TypeAlias = TargetSettingAdd
TargetSettingAddSingleResponse: TypeAlias = InsertResult
TargetSettingDeleteRequest: TypeAlias = Base_ID
TargetSettingDeleteResponse: TypeAlias = UpdateResult
TargetSettingGetRequest: TypeAlias = TargetSettingGet
TargetSettingGetResponse: TypeAlias = TargetSettingRegosArrayResult


_MODEL_NAMES = ['TargetSetting', 'TargetSettingAdd', 'TargetSettingGet', 'TargetSettingRegosArrayResult']


__all__ = [
    'TargetSetting',
    'TargetSettingAdd',
    'TargetSettingGet',
    'TargetSettingRegosArrayResult',
    'TargetSettingTypeEnum',
    'TargetSettingGetRequest',
    'TargetSettingGetResponse',
    'TargetSettingAddSingleRequest',
    'TargetSettingAddSingleResponse',
    'TargetSettingAddRequest',
    'TargetSettingAddResponse',
    'TargetSettingDeleteRequest',
    'TargetSettingDeleteResponse'
]
