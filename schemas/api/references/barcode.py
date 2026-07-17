"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Barcode(RegosModel):
    "Модель, описывающая штрих-коды"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID штрих-кода")
    item_id: int | None = PydField(default=None, description="ID номенклатуры")
    barcode_type: BarcodeType | None = PydField(default=None, description="Тип штрих-кода")
    value: str | None = PydField(default=None, description="Штрих-код")
    base: bool | None = PydField(default=None, description="Является ли штрих-код основным: true - Основной, false - Не основной")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате Unix time в секундах")


class BarcodeAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    item_id: int | None = PydField(default=None, description="ID номенклатуры")
    barcode_type_id: int | None = PydField(default=None, description="ID типа штрихкода")
    value: str | None = PydField(default=None, description="Штрих-код")
    forced: bool | None = PydField(default=None, description="<false | null> - штрих-код не добавляется, если он найден среди штрихкодов других позиций номенклатуры. true -\nштрих-код добавляется, если он не является дубликатом для указанной позиции номенклатуры")


class BarcodeAddEAN13(RegosModel):
    "Модель, чтобы добавить новый/сгенерированный штриш-код типа EAN13. генерируется при добавлении"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    item_id: int | None = PydField(default=None, description="ID номенклатуры")


class BarcodeArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Barcode] | Error | None = PydField(default=None, description="Объект результата.")


class BarcodeDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id штрих-кода")


class BarcodeGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID штрих-кодов")
    item_ids: list[int] | None = PydField(default=None, description="Массив id номенклатуры")
    value: str | None = PydField(default=None, description="Значение штрих-кода")


class Barcode_SetBase(RegosModel):
    "модель для установки основного/базового ШК"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID штрих-кода")
    item_id: int | None = PydField(default=None, description="ID номенклатуры")
    value: str | None = PydField(default=None, description="Штрих-код")


class EAN13(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    value: int | None = PydField(default=None)


class EAN13RegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: EAN13 | Error | None = PydField(default=None, description="Объект результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult
from schemas.api.references.barcode_type import BarcodeType


BarcodeAddEan13Request: TypeAlias = BarcodeAddEAN13
BarcodeAddEan13Response: TypeAlias = InsertResult
BarcodeAddRequest: TypeAlias = BarcodeAdd
BarcodeAddResponse: TypeAlias = InsertResult
BarcodeDeleteRequest: TypeAlias = BarcodeDelete
BarcodeDeleteResponse: TypeAlias = UpdateResult
BarcodeFillEmptyBarcodeItemsResponse: TypeAlias = UpdateResult
BarcodeGenerateEan13Response: TypeAlias = EAN13RegosObjectResult
BarcodeGetRequest: TypeAlias = BarcodeGet
BarcodeGetResponse: TypeAlias = BarcodeArrayRegosObjectResult
BarcodeSetBaseRequest: TypeAlias = Barcode_SetBase
BarcodeSetBaseResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['Barcode', 'BarcodeAdd', 'BarcodeAddEAN13', 'BarcodeArrayRegosObjectResult', 'BarcodeDelete', 'BarcodeGet', 'Barcode_SetBase', 'EAN13', 'EAN13RegosObjectResult']


__all__ = [
    'Barcode',
    'BarcodeAdd',
    'BarcodeAddEAN13',
    'BarcodeArrayRegosObjectResult',
    'BarcodeDelete',
    'BarcodeGet',
    'Barcode_SetBase',
    'EAN13',
    'EAN13RegosObjectResult',
    'BarcodeGetRequest',
    'BarcodeGetResponse',
    'BarcodeAddRequest',
    'BarcodeAddResponse',
    'BarcodeAddEan13Request',
    'BarcodeAddEan13Response',
    'BarcodeSetBaseRequest',
    'BarcodeSetBaseResponse',
    'BarcodeDeleteRequest',
    'BarcodeDeleteResponse',
    'BarcodeGenerateEan13Response',
    'BarcodeFillEmptyBarcodeItemsResponse'
]
