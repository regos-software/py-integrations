"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Chat(RegosModel):
    "Модель, описывающая чат"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: str | None = PydField(default=None, description="UUID чата")
    chat_type: ChatTypeEnum | None = PydField(default=None, description="Тип чата (`Group` или `Individual`)")
    name: str | None = PydField(default=None, description="Наименование чата")
    logo_url: str | None = PydField(default=None, description="Ссылка на логотип чата")
    external_id: str | None = PydField(default=None, description="Внешний идентификатор чата")
    last_message_id: str | None = PydField(default=None, description="UUID последнего сообщения")
    last_message_date: int | None = PydField(default=None, description="Дата последнего сообщения (Unix time, сек.)")
    last_message_text: str | None = PydField(default=None, description="Текст последнего видимого сообщения (для staff-only сообщений подбирается ближайшее доступное)")
    created_user_id: int | None = PydField(default=None, description="ID пользователя, создавшего чат")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи (Unix time, сек.)")
    closed: bool | None = PydField(default=None, description="Признак закрытого чата")
    closed_date: int | None = PydField(default=None, description="Дата закрытия чата (Unix time, сек.)")
    participants: list[ChatParticipant] | None = PydField(default=None, description="Участники чата")
    entity_type: ChatLinkedEntityTypeEnum | None = PydField(default=None, description="Тип связанной бизнес-сущности (Task, Lead, Deal, Ticket)")
    entity_id: int | None = PydField(default=None, description="ID связанной бизнес-сущности")
    unread_count: int | None = PydField(default=None, description="Количество непрочитанных сообщений текущего пользователя")
    muted: bool | None = PydField(default=None, description="Признак отключенных уведомлений по чату для текущего пользователя")
    archived: bool | None = PydField(default=None, description="Признак архивации чата текущим пользователем")
    pinned: bool | None = PydField(default=None, description="Признак закрепления чата текущим пользователем")


class ChatAdd(RegosModel):
    "Модель создания чата."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Название чата")
    logo_url: str | None = PydField(default=None, description="URL логотипа чата")
    external_id: str | None = PydField(default=None, description="Внешний идентификатор чата. Для `Individual` игнорируется")
    chat_type: ChatTypeEnum | None = PydField(default=None, description="Тип создаваемого чата (`Group` или `Individual`). Если не передан, создается `Group`")
    participants: list[ChatParticipantAddEdit] | None = PydField(default=None, description="Список участников для первоначального состава чата. Если не передан, создатель чата добавляется автоматически")


class ChatAddBot(RegosModel):
    "Модель добавления чат-бота в чат."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    chat_id: str | None = PydField(default=None, description="UUID чата")
    connected_integration_id: str | None = PydField(default=None, description="ID подключенной интеграции")


class ChatAddParticipant(RegosModel):
    "Модель добавления одного участника в чат."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    chat_id: str | None = PydField(default=None, description="UUID чата")
    participant: ChatParticipantAddEdit | None = PydField(default=None, description="Участник для добавления")


class ChatAvailableReaction(RegosModel):
    "Доступная реакция чата."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    reaction: str | None = PydField(default=None, description="Код реакции.")
    sort_order: int | None = PydField(default=None, description="Порядок отображения.")


class ChatAvailableReactionRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ChatAvailableReaction] | Error | None = PydField(default=None, description="Массив результата.")


class ChatEdit(RegosModel):
    "Модель редактирования чата."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str | None = PydField(default=None, description="UUID чата")
    name: str | None = PydField(default=None, description="Новое название чата")
    logo_url: str | None = PydField(default=None, description="Новый URL логотипа чата")
    external_id: str | None = PydField(default=None, description="Новый внешний идентификатор чата")


class ChatEntityTypeEnum(str, Enum):
    "Тип сущности, которая участвует в чате."
    Default = "Default"
    User = "User"
    ChatBot = "ChatBot"
    Client = "Client"


