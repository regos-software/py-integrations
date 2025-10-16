# schemas/api/docs/purchase_operation.py
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel

from schemas.api.base import APIBaseResponse, ArrayResult, BaseSchema
from schemas.api.references.item import Item
from schemas.api.references.tax import VatCalculationType


# ---------- Core model ----------


class PurchaseOperation(BaseModel):
    id: Optional[int] = None
    document_id: Optional[int] = None
    item: Optional[Item] = None

    quantity: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    vat_value: Optional[Decimal] = None
    vat_calculation_type: Optional[VatCalculationType] = None

    price: Optional[Decimal] = None
    current_price: Optional[Decimal] = None
    last_purchase_cost: Optional[Decimal] = None

    description: Optional[str] = None
    additional_expenses_amount: Optional[Decimal] = None

    last_update: Optional[int] = None  # unixtime (sec)


# ---------- Get ----------


class PurchaseOperationGetRequest(BaseSchema):
    """
    Параметры для /v1/PurchaseOperation/Get
    """

    ids: Optional[List[int]] = None
    item_ids: Optional[List[int]] = None
    document_ids: Optional[List[int]] = None


# ---------- Add ----------


class PurchaseOperationAddRequest(BaseSchema):
    """
    Один элемент массива для /v1/PurchaseOperation/Add
    Все элементы массива должны иметь одинаковый document_id.
    """

    document_id: int
    item_id: int
    quantity: Decimal
    cost: Optional[Decimal] = None
    vat_value: Optional[Decimal] = None
    price: Optional[Decimal] = None
    description: Optional[str] = None


# ---------- Edit ----------


class PurchaseOperationEditItem(BaseSchema):
    """
    Один элемент массива для /v1/PurchaseOperation/Edit
    """

    id: int
    quantity: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    vat_value: Optional[Decimal] = None
    price: Optional[Decimal] = None
    additional_expenses_amount: Optional[Decimal] = None
    description: Optional[str] = None


# ---------- Delete ----------


class PurchaseOperationDeleteItem(BaseSchema):
    """
    Один элемент массива для /v1/PurchaseOperation/Delete
    """

    id: int


class PurchaseOperationActionResponse(APIBaseResponse):
    result: Optional[ArrayResult] = []
