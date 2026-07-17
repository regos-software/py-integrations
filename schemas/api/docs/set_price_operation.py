"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class SetPriceOperation(RegosModel):
    "Модель, описывающая операции установки цен"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции")
    document_id: int | None = PydField(default=None, description="ID документа перемещения")
    item: Item | None = PydField(default=None, description="Номенклатура")
    base_value: _Decimal | None = PydField(default=None, description="Текущая цена (базовая цена)")
    new_value: _Decimal | None = PydField(default=None, description="Новая цена")
    current_value: _Decimal | None = PydField(default=None, description="Текущие значение")
    performed: bool | None = PydField(default=None, description="Метка о проведении операции")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class SetPriceOperationAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None)
    item_id: int | None = PydField(default=None)
    base_value: _Decimal | None = PydField(default=None)
    new_value: _Decimal | None = PydField(default=None)


class SetPriceOperationDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции документа утановки цен")


class SetPriceOperationEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id операции документа установки цен")
    base_value: _Decimal | None = PydField(default=None, description="Текущая цена (базовая цена)")
    new_value: _Decimal | None = PydField(default=None, description="Новая цена")


class SetPriceOperationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID операций установки цен")
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номенклатуры")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов (не более 1 элемента)")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: Item.name, Item.articul, Item.code, Item.barcodes")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class SetPriceOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[SetPriceOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import DocsOperationsCopy, Error, ObjectRegosObjectResult, SetPriceByPriceType_Model, UpdateResult
from schemas.api.references.item import Item


SetPriceOperationAddRequest: TypeAlias = list[SetPriceOperationAdd]
SetPriceOperationAddResponse: TypeAlias = UpdateResult
SetPriceOperationCopyOperationsFromDocPurchaseRequest: TypeAlias = DocsOperationsCopy
SetPriceOperationCopyOperationsFromDocPurchaseResponse: TypeAlias = ObjectRegosObjectResult
SetPriceOperationDeleteRequest: TypeAlias = list[SetPriceOperationDelete]
SetPriceOperationDeleteResponse: TypeAlias = UpdateResult
SetPriceOperationEditRequest: TypeAlias = list[SetPriceOperationEdit]
SetPriceOperationEditResponse: TypeAlias = UpdateResult
SetPriceOperationGetRequest: TypeAlias = SetPriceOperationGet
SetPriceOperationGetResponse: TypeAlias = SetPriceOperationRegosOffsettedArrayResult
SetPriceOperationSetBasePriceByPriceTypeRequest: TypeAlias = SetPriceByPriceType_Model
SetPriceOperationSetBasePriceByPriceTypeResponse: TypeAlias = UpdateResult
SetPriceOperationSetNewPriceByPriceTypeRequest: TypeAlias = SetPriceByPriceType_Model
SetPriceOperationSetNewPriceByPriceTypeResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['SetPriceOperation', 'SetPriceOperationAdd', 'SetPriceOperationDelete', 'SetPriceOperationEdit', 'SetPriceOperationGet', 'SetPriceOperationRegosOffsettedArrayResult']


__all__ = [
    'SetPriceOperation',
    'SetPriceOperationAdd',
    'SetPriceOperationDelete',
    'SetPriceOperationEdit',
    'SetPriceOperationGet',
    'SetPriceOperationRegosOffsettedArrayResult',
    'SetPriceOperationGetRequest',
    'SetPriceOperationGetResponse',
    'SetPriceOperationAddRequest',
    'SetPriceOperationAddResponse',
    'SetPriceOperationEditRequest',
    'SetPriceOperationEditResponse',
    'SetPriceOperationDeleteRequest',
    'SetPriceOperationDeleteResponse',
    'SetPriceOperationCopyOperationsFromDocPurchaseRequest',
    'SetPriceOperationCopyOperationsFromDocPurchaseResponse',
    'SetPriceOperationSetBasePriceByPriceTypeRequest',
    'SetPriceOperationSetBasePriceByPriceTypeResponse',
    'SetPriceOperationSetNewPriceByPriceTypeRequest',
    'SetPriceOperationSetNewPriceByPriceTypeResponse'
]
