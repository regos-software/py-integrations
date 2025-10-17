from abc import ABC, abstractmethod
from typing import Any


class IntegrationBase(ABC):
    """
    Абстрактный базовый класс для интеграций с REGOS.
    Определяет обязательные методы, которые должны реализовываться наследниками.
    """

    @abstractmethod
    async def connect(self) -> Any:
        """
        Устанавливает соединение между интеграцией и сервисом REGOS.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> Any:
        """
        Прерывает соединение между интеграцией и сервисом REGOS.
        """
        pass

    @abstractmethod
    async def reconnect(self) -> Any:
        """
        Переподключает интеграцию к сервису REGOS.
        """
        pass

    @abstractmethod
    async def handle_webhook(self, data: dict) -> Any:
        """
        Обрабатывает входящие вебхуки от REGOS.
        :param data: Содержимое webhook-запроса
        """
        pass

    @abstractmethod
    async def update_settings(self, settings: dict) -> Any:
        """
        Обновляет настройки интеграции.
        :param settings: Новые параметры интеграции
        """
        pass

    @abstractmethod
    async def handle_external(self, data: dict) -> Any:
        """
        Обрабатывает входящие запросы от внешних систем (не от REGOS).
        :param data: Полный пакет данных запроса (метод, заголовки, тело, query и т.д.)
        """
        pass
