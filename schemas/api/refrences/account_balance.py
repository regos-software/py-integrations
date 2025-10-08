from __future__ import annotations

from decimal import Decimal
from pydantic import BaseModel
from schemas.api.refrences.currency import Currency


class AccountBalance(BaseModel):
    id: int                     # Id счета
    code: str                   # Код счета
    name: str                   # Наименование счета
    currency: Currency          # Валюта счета
    balance: Decimal            # Баланс счета
    last_update: int            # Дата последнего изменения (Unix time, сек)
