from typing import List, Optional, Iterable
from enum import Enum
from pydantic import BaseModel

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.references.account import Account
from schemas.api.references.currency import Currency

logger = setup_logger("references.account")


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



class AccountGetRequest(BaseModel):
    ids: Optional[List[int]] = None               # Массив id счетов
    firm_id: Optional[int] = None                 # id предприятия
    currency_ids: Optional[List[int]] = None      # Массив id валют
    sort_orders: Optional[List[SortOrder]] = None # Сортировка выходных данных
    search: Optional[str] = None                  # Строка поиска по полю name
    limit: Optional[int] = 10000
    offset: Optional[int] = 0


class AccountAddRequest(BaseModel):
    code: str
    name: str
    currency_id: int


class AccountEditRequest(BaseModel):
    id: int
    code: Optional[str] = None
    name: Optional[str] = None
    currency_id: Optional[int] = None


class AccountDeleteRequest(BaseModel):
    id: int



class AccountService:
    PATH_GET = "Account/Get"
    PATH_ADD = "Account/Add"
    PATH_EDIT = "Account/Edit"
    PATH_DELETE = "Account/Delete"

    def __init__(self, api):
        self.api = api

    async def get(self, req: AccountGetRequest) -> List[Account]:
        """
        POST …/v1/Account/Get
        Возвращает список счетов.
        """
        resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            return []
        return [Account.model_validate(x) for x in resp.result]

    async def get_by_ids(self, ids: Iterable[int]) -> List[Account]:
        return await self.get(AccountGetRequest(ids=list(ids)))

    async def add(self, req: AccountAddRequest) -> int | None:
        """
        POST …/v1/Account/Add
        Создаёт новый счёт.
        """
        resp = await self.api.call(self.PATH_ADD, req, APIBaseResponse)
        if not getattr(resp, "ok", False):
            return None
        return resp.result

    async def edit(self, req: AccountEditRequest) -> bool:
        """
        POST …/v1/Account/Edit
        Редактирует счёт.
        """
        resp = await self.api.call(self.PATH_EDIT, req, APIBaseResponse)
        return getattr(resp, "ok", False)

    async def delete(self, req: AccountDeleteRequest) -> bool:
        """
        POST …/v1/Account/Delete
        Удаляет счёт по id.
        """
        resp = await self.api.call(self.PATH_DELETE, req, APIBaseResponse)
        return getattr(resp, "ok", False)
