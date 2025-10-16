from __future__ import annotations
from typing import List, Optional

from pydantic import BaseModel

from schemas.api.common.sort_orders import SortOrders


class Brand(BaseModel):
    id: int
    name: Optional[str] = None
    last_update: int


class BrandGetRequest(BaseModel):
    ids: Optional[List[int]] = None
    sort_orders: Optional[SortOrders] = None
    search: Optional[str] = None
    limit: Optional[int]
    offset: Optional[int]


class BrandAddRequest(BaseModel):
    name: str


class BrandEditRequest(BaseModel):
    id: int
    name: str


class BrandDeleteRequest(BaseModel):
    id: int
