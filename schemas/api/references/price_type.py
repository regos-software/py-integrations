from __future__ import annotations
from decimal import Decimal
from pydantic import BaseModel

from .currency import Currency


class PriceType(BaseModel):
    """
    Модель, описывающая виды цен.
    """
    id: int  # ID вида цены
    name: str  # Наименование вида цены
    round_to: Decimal  # Предел округления
    markup: Decimal  # Наценка для вида цены
    max_discount: Decimal  # Максимальная скидка
    currency: Currency  # Валюта
    currency_additional: Currency  # Дополнительная валюта
    last_update: int  # Последнее изменение (unixtime, сек)
