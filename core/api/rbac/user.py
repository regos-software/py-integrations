from __future__ import annotations

from core.logger import setup_logger
from schemas.api.rbac.user import UserGetRequest, UserGetResponse

logger = setup_logger("rbac.User")


class UserService:
    """Сервис RBAC для работы с пользователями."""

    PATH_GET = "User/Get"

    def __init__(self, api):
        self.api = api

    async def get(self, req: UserGetRequest) -> UserGetResponse:
        """Возвращает список пользователей согласно фильтрам."""

        return await self.api.call(self.PATH_GET, req, UserGetResponse)
