from typing import List, Optional, Iterable
from enum import Enum
from decimal import Decimal
from pydantic import BaseModel

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.references.currency import Currency

logger = setup_logger("references.currency")


class SortColumn(str, Enum):
    ID = "Id"                      #Id валюты
    NAME = "Name"                  #Наименование
    CODE_NUM = "CodeNum"           #Цифровой код
    CODE_CHR = "CodeChr"           #Буквенный код
    EXCHANGE_RATE = "ExchangeRate" #Курс
    LAST_UPDATE = "LastUpdate"     #Последнее изменение


class SortDirection(str, Enum):
    ASC = "asc"   #По возрастанию
    DESC = "desc" #По убыванию


class SortOrder(BaseModel):
    column: SortColumn
    direction: SortDirection


class CurrencyGetRequest(BaseModel):
    ids: Optional[List[int]] = None                 #Массив ID валют
    sort_orders: Optional[List[SortOrder]] = None   #Сортировака выходных параметров
    search: Optional[str] = None                    #Строка поиска по: name (наименование), code_chr (Буквенный код)
    limit: Optional[int] = 10000                    
    offset: Optional[int] = 0


class CurrencyAddRequest(BaseModel):
    code_num: int                #Цифровой код валюты
    code_chr: str                #Буквенный код валюты
    name: str                    #Наименование валюты


class CurrencyEditRequest(BaseModel):
    id: int                                       #id валюты
    code_num: Optional[int] = None                #Цифровой код валюты
    code_chr: Optional[str] = None                #Буквенный код валюты
    name: Optional[str] = None                    #Наименование валюты


class CurrencyDeleteRequest(BaseModel):
    id: int


class CurrencyEditExchangeRateRequest(BaseModel):
    id: int
    exchange_rate: Decimal                      #Курс валюты по отношению к основной


class CurrencyService:
    PATH_GET = "Currency/Get"
    PATH_ADD = "Currency/Add"
    PATH_EDIT = "Currency/Edit"
    PATH_DELETE = "Currency/Delete"
    PATH_EDIT_EXCHANGE_RATE = "Currency/EditExchangeRate"

    def __init__(self, api):
        self.api = api

    async def get(self, req: CurrencyGetRequest) -> List[Currency]:
        """
        POST …/v1/Currency/Get
        Возвращает список валют.
        """
        resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            return []
        return [Currency.model_validate(x) for x in resp.result]

    async def get_by_ids(self, ids: Iterable[int]) -> List[Currency]:
        return await self.get(CurrencyGetRequest(ids=list(ids)))

    async def add(self, req: CurrencyAddRequest) -> int | None:
        """
        POST …/v1/Currency/Add
        Создаёт новую валюту.
        """
        resp = await self.api.call(self.PATH_ADD, req, APIBaseResponse)
        if not getattr(resp, "ok", False):
            return None
        return resp.result

    async def edit(self, req: CurrencyEditRequest) -> bool:
        """
        POST …/v1/Currency/Edit
        Редактирует валюту.
        """
        resp = await self.api.call(self.PATH_EDIT, req, APIBaseResponse)
        return getattr(resp, "ok", False)

    async def delete(self, req: CurrencyDeleteRequest) -> bool:
        """
        POST …/v1/Currency/Delete
        Удаляет валюту по id.
        """
        resp = await self.api.call(self.PATH_DELETE, req, APIBaseResponse)
        return getattr(resp, "ok", False)

    async def edit_exchange_rate(self, req: CurrencyEditExchangeRateRequest) -> bool:
        """
        POST …/v1/Currency/EditExchangeRate
        Устанавливает курс валюты по отношению к основной.
        """
        resp = await self.api.call(self.PATH_EDIT_EXCHANGE_RATE, req, APIBaseResponse)
        return getattr(resp, "ok", False)

