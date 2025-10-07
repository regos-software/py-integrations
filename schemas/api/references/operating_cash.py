from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

from .stock import Stock
from .price_type import PriceType
from ..rbac.user import User


class OperatingCash(BaseModel):
    """
    Модель, описывающая кассы розничной торговли.
    """
    id: int  # ID розничной кассы
    stock: Stock  # Склад
    key: str  # Ключ безопасности кассы
    price_type: PriceType  # Вид цены
    description: Optional[str] = None  # Дополнительное описание
    virtual: bool  # Виртуальная касса
    auto_close: bool  # Автоматическое закрытие смены
    max_cheque_quantity_in_session: int  # Макс. количество чеков за смену
    last_update: int  # Дата последнего изменения (unixtime, сек)
    user_accept: User  # Пользователь, который принял кассу в работу
