"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Campaign(RegosModel):
    "Модель массовой рассылки"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID рассылки")
    name: str | None = PydField(default=None, description="Название рассылки")
    type: CampaignTypeEnum | None = PydField(default=None, description="Тип рассылки")
    date: int | None = PydField(default=None, description="Дата создания рассылки в формате Unix time в секундах")
    run_date: int | None = PydField(default=None, description="Дата запуска рассылки в формате Unix time в секундах")
    run_immediately: bool | None = PydField(default=None, description="Будет ли рассылка запущена сразу после создания: true - Рассылка будет запушена сразу после создания (параметр run_date\nбудет проигнорирован), false - Рассылка будет запушена в дату, у казанную в параметре run_date")
    message: str | None = PydField(default=None, description="Текст рассылки")
    image_url: str | None = PydField(default=None, description="Изображение для рассылки")
    recipient_count: int | None = PydField(default=None, description="Количество получателей рассылки")
    status: CampaignStatusEnum | None = PydField(default=None, description="Статус рассылки")
    scheduler_uuid: str | None = PydField(default=None, description="UUID в планировщике")
    integration_key: str | None = PydField(default=None, description="Ключ интеграции, через которую выполняется кампания")
    connected_integration_id: str | None = PydField(default=None, description="ID подключённой интеграции (имеет приоритет над integration_key)")
    last_update: int | None = PydField(default=None, description="Дата последнего обновления параметров в формате Unix time в секундах")


class CampaignAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    type: CampaignTypeEnum | None = PydField(default=None, description="Тип рассылки")
    integration_key: str | None = PydField(default=None, description="Устаревшее поле. Ключ интеграции, через которую выполняется кампания. Если передан одновременно с connected_integration_id, используется connected_integration_id")
    connected_integration_id: str | None = PydField(default=None, description="ID подключённой интеграции. Имеет приоритет над integration_key (если переданы оба поля)")
    run_date: int | None = PydField(default=None, description="Дата запуска рассылки в формате Unix time в секундах")
    run_immediately: bool | None = PydField(default=None, description="Будет ли рассылка запущена сразу после создания: true - Рассылка будет запушена сразу после создания (параметр run_date\nбудет проигнорирован), false - Рассылка будет запушена в дату, у казанную в параметре run_date")
    name: str | None = PydField(default=None, description="Название рассылки")
    message: str | None = PydField(default=None, description="Текст сообщения рассылки")
    file: str | None = PydField(default=None, description="Файл изображения, закодированный в Base64")
    recepients: list[CampaignRecepient] | None = PydField(default=None, description="Массив получателей. Если не передан или пустой, используется RetailCustomer без фильтров (поведение по умолчанию)")


class CampaignColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: CampaignColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class CampaignColumns(str, Enum):
    Default = "Default"
    Id = "Id"
    Name = "Name"
    Type = "Type"
    Date = "Date"
    RunDate = "RunDate"
    RunImmediately = "RunImmediately"
    Message = "Message"
    Image_url = "Image_url"
    RecipientCount = "RecipientCount"
    State = "State"
    LastUpdate = "LastUpdate"


class CampaignEdit(RegosModel):
    "Модель изменения кампании"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID рассылки")
    name: str | None = PydField(default=None, description="Название рассылки")
    message: str | None = PydField(default=None, description="Текст сообщения рассылки")
    file: str | None = PydField(default=None, description="Файл изображения, закодированный в Base64")
    run_date: int | None = PydField(default=None, description="Дата запуска рассылки в формате Unix time в секундах")
    run_immediately: bool | None = PydField(default=None, description="Будет ли рассылка запущена сразу после создания: true - Рассылка будет запушена сразу после создания (параметр run_date\nбудет проигнорирован), false - Рассылка будет запушена в дату, у казанную в параметре run_date")
    integration_key: str | None = PydField(default=None, description="Устаревшее поле. Ключ интеграции, через которую выполняется кампания. Если передан одновременно с connected_integration_id, используется connected_integration_id")
    connected_integration_id: str | None = PydField(default=None, description="ID подключённой интеграции. Имеет приоритет над integration_key (если переданы оба поля)")


