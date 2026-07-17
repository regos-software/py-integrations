"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class ProductionOperation(RegosModel):
    "Модель, описывающая операцию производства"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции")
    document_id: int | None = PydField(default=None, description="ID документа производства")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    item: Item | None = PydField(default=None, description="Номенклатура")
    doc_tech_map: DocTechMap | None = PydField(default=None, description="Техническая карта, описывающая производство номеклатуры")
    last_update: int | None = PydField(default=None, description="Время последнего изменения записи в формате Unix time")


class ProductionOperationAdd(RegosModel):
    "модель добавления операций производства"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None, description="ID документа производства")
    data: list[ProductionOperationAddData] | None = PydField(default=None, description="Массив создаваемых операций")


class ProductionOperationAddData(RegosModel):
    "модельпозиции операции производства (относиться к Production_Operation_Add)"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    item_id: int | None = PydField(default=None, description="id производимого товара")
    quantity: _Decimal | None = PydField(default=None, description="кол-во")


class ProductionOperationDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID операций производства")


class ProductionOperationEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)


class ProductionOperationGet(RegosModel):
    "модель запроса (фильтры) для получения списка операций производства"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID операций производства")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов (не более 1 элемента)")
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номенклатуры")
    tech_map_ids: list[int] | None = PydField(default=None, description="Массив ID технических карт")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: Item.name, Item.articul, Item.code, Item.barcodes")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class ProductionOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ProductionOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class ProductionOperationReplaceOprTechMap(RegosModel):
    "Модель для замена тех.карты прикреплённое к товару, если текущая непроведённая, и нужен другой проведённый"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="id позиции")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import DocsOperationsMovement, Error, UpdateResult
from schemas.api.docs.doc_tech_map import DocTechMap
from schemas.api.references.item import Item


ProductionOperationAddRequest: TypeAlias = ProductionOperationAdd
ProductionOperationAddResponse: TypeAlias = UpdateResult
ProductionOperationDeleteRequest: TypeAlias = ProductionOperationDelete
ProductionOperationDeleteResponse: TypeAlias = UpdateResult
ProductionOperationEditRequest: TypeAlias = list[ProductionOperationEdit]
ProductionOperationEditResponse: TypeAlias = UpdateResult
ProductionOperationGetRequest: TypeAlias = ProductionOperationGet
ProductionOperationGetResponse: TypeAlias = ProductionOperationRegosOffsettedArrayResult
ProductionOperationMoveOperationsRequest: TypeAlias = DocsOperationsMovement
ProductionOperationMoveOperationsResponse: TypeAlias = UpdateResult
ProductionOperationReplaceOprTechMapRequest: TypeAlias = ProductionOperationReplaceOprTechMap
ProductionOperationReplaceOprTechMapResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['ProductionOperation', 'ProductionOperationAdd', 'ProductionOperationAddData', 'ProductionOperationDelete', 'ProductionOperationEdit', 'ProductionOperationGet', 'ProductionOperationRegosOffsettedArrayResult', 'ProductionOperationReplaceOprTechMap']


__all__ = [
    'ProductionOperation',
    'ProductionOperationAdd',
    'ProductionOperationAddData',
    'ProductionOperationDelete',
    'ProductionOperationEdit',
    'ProductionOperationGet',
    'ProductionOperationRegosOffsettedArrayResult',
    'ProductionOperationReplaceOprTechMap',
    'ProductionOperationGetRequest',
    'ProductionOperationGetResponse',
    'ProductionOperationAddRequest',
    'ProductionOperationAddResponse',
    'ProductionOperationEditRequest',
    'ProductionOperationEditResponse',
    'ProductionOperationReplaceOprTechMapRequest',
    'ProductionOperationReplaceOprTechMapResponse',
    'ProductionOperationDeleteRequest',
    'ProductionOperationDeleteResponse',
    'ProductionOperationMoveOperationsRequest',
    'ProductionOperationMoveOperationsResponse'
]