class ChatGet(RegosModel):
    "Модель фильтров для получения списка чатов."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[str] | None = PydField(default=None, description="Массив UUID чатов")
    external_id: str | None = PydField(default=None, description="Внешний идентификатор чата для точной фильтрации")
    chat_type: ChatTypeEnum | None = PydField(default=None, description="Тип чата (`Group` или `Individual`)")
    participant_entity_type: ChatEntityTypeEnum | None = PydField(default=None, description="Тип участника для фильтра (User, Client, ChatBot)")
    participant_entity_id: int | None = PydField(default=None, description="ID участника для фильтра")
    search: str | None = PydField(default=None, description="Поиск по названию чата")
    closed: bool | None = PydField(default=None, description="Фильтр по признаку закрытия чата")
    archived: bool | None = PydField(default=None, description="Фильтр по признаку архивации чата текущим пользователем")
    pinned: bool | None = PydField(default=None, description="Фильтр по признаку закрепления чата текущим пользователем")
    entity_type: ChatLinkedEntityTypeEnum | None = PydField(default=None, description="Тип связанной бизнес-сущности чата (Task, Lead, Deal, Ticket)")
    entity_bound: bool | None = PydField(default=None, description="Фильтр по признаку связи чата с бизнес-сущностью")
    sort_orders: list[ChatOrder] | None = PydField(default=None, description="Массив сортировок { column, direction }. Если не передана, сортировка не применяется")
    limit: int | None = PydField(default=None, description="Лимит элементов выборки")
    offset: int | None = PydField(default=None, description="Смещение выборки")


class ChatGetAvailableReactions(RegosModel):
    "Модель получения доступных реакций чата."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    chat_id: str | None = PydField(default=None, description="UUID чата")


class ChatJoin(RegosModel):
    "Модель вступления текущего пользователя в канал."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str | None = PydField(default=None, description="UUID канала")


class ChatLeave(RegosModel):
    "Модель выхода текущего пользователя из обычного группового чата."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str | None = PydField(default=None, description="UUID чата")


class ChatLinkedEntityTypeEnum(str, Enum):
    "Тип бизнес-сущности, к которой привязан чат."
    Default = "Default"
    Task = "Task"
    Lead = "Lead"
    Deal = "Deal"
    Ticket = "Ticket"


class ChatOrder(RegosModel):
    "Модель одной сортировки списка чатов."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: ChatOrderColumn | None = PydField(default=None, description="Колонка сортировки.")
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="Направление сортировки.")


class ChatOrderColumn(str, Enum):
    "Колонка сортировки для получения списка чатов."
    default = "default"
    name = "name"
    last_message_date = "last_message_date"
    last_update = "last_update"
    created_user_id = "created_user_id"
    id = "id"


class ChatParticipant(RegosModel):
    "Модель участника чата."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    entity_type: ChatEntityTypeEnum | None = PydField(default=None, description="Тип сущности участника (пользователь, клиент или чат-бот).")
    entity_id: int | None = PydField(default=None, description="Идентификатор сущности участника.")
    role: ChatParticipantRoleEnum | None = PydField(default=None, description="Роль участника в чате.")
    name: str | None = PydField(default=None, description="Отображаемое имя участника (если доступно).")
    photo_url: str | None = PydField(default=None, description="URL фотографии участника (если доступно).")
    joined_date: int | None = PydField(default=None, description="Дата присоединения к чату в Unix time.")
    last_update: int | None = PydField(default=None, description="Дата последнего обновления записи в Unix time.")


class ChatParticipantAddEdit(RegosModel):
    "Модель связи участника для добавления/изменения состава чата."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    entity_type: ChatEntityTypeEnum | None = PydField(default=None, description="Тип сущности участника.")
    entity_id: int | None = PydField(default=None, description="Идентификатор сущности участника.")
    role: ChatParticipantRoleEnum | None = PydField(default=None, description="Роль участника в чате.")


