"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocAdditionalExpensesOperation(RegosModel):
    "Модель, описывающая операцию дополнительных расходов"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции")
    document_id: int | None = PydField(default=None, description="ID документа дополнительных расходов")
    item: Item | None = PydField(default=None, description="Номенклатура")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    order: int | None = PydField(default=None, description="Порядок операции")
    cost: _Decimal | None = PydField(default=None, description="Стоимость номенклатуры")
    price: _Decimal | None = PydField(default=None, description="Цена номенклатуры")
    vat_value: _Decimal | None = PydField(default=None, description="Значение ставки НДС")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    last_update: int | None = PydField(default=None, description="Время последнего изменения записи в формате unix time")


class DocAdditionalExpensesOperationAdd(RegosModel):
    "Модель для добавления операции документа доп арсходов"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None, description="ID документ")
    item_id: int | None = PydField(default=None, description="ID нмоенклатуры")
    quantity: _Decimal | None = PydField(default=None, description="Количество")
    order: int | None = PydField(default=None, description="Порядок операции (NULL = не задано, в БД сохраняется как NULL).\nДля версий БД ниже 363 игнорируется.")
    cost: _Decimal | None = PydField(default=None, description="Стоимость")
    price: _Decimal | None = PydField(default=None, description="Цена")
    vat_value: _Decimal | None = PydField(default=None, description="ставка НДС")


class DocAdditionalExpensesOperationEdit(RegosModel):
    "Модель для редактирования операци доп расходов"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    order: int | None = PydField(default=None, description="Порядок операции. Если NULL, значение в БД не меняется.\nДля версий БД ниже 363 игнорируется.")
    cost: _Decimal | None = PydField(default=None)
    vat_value: _Decimal | None = PydField(default=None)
    price: _Decimal | None = PydField(default=None)


class DocAdditionalExpensesOperationGet(RegosModel):
    "модель запроса операций в документе дополнительных расходов"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID операций дополнительных расходов")
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номенклатуры")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов дополнительных расходов")
    search: str | None = PydField(default=None, description="Поиск по наименованию, артикулу, коду и штрихкоду номенклатуры")
    limit: int | None = PydField(default=None, description="Количество возвращаемых элементов выборки")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocAdditionalExpensesOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocAdditionalExpensesOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Base_ID, Error, UpdateResult, VatCalculationTypeEnum
from schemas.api.references.item import Item


DocAdditionalExpensesOperationAddRequest: TypeAlias = list[DocAdditionalExpensesOperationAdd]
DocAdditionalExpensesOperationAddResponse: TypeAlias = UpdateResult
DocAdditionalExpensesOperationDeleteRequest: TypeAlias = list[Base_ID]
DocAdditionalExpensesOperationDeleteResponse: TypeAlias = UpdateResult
DocAdditionalExpensesOperationEditRequest: TypeAlias = list[DocAdditionalExpensesOperationEdit]
DocAdditionalExpensesOperationEditResponse: TypeAlias = UpdateResult
DocAdditionalExpensesOperationGetRequest: TypeAlias = DocAdditionalExpensesOperationGet
DocAdditionalExpensesOperationGetResponse: TypeAlias = DocAdditionalExpensesOperationRegosOffsettedArrayResult


_MODEL_NAMES = ['DocAdditionalExpensesOperation', 'DocAdditionalExpensesOperationAdd', 'DocAdditionalExpensesOperationEdit', 'DocAdditionalExpensesOperationGet', 'DocAdditionalExpensesOperationRegosOffsettedArrayResult']


__all__ = [
    'DocAdditionalExpensesOperation',
    'DocAdditionalExpensesOperationAdd',
    'DocAdditionalExpensesOperationEdit',
    'DocAdditionalExpensesOperationGet',
    'DocAdditionalExpensesOperationRegosOffsettedArrayResult',
    'DocAdditionalExpensesOperationGetRequest',
    'DocAdditionalExpensesOperationGetResponse',
    'DocAdditionalExpensesOperationAddRequest',
    'DocAdditionalExpensesOperationAddResponse',
    'DocAdditionalExpensesOperationEditRequest',
    'DocAdditionalExpensesOperationEditResponse',
    'DocAdditionalExpensesOperationDeleteRequest',
    'DocAdditionalExpensesOperationDeleteResponse'
]
