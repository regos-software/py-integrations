from typing import List, Optional, Iterable
from enum import Enum
from pydantic import BaseModel

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.refrences.account_balance import AccountBalance

logger = setup_logger("references.account_balance")



class SortColumn(str, Enum):
    ID = "Id"                       # Id счета
    NAME = "Name"                   # Наименование счета
    CODE = "Code"                   # Код счета
    CURRENCY_NAME = "CurrencyName"  # Наименование валюты счета
    LAST_UPDATE = "LastUpdate"      # Дата изменения


class SortDirection(str, Enum):
    ASC = "asc"    # По возрастанию
    DESC = "desc"  # По убыванию


class SortOrder(BaseModel):
    column: SortColumn
    direction: SortDirection



class AccountBalanceGetRequest(BaseModel):
    ids: Optional[List[int]] = None              # массив id счетов
    firm_id: Optional[int] = None                # id предприятия
    currency_ids: Optional[List[int]] = None     # массив id валют
    sort_orders: Optional[List[SortOrder]] = None
    search: Optional[str] = None                 # поиск по name
    limit: Optional[int] = 10000
    offset: Optional[int] = 0



class AccountBalanceService:
    PATH_GET = "AccountBalance/Get"

    def __init__(self, api):
        self.api = api

    async def get(self, req: AccountBalanceGetRequest) -> List[AccountBalance]:
        """
        POST …/v1/AccountBalance/Get
        Возвращает информацию о балансе счёта.
        """
        resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            return []
        return [AccountBalance.model_validate(x) for x in resp.result]

    async def get_by_ids(self, ids: Iterable[int]) -> List[AccountBalance]:
        return await self.get(AccountBalanceGetRequest(ids=list(ids)))
