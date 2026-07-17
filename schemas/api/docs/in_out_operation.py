"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class InOutOperation(RegosModel):
    "Модель, описывающая операцию списания/занесения"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции списания/занесения")
    document_id: int | None = PydField(default=None, description="ID документа списания/занесения")
    item: Item | None = PydField(default=None, description="Номенклатура")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    order: int | None = PydField(default=None, description="Порядок операции")
    description: str | None = PydField(default=None, description="Примечание")
    last_purchase_cost: _Decimal | None = PydField(default=None, description="Стоимость последней закупки")
    last_update: int | None = PydField(default=None, description="Время последнего изменения записи в формате unix time")


class InOutOperationAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None)
    item_id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    order: int | None = PydField(default=None, description="Порядок операции (NULL = не задано, в БД сохраняется как NULL).\nДля версий БД ниже 363 игнорируется.")
    description: str | None = PydField(default=None, description="примечание")


class InOutOperationDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)


class InOutOperationEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    order: int | None = PydField(default=None, description="Порядок операции. Если NULL, значение в БД не меняется.\nДля версий БД ниже 363 игнорируется.")
    description: str | None = PydField(default=None, description="примечание")


class InOutOperationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID операций списания/занесения")
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номенклатуры")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов (не более 1 элемента)")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: Item.name, Item.articul, Item.code, Item.barcodes")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class InOutOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[InOutOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import DocsOperationsCopy, DocsOperationsMovement, Error, UpdateResult
from schemas.api.references.item import Item


InOutOperationAddRequest: TypeAlias = list[InOutOperationAdd]
InOutOperationAddResponse: TypeAlias = UpdateResult
InOutOperationCopyOperationsFromDocInventoryRequest: TypeAlias = DocsOperationsCopy
InOutOperationCopyOperationsFromDocInventoryResponse: TypeAlias = UpdateResult
InOutOperationDeleteRequest: TypeAlias = list[InOutOperationDelete]
InOutOperationDeleteResponse: TypeAlias = UpdateResult
InOutOperationEditRequest: TypeAlias = list[InOutOperationEdit]
InOutOperationEditResponse: TypeAlias = UpdateResult
InOutOperationGetRequest: TypeAlias = InOutOperationGet
InOutOperationGetResponse: TypeAlias = InOutOperationRegosOffsettedArrayResult
InOutOperationMoveOperationsRequest: TypeAlias = DocsOperationsMovement
InOutOperationMoveOperationsResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['InOutOperation', 'InOutOperationAdd', 'InOutOperationDelete', 'InOutOperationEdit', 'InOutOperationGet', 'InOutOperationRegosOffsettedArrayResult']


__all__ = [
    'InOutOperation',
    'InOutOperationAdd',
    'InOutOperationDelete',
    'InOutOperationEdit',
    'InOutOperationGet',
    'InOutOperationRegosOffsettedArrayResult',
    'InOutOperationGetRequest',
    'InOutOperationGetResponse',
    'InOutOperationAddRequest',
    'InOutOperationAddResponse',
    'InOutOperationEditRequest',
    'InOutOperationEditResponse',
    'InOutOperationDeleteRequest',
    'InOutOperationDeleteResponse',
    'InOutOperationMoveOperationsRequest',
    'InOutOperationMoveOperationsResponse',
    'InOutOperationCopyOperationsFromDocInventoryRequest',
    'InOutOperationCopyOperationsFromDocInventoryResponse'
]
