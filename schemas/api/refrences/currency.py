from __future__ import annotations

from decimal import Decimal
from pydantic import BaseModel


class Currency(BaseModel):
    id: int
    code_num: int
    code_chr: str
    name: str
    exchange_rate: Decimal
    is_base: bool
    deleted: bool
    last_update: int
