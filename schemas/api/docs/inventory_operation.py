"""Схемы операций документа инвентаризации."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field as PydField

from schemas.api.base import APIBaseResponse, BaseSchema
from schemas.api.references.item import Item


class InventoryOperation(BaseModel):
    """Модель операции инвентаризации."""

    id: Optional[int] = None
    document_id: Optional[int] = None
    datetime: Optional[int] = None
    item: Optional[Item] = None
    actual_quantity: Optional[Decimal] = None
    registered_quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    last_purchase_cost: Optional[Decimal] = None
    last_update: Optional[int] = None


class InventoryOperationGetRequest(BaseSchema):
    """Фильтры получения операций инвентаризации."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(
        default=None, description="Список ID операций инвентаризации."
    )
    document_ids: Optional[List[int]] = PydField(
        default=None, description="Список ID документов инвентаризации."
    )
    search: Optional[str] = PydField(
        default=None,
        description=(
            "Поиск по наименованию, артикулу или коду номенклатуры документа."
        ),
    )
    only_deviation: Optional[bool] = PydField(
        default=None, description="Показывать только операции с отклонениями."
    )
    limit: Optional[int] = PydField(
        default=None, ge=1, description="Количество записей в выдаче."
    )
    offset: Optional[int] = PydField(
        default=None, ge=0, description="Смещение для пагинации."
    )


class InventoryOperationAddRequest(BaseSchema):
    """Параметры создания операции инвентаризации."""

    model_config = ConfigDict(extra="forbid")

    document_id: int = PydField(..., ge=1, description="ID документа инвентаризации.")
    item_id: int = PydField(..., ge=1, description="ID номенклатуры.")
    actual_quantity: Decimal = PydField(
        ..., description="Актуальное количество номенклатуры."
    )
    datetime: Optional[int] = PydField(
        default=None,
        ge=0,
        description="Дата, на которую берутся данные по количеству (Unix).",
    )
    update_actual_quantity: bool = PydField(
        default=True,
        description="Обновлять фактическое количество, а не суммировать.",
    )


class InventoryOperationEditItem(BaseSchema):
    """Параметры изменения операции инвентаризации."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="ID операции инвентаризации.")
    actual_quantity: Optional[Decimal] = PydField(
        default=None, description="Новое фактическое количество."
    )
    update_actual_quantity: bool = PydField(
        default=True,
        description="Всегда обновлять фактическое количество.",
    )
    price: Optional[Decimal] = PydField(
        default=None, description="Новая цена номенклатуры."
    )


class InventoryOperationDeleteItem(BaseSchema):
    """Параметры удаления операции инвентаризации."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="ID операции для удаления.")


class InventoryOperationMutationResult(BaseSchema):
    """Результат модификации операций инвентаризации."""

    model_config = ConfigDict(extra="ignore")

    row_affected: Optional[int] = PydField(
        default=None,
        ge=0,
        alias="row_affected",
        description="Количество обработанных операций.",
    )
    raw_affected: Optional[int] = PydField(
        default=None,
        ge=0,
        alias="raw_affected",
        description="Количество обработанных операций (опечатка API).",
    )

    @property
    def affected(self) -> int:
        return self.row_affected or self.raw_affected or 0


class InventoryOperationGetResponse(APIBaseResponse[List[InventoryOperation]]):
    """Ответ на запрос /v1/InventoryOperation/Get."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "InventoryOperation",
    "InventoryOperationAddRequest",
    "InventoryOperationDeleteItem",
    "InventoryOperationEditItem",
    "InventoryOperationGetRequest",
    "InventoryOperationGetResponse",
    "InventoryOperationMutationResult",
]
