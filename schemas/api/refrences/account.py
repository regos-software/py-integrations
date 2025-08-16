from __future__ import annotations

from pydantic import BaseModel
from schemas.api.refrences.currency import Currency


class Account(BaseModel):
    id: int
    code: str
    name: str
    currency: Currency
    last_update: int
