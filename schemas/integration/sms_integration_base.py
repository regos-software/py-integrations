from abc import ABC, abstractmethod
from typing import Any
from schemas.integration.integration_base import IntegrationBase


class IntegrationSmsBase(IntegrationBase, ABC):
    """
    Абстрактный базовый класс для SMS-интеграций с REGOS.
    Наследуется от IntegrationBase и добавляет метод отправки сообщений.
    """

    @abstractmethod
    async def send_messages(self, messages: list[dict]) -> Any:
        """
        Отправка одного или нескольких сообщений через SMS-интеграцию.

        :param messages: Список сообщений в формате словарей.
        :return: Результат отправки.
        """
        pass