class ChatParticipantRemove(RegosModel):
    "Модель связи участника для удаления из чата."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    entity_type: ChatEntityTypeEnum | None = PydField(default=None, description="Тип сущности участника.")
    entity_id: int | None = PydField(default=None, description="Идентификатор сущности участника.")


class ChatParticipantRoleEnum(str, Enum):
    "Роль участника внутри чата."
    Default = "Default"
    Staff = "Staff"
    Member = "Member"
    Bot = "Bot"


class ChatRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Chat] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class ChatRemoveParticipants(RegosModel):
    "Модель удаления участников из чата."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str | None = PydField(default=None, description="UUID чата")
    participants: list[ChatParticipantRemove] | None = PydField(default=None, description="Список участников для удаления")


class ChatSetArchived(RegosModel):
    "Модель изменения признака архивации чата."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str | None = PydField(default=None, description="UUID чата")
    archived: bool | None = PydField(default=None, description="true - переместить в архив, false - вернуть из архива")


class ChatSetAvailableReactions(RegosModel):
    "Модель настройки доступных реакций чата."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    chat_id: str | None = PydField(default=None, description="UUID чата")
    reactions: list[str] | None = PydField(default=None, description="Список реакций чата; пустой список сбрасывает настройку к серверной")


class ChatSetMuted(RegosModel):
    "Модель изменения признака отключенных уведомлений по чату."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str | None = PydField(default=None, description="UUID чата")
    muted: bool | None = PydField(default=None, description="true - отключить уведомления, false - включить")


class ChatSetParticipants(RegosModel):
    "Модель полной замены состава участников чата."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str | None = PydField(default=None, description="UUID чата")
    participants: list[ChatParticipantAddEdit] | None = PydField(default=None, description="Список участников для добавления/обновления")


class ChatSetPinned(RegosModel):
    "Модель изменения признака закрепления чата."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str | None = PydField(default=None, description="UUID чата")
    pinned: bool | None = PydField(default=None, description="true - закрепить чат, false - снять закрепление")


class ChatTypeEnum(str, Enum):
    "Тип чата."
    Default = "Default"
    Group = "Group"
    Individual = "Individual"
    Channel = "Channel"


class ChatUnreadCount(RegosModel):
    "Модель агрегированного количества непрочитанных сообщений для бейджа."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    unread_count: int | None = PydField(default=None, description="Общее количество непрочитанных сообщений.")


class ChatUnreadCountByKey(RegosModel):
    "Модель одного агрегированного счетчика непрочитанных сообщений."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    key: str | None = PydField(default=None, description="Ключ счетчика из запроса")
    unread_count: int | None = PydField(default=None, description="Количество непрочитанных сообщений по фильтру")


class ChatUnreadCountByKeyRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ChatUnreadCountByKey] | Error | None = PydField(default=None, description="Массив результата.")


class ChatUnreadCountRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: ChatUnreadCount | Error | None = PydField(default=None, description="Объект результата.")


class ChatUnreadCountsFilter(RegosModel):
    "Модель одного именованного фильтра агрегированного счетчика."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    key: str | None = PydField(default=None, description="Ключ счетчика, который возвращается в ответе без изменения")
    ids: list[str] | None = PydField(default=None, description="Массив UUID чатов")
    external_id: str | None = PydField(default=None, description="Внешний идентификатор чата для точной фильтрации")
    chat_type: ChatTypeEnum | None = PydField(default=None, description="Тип чата (`Group` или `Individual`)")
    participant_entity_type: ChatEntityTypeEnum | None = PydField(default=None, description="Тип участника для фильтра (User, Client, ChatBot)")
    participant_entity_id: int | None = PydField(default=None, description="ID участника для фильтра")
    search: str | None = PydField(default=None, description="Поиск по названию чата")
    closed: bool | None = PydField(default=None, description="Фильтр по признаку закрытия чата")
    archived: bool | None = PydField(default=None, description="Фильтр по признаку архивации чата текущим пользователем")
    pinned: bool | None = PydField(default=None, description="Фильтр по признаку закрепления чата текущим пользователем")
    entity_type: ChatLinkedEntityTypeEnum | None = PydField(default=None, description="Тип связанной бизнес-сущности чата (Task, Lead, Deal, Ticket)")
    entity_bound: bool | None = PydField(default=None, description="Фильтр по признаку связи чата с бизнес-сущностью")


