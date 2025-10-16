from __future__ import annotations
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

from schemas.api.base import APIBaseResponse

from .firm import Firm


class SortColumn(str, Enum):
    ID = "Id"
    NAME = "Name"
    LAST_UPDATE = "LastUpdate"


class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SortOrder(BaseModel):
    column: SortColumn
    direction: SortDirection


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


class StockGetRequest(BaseModel):
    """
    Модель запроса для получения списка складов.
    """

    ids: Optional[List[int]] = []  # Массив ID складов
    firm_ids: Optional[List[int]] = []  # Массив ID предприятий
    sort_orders: Optional[List[SortOrder]] = []  # Сортировка выходных данных
    search: Optional[str] = ""  # Строка поиска по полю name
    deleted_mark: Optional[bool] = False  # Метка об удалении
    limit: Optional[int] = (
        10000  # Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000
    )
    offset: Optional[int] = 0  # Смещение для пагинации


class StockGetResponse(APIBaseResponse):
    """
    Модель ответа при получении списка складов.
    """

    result: List[Stock] = []  # Массив складов
    next_offset: Optional[int] = None  # Смещение для следующего запроса (если есть)
    total: int = (
        0  # Общее количество складов, подходящих под условия запроса (без учёта limit и offset)
    )
