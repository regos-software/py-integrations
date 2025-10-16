from typing import List
from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSetting,
    ConnectedIntegrationSettingRequest,
    ConnectedIntegrationSettingEditRequest,
    ConnectedIntegrationSettingEditItem,
)

logger = setup_logger("ConnectedIntegrationSettingService")


class ConnectedIntegrationSettingService:
    PATH_GET = "ConnectedIntegrationSetting/Get"
    PATH_EDIT = "ConnectedIntegrationSetting/Edit"

    def __init__(self, api):
        self.api = api

    async def get(
        self, req: ConnectedIntegrationSettingRequest
    ) -> APIBaseResponse[List[ConnectedIntegrationSetting]]:
        """Получить список настроек по ключу интеграции (и, опционально, firm_id)."""
        resp = await self.api.call(
            self.PATH_GET, req, APIBaseResponse[List[ConnectedIntegrationSetting]]
        )
        return resp

    async def edit(
        self, req: ConnectedIntegrationSettingEditRequest
    ) -> APIBaseResponse:
        """
        Массовое редактирование настроек.
        Возвращает True, если запрос выполнен успешно.
        """
        resp = await self.api.call(self.PATH_EDIT, req, APIBaseResponse)
        return resp
