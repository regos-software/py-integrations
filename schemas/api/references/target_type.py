"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class TargetType(RegosModel):
    "Модель, описывающая типы целей"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id тип цели")
    name: str | None = PydField(default=None, description="Наименование типа цели")
    name_key: str | None = PydField(default=None, description="Ключ наименования")
    description: str | None = PydField(default=None, description="Примечание")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class TargetTypeRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[TargetType] | Error | None = PydField(default=None, description="Массив результата.")


class TargetTypesEnum(str, Enum):
    "Перечисление типов целей"
    Default = "Default"
    ReceiptCount = "ReceiptCount"
    UnitCount = "UnitCount"
    AverageReceipt = "AverageReceipt"
    SalesAmount = "SalesAmount"
    CrmDealWonAmount = "CrmDealWonAmount"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error


TargetTypeGetResponse: TypeAlias = TargetTypeRegosArrayResult


_MODEL_NAMES = ['TargetType', 'TargetTypeRegosArrayResult']


__all__ = [
    'TargetType',
    'TargetTypeRegosArrayResult',
    'TargetTypesEnum',
    'TargetTypeGetResponse'
]
