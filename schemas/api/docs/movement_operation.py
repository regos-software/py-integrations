"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class MovementOperation(RegosModel):
    "Модель, описывающая операцию перемещения"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции перемещения")
    document_id: int | None = PydField(default=None, description="ID документа перемещения")
    item: Item | None = PydField(default=None, description="Номенклатура")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    order: int | None = PydField(default=None, description="Порядок операции")
    price: _Decimal | None = PydField(default=None, description="Цена номенклатуры")
    last_purchase_cost: _Decimal | None = PydField(default=None, description="Цена последнего поступления номенклатуры от контрагента")
    description: str | None = PydField(default=None, description="Количество номенклатуры")
    last_update: int | None = PydField(default=None, description="Время последнего изменения записи в формате Unix time")


class MovementOperationAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None)
    item_id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    order: int | None = PydField(default=None, description="Порядок операции (NULL = не задано, в БД сохраняется как NULL).\nДля версий БД ниже 363 игнорируется.")
    description: str | None = PydField(default=None, description="примечание")


class MovementOperationDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)


class MovementOperationEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    order: int | None = PydField(default=None, description="Порядок операции. Если NULL, значение в БД не меняется.\nДля версий БД ниже 363 игнорируется.")
    price: _Decimal | None = PydField(default=None, description="стоимость")
    description: str | None = PydField(default=None, description="примечание")


class MovementOperationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID операций перемещения")
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номенклатуры")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов (не более 1 элемента)")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: Item.name, Item.articul, Item.code, Item.barcodes")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class MovementOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[MovementOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import DocsOperationsMovement, Error, SetPriceByPriceType_Model, UpdateResult
from schemas.api.references.item import Item


MovementOperationAddRequest: TypeAlias = list[MovementOperationAdd]
MovementOperationAddResponse: TypeAlias = UpdateResult
MovementOperationDeleteRequest: TypeAlias = list[MovementOperationDelete]
MovementOperationDeleteResponse: TypeAlias = UpdateResult
MovementOperationEditRequest: TypeAlias = list[MovementOperationEdit]
MovementOperationEditResponse: TypeAlias = UpdateResult
MovementOperationGetRequest: TypeAlias = MovementOperationGet
MovementOperationGetResponse: TypeAlias = MovementOperationRegosOffsettedArrayResult
MovementOperationMoveOperationsRequest: TypeAlias = DocsOperationsMovement
MovementOperationMoveOperationsResponse: TypeAlias = UpdateResult
MovementOperationSetPriceByPriceTypeRequest: TypeAlias = SetPriceByPriceType_Model
MovementOperationSetPriceByPriceTypeResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['MovementOperation', 'MovementOperationAdd', 'MovementOperationDelete', 'MovementOperationEdit', 'MovementOperationGet', 'MovementOperationRegosOffsettedArrayResult']


__all__ = [
    'MovementOperation',
    'MovementOperationAdd',
    'MovementOperationDelete',
    'MovementOperationEdit',
    'MovementOperationGet',
    'MovementOperationRegosOffsettedArrayResult',
    'MovementOperationGetRequest',
    'MovementOperationGetResponse',
    'MovementOperationAddRequest',
    'MovementOperationAddResponse',
    'MovementOperationEditRequest',
    'MovementOperationEditResponse',
    'MovementOperationDeleteRequest',
    'MovementOperationDeleteResponse',
    'MovementOperationMoveOperationsRequest',
    'MovementOperationMoveOperationsResponse',
    'MovementOperationSetPriceByPriceTypeRequest',
    'MovementOperationSetPriceByPriceTypeResponse'
]
