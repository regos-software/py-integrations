from __future__ import annotations

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class Currency(BaseModel):
    id: int
    code_num: Optional[int] = None
    code_chr: Optional[str] = None
    name: Optional[str] = None
    exchange_rate: Decimal
    is_base: bool
    deleted: bool
    last_update: int