class ChatUnreadCountsGet(RegosModel):
    "Модель запроса агрегированных счетчиков непрочитанных сообщений."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    participant_entity_type: ChatEntityTypeEnum | None = PydField(default=None, description="Общий тип участника для всех фильтров")
    participant_entity_id: int | None = PydField(default=None, description="Общий ID участника для всех фильтров")
    filters: list[ChatUnreadCountsFilter] | None = PydField(default=None, description="Список именованных фильтров для расчета счетчиков")


class ChatUserPresence(RegosModel):
    "Presence пользователя чатов."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    user_id: int | None = PydField(default=None, description="ID пользователя")
    online: bool | None = PydField(default=None, description="Пользователь онлайн")
    last_online_date: int | None = PydField(default=None, description="Unix timestamp последнего online-статуса пользователя")


class ChatUserPresenceGet(RegosModel):
    "Модель запроса presence пользователей чатов."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user_ids: list[int] | None = PydField(default=None, description="ID пользователей, presence которых нужно получить")


class ChatUserPresenceRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ChatUserPresence] | Error | None = PydField(default=None, description="Массив результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, Insert_uuid_Result, UpdateResult


ChatAddBotRequest: TypeAlias = ChatAddBot
ChatAddBotResponse: TypeAlias = UpdateResult
ChatAddParticipantRequest: TypeAlias = ChatAddParticipant
ChatAddParticipantResponse: TypeAlias = UpdateResult
ChatAddRequest: TypeAlias = ChatAdd
ChatAddResponse: TypeAlias = Insert_uuid_Result
ChatEditRequest: TypeAlias = ChatEdit
ChatEditResponse: TypeAlias = UpdateResult
ChatGetAvailableReactionsRequest: TypeAlias = ChatGetAvailableReactions
ChatGetAvailableReactionsResponse: TypeAlias = ChatAvailableReactionRegosArrayResult
ChatGetRequest: TypeAlias = ChatGet
ChatGetResponse: TypeAlias = ChatRegosOffsettedArrayResult
ChatGetUnreadCountResponse: TypeAlias = ChatUnreadCountRegosObjectResult
ChatGetUnreadCountsRequest: TypeAlias = ChatUnreadCountsGet
ChatGetUnreadCountsResponse: TypeAlias = ChatUnreadCountByKeyRegosArrayResult
ChatGetUserPresenceRequest: TypeAlias = ChatUserPresenceGet
ChatGetUserPresenceResponse: TypeAlias = ChatUserPresenceRegosArrayResult
ChatJoinRequest: TypeAlias = ChatJoin
ChatJoinResponse: TypeAlias = UpdateResult
ChatLeaveRequest: TypeAlias = ChatLeave
ChatLeaveResponse: TypeAlias = UpdateResult
ChatRemoveParticipantsRequest: TypeAlias = ChatRemoveParticipants
ChatRemoveParticipantsResponse: TypeAlias = UpdateResult
ChatSetArchivedRequest: TypeAlias = ChatSetArchived
ChatSetArchivedResponse: TypeAlias = UpdateResult
ChatSetAvailableReactionsRequest: TypeAlias = ChatSetAvailableReactions
ChatSetAvailableReactionsResponse: TypeAlias = UpdateResult
ChatSetMutedRequest: TypeAlias = ChatSetMuted
ChatSetMutedResponse: TypeAlias = UpdateResult
ChatSetParticipantsRequest: TypeAlias = ChatSetParticipants
ChatSetParticipantsResponse: TypeAlias = UpdateResult
ChatSetPinnedRequest: TypeAlias = ChatSetPinned
ChatSetPinnedResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['Chat', 'ChatAdd', 'ChatAddBot', 'ChatAddParticipant', 'ChatAvailableReaction', 'ChatAvailableReactionRegosArrayResult', 'ChatEdit', 'ChatGet', 'ChatGetAvailableReactions', 'ChatJoin', 'ChatLeave', 'ChatOrder', 'ChatParticipant', 'ChatParticipantAddEdit', 'ChatParticipantRemove', 'ChatRegosOffsettedArrayResult', 'ChatRemoveParticipants', 'ChatSetArchived', 'ChatSetAvailableReactions', 'ChatSetMuted', 'ChatSetParticipants', 'ChatSetPinned', 'ChatUnreadCount', 'ChatUnreadCountByKey', 'ChatUnreadCountByKeyRegosArrayResult', 'ChatUnreadCountRegosObjectResult', 'ChatUnreadCountsFilter', 'ChatUnreadCountsGet', 'ChatUserPresence', 'ChatUserPresenceGet', 'ChatUserPresenceRegosArrayResult']


__all__ = [
    'Chat',
    'ChatAdd',
    'ChatAddBot',
    'ChatAddParticipant',
    'ChatAvailableReaction',
    'ChatAvailableReactionRegosArrayResult',
    'ChatEdit',
    'ChatEntityTypeEnum',
    'ChatGet',
    'ChatGetAvailableReactions',
    'ChatJoin',
    'ChatLeave',
    'ChatLinkedEntityTypeEnum',
    'ChatOrder',
    'ChatOrderColumn',
    'ChatParticipant',
    'ChatParticipantAddEdit',
    'ChatParticipantRemove',
    'ChatParticipantRoleEnum',
    'ChatRegosOffsettedArrayResult',
    'ChatRemoveParticipants',
    'ChatSetArchived',
    'ChatSetAvailableReactions',
    'ChatSetMuted',
    'ChatSetParticipants',
    'ChatSetPinned',
    'ChatTypeEnum',
    'ChatUnreadCount',
    'ChatUnreadCountByKey',
    'ChatUnreadCountByKeyRegosArrayResult',
    'ChatUnreadCountRegosObjectResult',
    'ChatUnreadCountsFilter',
    'ChatUnreadCountsGet',
    'ChatUserPresence',
    'ChatUserPresenceGet',
    'ChatUserPresenceRegosArrayResult',
    'ChatGetRequest',
    'ChatGetResponse',
    'ChatAddRequest',
    'ChatAddResponse',
    'ChatEditRequest',
    'ChatEditResponse',
    'ChatSetParticipantsRequest',
    'ChatSetParticipantsResponse',
    'ChatRemoveParticipantsRequest',
    'ChatRemoveParticipantsResponse',
    'ChatLeaveRequest',
    'ChatLeaveResponse',
    'ChatJoinRequest',
    'ChatJoinResponse',
    'ChatAddParticipantRequest',
    'ChatAddParticipantResponse',
    'ChatAddBotRequest',
    'ChatAddBotResponse',
    'ChatGetUnreadCountResponse',
    'ChatGetUnreadCountsRequest',
    'ChatGetUnreadCountsResponse',
    'ChatGetUserPresenceRequest',
    'ChatGetUserPresenceResponse',
    'ChatSetMutedRequest',
    'ChatSetMutedResponse',
    'ChatSetArchivedRequest',
    'ChatSetArchivedResponse',
    'ChatSetPinnedRequest',
    'ChatSetPinnedResponse',
    'ChatGetAvailableReactionsRequest',
    'ChatGetAvailableReactionsResponse',
    'ChatSetAvailableReactionsRequest',
    'ChatSetAvailableReactionsResponse'
]
