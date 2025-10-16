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
    ) -> List[ConnectedIntegrationSetting]:
        """Получить список настроек по ключу интеграции (и, опционально, firm_id)."""
        resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            logger.warning(f"Не удалось получить настройки: {resp}")
            return []
        return [ConnectedIntegrationSetting.model_validate(x) for x in resp.result]

    async def edit(self, items: List[ConnectedIntegrationSettingEditItem]) -> bool:
        """
        Массовое редактирование настроек.
        Возвращает True, если запрос выполнен успешно.
        """
        req = ConnectedIntegrationSettingEditRequest(items)
        resp = await self.api.call(self.PATH_EDIT, req, APIBaseResponse)
        if getattr(resp, "ok", False):
            logger.info(f"Настройки обновлены: {items}")
            return True
        logger.error(f"Ошибка обновления настроек: {resp}")
        return False
