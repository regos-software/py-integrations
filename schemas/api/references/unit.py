from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class Unit(BaseModel):
    """
    Модель, описывающая единицы измерения.
    """

    id: int  # ID единицы измерения
    name: Optional[str] = None  # Наименование единицы измерения
    type: Optional[str] = None  # Тип единицы измерения
    description: Optional[str] = None  # Описание единицы измерения
    kkm_code: Optional[int] = None  # ККМ код единицы измерения
    last_update: int  # Дата последнего изменения (unixtime, сек)
