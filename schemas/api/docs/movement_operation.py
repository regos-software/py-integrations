# schemas/api/docs/Movement_operation.py
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel

from schemas.api.base import APIBaseResponse, ArrayResult, BaseSchema
from schemas.api.references.item import Item
from schemas.api.references.tax import VatCalculationType


# ---------- Core model ----------


class MovementOperation(BaseModel):
    """Модель операции перемещения."""

    id: Optional[int] = None
    document_id: Optional[int] = None
    item: Optional[Item] = None
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    last_purchase_cost: Optional[Decimal] = None
    description: Optional[str] = None
    last_update: Optional[int] = None  # unixtime (sec)


# ---------- Get ----------


class MovementOperationGetRequest(BaseSchema):
    """
    Параметры для /v1/MovementOperation/Get
    """

    ids: Optional[List[int]] = None
    item_ids: Optional[List[int]] = None
    document_ids: Optional[List[int]] = None


# ---------- Add ----------


class MovementOperationAddRequest(BaseSchema):
    """
    Один элемент массива для /v1/MovementOperation/Add
    Все элементы массива должны иметь одинаковый document_id.
    """

    document_id: int
    item_id: int
    quantity: Decimal
    description: Optional[str] = None


# ---------- Edit ----------


class MovementOperationEditItem(BaseSchema):
    """
    Один элемент массива для /v1/MovementOperation/Edit
    """

    id: int
    quantity: Optional[Decimal] = None
    description: Optional[str] = None


# ---------- Delete ----------


class MovementOperationDeleteItem(BaseSchema):
    """
    Один элемент массива для /v1/MovementOperation/Delete
    """

    id: int


class MovementOperationActionResponse(APIBaseResponse):
    result: Optional[ArrayResult] = []