class CampaignGet(RegosModel):
    "Модель для получения компавний"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID рассылок")
    status: CampaignStatusEnum | None = PydField(default=None, description="Статус рассылки: <New | 1> - Рассылка создана, но ещё не запущена, <Waiting | 2> - Рассылка ожидает времени\nрасслки, <Progress | 3> - Рассылка начата, но не завершена, <Completed | 4> - Рассылка завершена, <Error\n| 5> - Рассылка завершилась с ошибкой")
    type: CampaignTypeEnum | None = PydField(default=None, description="Тип рассылки: <SMS | 1> - Рассылка по SMS, <Telegram | 2> - Рассылка в Telegram")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: name - Название рассылки")
    sort_orders: list[CampaignColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    limit: int | None = PydField(default=None, description="Количество возвращаемых элементов выборки")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class CampaignRecepient(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    entity_type: CampaignRecipientEntityTypeEnum | None = PydField(default=None, description="тип сущности получателей")
    filters: list[Filter] | None = PydField(default=None, description="фильтры по сущности получателей")


class CampaignRecipient(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None)
    campaign_id: int | None = PydField(default=None, description="связь с Campaign")
    recipient: str | None = PydField(default=None, description="номер телефона или telegram user id")
    state: CampaignRecipientState | None = PydField(default=None, description="Статус")
    last_update: int | None = PydField(default=None)


class CampaignRecipientEntityTypeEnum(str, Enum):
    "Модель добавления компании"
    Default = "Default"
    RetailCustomer = "RetailCustomer"
    Partner = "Partner"
    CrmClient = "CrmClient"


class CampaignRecipientRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[CampaignRecipient] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class CampaignRecipientSetStatus(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID рассылки")
    state: CampaignRecipientState | None = PydField(default=None, description="Статус отправки: <New | 0> - Только добавлен в список, еще не отправлено, <Sended | 1> - Сообщение\nотправлено (например, ушло в SMS шлюз или в Telegram API), <Delivered | 2> - Подтверждена доставка (если есть\nобратная связь от канала), <Error | 3> - Ошибка при отправке сообщения")


class CampaignRecipientState(str, Enum):
    New = "New"
    Sended = "Sended"
    Delivered = "Delivered"
    Error = "Error"


class CampaignRecipientsGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    campaign_id: int | None = PydField(default=None, description="ID рассылки")
    state: CampaignRecipientState | None = PydField(default=None, description="Статус получателя (New, Sended, Delivered, Error)")
    limit: int | None = PydField(default=None, description="Количество возвращаемых элементов выборки")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class CampaignRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Campaign] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class CampaignSetStatus(RegosModel):
    "Установить статус кампании"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID рассылки")
    status: CampaignStatusEnum | None = PydField(default=None, description="Статус рассылки: <New | 1> - Рассылка создана, но ещё не запущена, <Waiting | 2> - Рассылка ожидает времени\nрасслки, <Progress | 3> - Рассылка начата, но не завершена, <Completed | 4> - Рассылка завершена, <Error\n| 5> - Рассылка завершилась с ошибкой")
    error_message: str | None = PydField(default=None, description="Сообщение об ошибке")


class CampaignStatusEnum(str, Enum):
    "Статусы компании"
    Default = "Default"
    New = "New"
    Waiting = "Waiting"
    Progress = "Progress"
    Completed = "Completed"
    Error = "Error"


class CampaignTypeEnum(str, Enum):
    "Типы компаний"
    Default = "Default"
    SMS = "SMS"
    Telegram = "Telegram"
    Email = "Email"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Base_ID, ColumnSortOrderDirection, Error, InsertResult, SingleObjectResult, UpdateResult
from schemas.api.common.filter import Filter


CampaignAddRequest: TypeAlias = CampaignAdd
CampaignAddResponse: TypeAlias = InsertResult
CampaignDeleteRequest: TypeAlias = Base_ID
CampaignDeleteResponse: TypeAlias = UpdateResult
CampaignEditRequest: TypeAlias = CampaignEdit
CampaignEditResponse: TypeAlias = UpdateResult
CampaignGetRecipientsRequest: TypeAlias = CampaignRecipientsGet
CampaignGetRecipientsResponse: TypeAlias = CampaignRecipientRegosOffsettedArrayResult
CampaignGetRequest: TypeAlias = CampaignGet
CampaignGetResponse: TypeAlias = CampaignRegosOffsettedArrayResult
CampaignSetRecipientsStatusRequest: TypeAlias = list[CampaignRecipientSetStatus]
CampaignSetRecipientsStatusResponse: TypeAlias = SingleObjectResult
CampaignSetStatusRequest: TypeAlias = CampaignSetStatus
CampaignSetStatusResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['Campaign', 'CampaignAdd', 'CampaignColumn', 'CampaignEdit', 'CampaignGet', 'CampaignRecepient', 'CampaignRecipient', 'CampaignRecipientRegosOffsettedArrayResult', 'CampaignRecipientSetStatus', 'CampaignRecipientsGet', 'CampaignRegosOffsettedArrayResult', 'CampaignSetStatus']


__all__ = [
    'Campaign',
    'CampaignAdd',
    'CampaignColumn',
    'CampaignColumns',
    'CampaignEdit',
    'CampaignGet',
    'CampaignRecepient',
    'CampaignRecipient',
    'CampaignRecipientEntityTypeEnum',
    'CampaignRecipientRegosOffsettedArrayResult',
    'CampaignRecipientSetStatus',
    'CampaignRecipientState',
    'CampaignRecipientsGet',
    'CampaignRegosOffsettedArrayResult',
    'CampaignSetStatus',
    'CampaignStatusEnum',
    'CampaignTypeEnum',
    'CampaignGetRequest',
    'CampaignGetResponse',
    'CampaignAddRequest',
    'CampaignAddResponse',
    'CampaignEditRequest',
    'CampaignEditResponse',
    'CampaignDeleteRequest',
    'CampaignDeleteResponse',
    'CampaignSetStatusRequest',
    'CampaignSetStatusResponse',
    'CampaignGetRecipientsRequest',
    'CampaignGetRecipientsResponse',
    'CampaignSetRecipientsStatusRequest',
    'CampaignSetRecipientsStatusResponse'
]
