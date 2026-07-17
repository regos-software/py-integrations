"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class TechMapOperation(RegosModel):
    "Модель, описывающая операцию технической карты"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции")
    document_id: int | None = PydField(default=None, description="ID технической карты")
    item: Item | None = PydField(default=None, description="Номенклатура")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    part_cost: _Decimal | None = PydField(default=None, description="Процентная часть в стоимости товара (только для документов технической карты разборки)")
    last_update: int | None = PydField(default=None, description="Время последнего изменения записи в формате unixtime")


class TechMapOperationAdd(RegosModel):
    "модель добавления позиций к оперицям"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None, description="ID документа технической карты")
    data: list[TechMapOperationAddData] | None = PydField(default=None, description="Массив создаваемых операций")


class TechMapOperationAddData(RegosModel):
    "модель позииций относящийся к TechMap_Operation_Add"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    item_id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    part_cost: _Decimal | None = PydField(default=None, description="процентная часть в стоимости товара (только для документов тех карты разбора)")


class TechMapOperationDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)


class TechMapOperationEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    part_cost: _Decimal | None = PydField(default=None, description="процентная часть в стоимости товара (только для документов тех карты разбора)")


class TechMapOperationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID операций технической карты")
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номенклатуры")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов (не более 1 элемента)")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: Item.name, Item.articul, Item.code, Item.barcodes")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class TechMapOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[TechMapOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import DocsOperationsMovement, Error, UpdateResult
from schemas.api.references.item import Item


TechMapOperationAddRequest: TypeAlias = TechMapOperationAdd
TechMapOperationAddResponse: TypeAlias = UpdateResult
TechMapOperationDeleteRequest: TypeAlias = list[TechMapOperationDelete]
TechMapOperationDeleteResponse: TypeAlias = UpdateResult
TechMapOperationEditRequest: TypeAlias = list[TechMapOperationEdit]
TechMapOperationEditResponse: TypeAlias = UpdateResult
TechMapOperationGetRequest: TypeAlias = TechMapOperationGet
TechMapOperationGetResponse: TypeAlias = TechMapOperationRegosOffsettedArrayResult
TechMapOperationMoveOperationsRequest: TypeAlias = DocsOperationsMovement
TechMapOperationMoveOperationsResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['TechMapOperation', 'TechMapOperationAdd', 'TechMapOperationAddData', 'TechMapOperationDelete', 'TechMapOperationEdit', 'TechMapOperationGet', 'TechMapOperationRegosOffsettedArrayResult']


__all__ = [
    'TechMapOperation',
    'TechMapOperationAdd',
    'TechMapOperationAddData',
    'TechMapOperationDelete',
    'TechMapOperationEdit',
    'TechMapOperationGet',
    'TechMapOperationRegosOffsettedArrayResult',
    'TechMapOperationGetRequest',
    'TechMapOperationGetResponse',
    'TechMapOperationAddRequest',
    'TechMapOperationAddResponse',
    'TechMapOperationEditRequest',
    'TechMapOperationEditResponse',
    'TechMapOperationDeleteRequest',
    'TechMapOperationDeleteResponse',
    'TechMapOperationMoveOperationsRequest',
    'TechMapOperationMoveOperationsResponse'
]
