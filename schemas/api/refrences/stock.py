from __future__ import annotations
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

from .firm import Firm


class Stock(BaseModel):
    """
    Модель, описывающая склады.
    """
    id: int  # ID склада
    name: Optional[str] = None  # Наименование склада
    address: Optional[str] = None  # Адрес склада
    firm: Firm  # Предприятие
    area: Decimal  # Площадь
    description: Optional[str] = None  # Примечание
    deleted_mark: bool  # Метка об удалении
    last_update: int  # Дата последнего изменения (unixtime, сек)
