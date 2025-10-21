from __future__ import annotations
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

from .currency import Currency


class PriceType(BaseModel):
    """
    Модель, описывающая виды цен.
    """

    id: int  # ID вида цены
    name: Optional[str] = None  # Наименование вида цены
    round_to: Optional[Decimal] = None  # Предел округления
    markup: Optional[Decimal] = None  # Наценка для вида цены
    max_discount: Optional[Decimal] = None  # Максимальная скидка
    currency: Optional[Currency] = None  # Валюта
    currency_additional: Optional[Currency] = None  # Дополнительная валюта
    last_update: int  # Последнее изменение (unixtime, сек)
