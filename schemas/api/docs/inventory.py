"""Compatibility aliases for generated DocInventory schemas."""

from __future__ import annotations

from enum import Enum

from schemas.api.common.base import Insert
from schemas.api.docs.doc_inventory import (
    DocInventory,
    DocInventoryAddRequest,
    DocInventoryColumn,
    DocInventoryCompareType,
    DocInventoryEditRequest,
    DocInventoryGetRequest,
    DocInventoryGetResponse,
)


class InventoryCompareType(str, Enum):
    OPEN_DATE = "open_date"
    CLOSE_DATE = "close_date"
    OPERATION_DATE = "operation_date"


DocInventoryAddResult = Insert
DocInventorySortOrder = DocInventoryColumn


__all__ = [
    "DocInventory",
    "DocInventoryAddRequest",
    "DocInventoryAddResult",
    "DocInventoryEditRequest",
    "DocInventoryGetRequest",
    "DocInventoryGetResponse",
    "DocInventorySortOrder",
    "InventoryCompareType",
]
