"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class OrderToMovementOperation(RegosModel):
    "Модель, описывающая операции заказа на перемещение"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции")
    document_id: int | None = PydField(default=None, description="ID документа заказа на перемещение")
    item: Item | None = PydField(default=None, description="Номенклатура")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    description: str | None = PydField(default=None, description="Примечание")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time")


class OrderToMovementOperationAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None)
    item_id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    description: str | None = PydField(default=None, description="примечание")


class OrderToMovementOperationDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)


class OrderToMovementOperationEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    description: str | None = PydField(default=None, description="примечание")


class OrderToMovementOperationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID операций заказа на перемещение")
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номенклатуры")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов (не более 1 элемента)")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: Item.name, Item.articul, Item.code, Item.barcodes")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class OrderToMovementOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[OrderToMovementOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import DocsOperationsMovement, Error, UpdateResult
from schemas.api.references.item import Item


OrderToMovementOperationAddRequest: TypeAlias = list[OrderToMovementOperationAdd]
OrderToMovementOperationAddResponse: TypeAlias = UpdateResult
OrderToMovementOperationDeleteRequest: TypeAlias = list[OrderToMovementOperationDelete]
OrderToMovementOperationDeleteResponse: TypeAlias = UpdateResult
OrderToMovementOperationEditRequest: TypeAlias = list[OrderToMovementOperationEdit]
OrderToMovementOperationEditResponse: TypeAlias = UpdateResult
OrderToMovementOperationGetRequest: TypeAlias = OrderToMovementOperationGet
OrderToMovementOperationGetResponse: TypeAlias = OrderToMovementOperationRegosOffsettedArrayResult
OrderToMovementOperationMoveOperationsRequest: TypeAlias = DocsOperationsMovement
OrderToMovementOperationMoveOperationsResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['OrderToMovementOperation', 'OrderToMovementOperationAdd', 'OrderToMovementOperationDelete', 'OrderToMovementOperationEdit', 'OrderToMovementOperationGet', 'OrderToMovementOperationRegosOffsettedArrayResult']


__all__ = [
    'OrderToMovementOperation',
    'OrderToMovementOperationAdd',
    'OrderToMovementOperationDelete',
    'OrderToMovementOperationEdit',
    'OrderToMovementOperationGet',
    'OrderToMovementOperationRegosOffsettedArrayResult',
    'OrderToMovementOperationGetRequest',
    'OrderToMovementOperationGetResponse',
    'OrderToMovementOperationAddRequest',
    'OrderToMovementOperationAddResponse',
    'OrderToMovementOperationEditRequest',
    'OrderToMovementOperationEditResponse',
    'OrderToMovementOperationDeleteRequest',
    'OrderToMovementOperationDeleteResponse',
    'OrderToMovementOperationMoveOperationsRequest',
    'OrderToMovementOperationMoveOperationsResponse'
]
