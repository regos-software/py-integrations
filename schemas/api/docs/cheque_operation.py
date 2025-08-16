from __future__ import annotations
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel

from schemas.api.refrences.item import Item



class DocChequeOperation(BaseModel):
    uuid: str
    has_storno: bool
    storno_uuid: Optional[str] = None
    document: str
    stock_id: int
    item: Optional[Item] = None
    order: int
    quantity: Decimal
    price: Decimal
    price2: Decimal
    promo_id: Optional[int] = None
    vat_value: Decimal
    last_update: int


class DocChequeOperationGetRequest(BaseModel):
    doc_sale_uuid: Optional[str] = None
    uuids: Optional[List[str]] = None
    item_ids: Optional[List[int]] = None
    stock_ids: Optional[List[int]] = None
    firm_ids: Optional[List[int]] = None
    operating_cash_ids: Optional[List[int]] = None
