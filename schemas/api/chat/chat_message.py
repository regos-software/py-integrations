"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class ChatMessage(RegosModel):
    "Модель, описывающая сообщение чата"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    reply_id: str | None = PydField(default=None, description="UUID сообщения, на которое отправлен ответ")
    replay_text: str | None = PydField(default=None, description="Текст сообщения, на которое отправлен ответ")
    id: str | None = PydField(default=None, description="UUID сообщения")
    chat_id: str | None = PydField(default=None, description="UUID чата")
    author_entity_type: ChatEntityTypeEnum | None = PydField(default=None, description="Тип автора сообщения")
    author_entity_id: int | None = PydField(default=None, description="ID автора сообщения")
    author_role: ChatParticipantRoleEnum | None = PydField(default=None, description="Роль автора в чате: Staff, Member или Bot (если автор является участником чата)")
    author_entity_name: str | None = PydField(default=None, description="Имя автора сообщения")
    author_entity_photo: str | None = PydField(default=None, description="Фото автора сообщения")
    message_type: ChatMessageTypeEnum | None = PydField(default=None, description="Тип сообщения: Regular, System, Private")
    text: str | None = PydField(default=None, description="Текст сообщения")
    mentions: list[CommonMention] | None = PydField(default=None, description="Структурированные упоминания пользователей в text")
    file_ids: list[int] | None = PydField(default=None, description="Идентификаторы чатовых файлов (CommonFile) в папке текущего чата")
    action_code: str | None = PydField(default=None, description="Код системного действия")
    action_payload: str | None = PydField(default=None, description="Данные системного действия (JSON-строка)")
    actions: list[list[ChatMessageAction]] | None = PydField(default=None, description="Callback-действия сообщения для отрисовки inline-кнопок")
    event_id: str | None = PydField(default=None, description="Идентификатор события идемпотентности")
    external_message_id: str | None = PydField(default=None, description="Внешний ID сообщения")
    edited: bool | None = PydField(default=None, description="Признак, что сообщение редактировалось")
    read: bool | None = PydField(default=None, description="Признак прочтения сообщения текущим пользователем")
    pinned: bool | None = PydField(default=None, description="Признак закрепления сообщения в чате")
    reactions: list[ChatMessageReaction] | None = PydField(default=None, description="Агрегированные реакции сообщения")
    recipient_count: int | None = PydField(default=None, description="Количество получателей сообщения")
    read_count: int | None = PydField(default=None, description="Количество пользователей, прочитавших сообщение")
    created_date: int | None = PydField(default=None, description="Дата создания (Unix time, сек.)")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения (Unix time, сек.)")


class ChatMessageAction(RegosModel):
    "Callback-действие сообщения чата."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str | None = PydField(default=None, description="Уникальный идентификатор действия внутри сообщения")
    text: str | None = PydField(default=None, description="Текст кнопки действия")
    payload: Any = PydField(default=None, description="Непрозрачные данные действия для интеграции/бота")


class ChatMessageAdd(RegosModel):
    "Модель добавления сообщения в чат."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    reply_id: str | None = PydField(default=None, description="UUID сообщения, на которое отправляем ответ")
    replay_text: str | None = PydField(default=None, description="Текст сообщения, на которое отправляем ответ. Если не передан и указан reply_id, значение будет заполнено сервером по исходному сообщению")
    chat_id: str | None = PydField(default=None, description="UUID чата")
    author_entity_type: ChatEntityTypeEnum | None = PydField(default=None, description="Тип автора сообщения")
    author_entity_id: int | None = PydField(default=None, description="ID автора сообщения")
    message_type: ChatMessageTypeEnum | None = PydField(default=None, description="Тип сообщения (Regular, Private, System)")
    text: str | None = PydField(default=None, description="Текст сообщения. Должен быть указан text или file_ids")
    mentions: list[CommonMentionInput] | None = PydField(default=None, description="Структурированные упоминания пользователей в text")
    mention_options: CommonMentionOptions | None = PydField(default=None, description="Опции обработки упоминаний")
    file_ids: list[int] | None = PydField(default=None, description="Массив ID файлов. Должен быть указан text или file_ids")
    actions: list[list[ChatMessageAction]] | None = PydField(default=None, description="Callback-действия сообщения для отрисовки inline-кнопок")
    external_message_id: str | None = PydField(default=None, description="Внешний ID сообщения")


class ChatMessageAddFileResult(RegosModel):
    "Результат загрузки файла для сообщения чата."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    file_id: int | None = PydField(default=None, description="Идентификатор загруженного файла.")


class ChatMessageAddFileResultRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: ChatMessageAddFileResult | Error | None = PydField(default=None, description="Объект результата.")


class ChatMessageCallback(RegosModel):
    "Модель callback-действия сообщения чата."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    message_id: str | None = PydField(default=None, description="UUID сообщения")
    action_id: str | None = PydField(default=None, description="Идентификатор callback-действия внутри сообщения")


class ChatMessageDelete(RegosModel):
    "Модель удаления сообщения чата."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str | None = PydField(default=None, description="UUID сообщения")


class ChatMessageEdit(RegosModel):
    "Модель редактирования сообщения чата."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str | None = PydField(default=None, description="UUID сообщения")
    text: str | None = PydField(default=None, description="Новый текст сообщения")
    mentions: list[CommonMentionInput] | None = PydField(default=None, description="Новый список структурированных упоминаний в text. Если поле text передано, но mentions не передан, сервер очистит старые упоминания")
    mention_options: CommonMentionOptions | None = PydField(default=None, description="Опции обработки упоминаний")
    file_ids: list[int] | None = PydField(default=None, description="Новый список файлов")


class ChatMessageFile(RegosModel):
    "Модель файла сообщения чата с контекстом исходного сообщения."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    message_id: str | None = PydField(default=None, description="UUID сообщения")
    chat_id: str | None = PydField(default=None, description="UUID чата")
    author_entity_type: ChatEntityTypeEnum | None = PydField(default=None, description="Тип автора сообщения")
    author_entity_id: int | None = PydField(default=None, description="ID автора сообщения")
    author_role: ChatParticipantRoleEnum | None = PydField(default=None, description="Роль автора в чате: Staff, Member или Bot (если автор является участником чата)")
    author_entity_name: str | None = PydField(default=None, description="Имя автора сообщения")
    author_entity_photo: str | None = PydField(default=None, description="Фото автора сообщения")
    message_type: ChatMessageTypeEnum | None = PydField(default=None, description="Тип сообщения: Regular, System, Private")
    message_created_date: int | None = PydField(default=None, description="Дата создания сообщения (Unix time, сек.)")
    file_order: int | None = PydField(default=None, description="Порядковый номер файла внутри сообщения")
    file: CommonFile | None = PydField(default=None, description="Файл сообщения")


class ChatMessageFileKind(str, Enum):
    "Тип файлов для фильтрации вложений сообщений чата."
    All = "All"
    Media = "Media"
    Image = "Image"
    Video = "Video"
    Audio = "Audio"
    File = "File"


class ChatMessageFileRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ChatMessageFile] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class ChatMessageGet(RegosModel):
    "Модель фильтров для получения сообщений чата."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    chat_id: str | None = PydField(default=None, description="UUID чата")
    ids: list[str] | None = PydField(default=None, description="Массив UUID сообщений")
    from_date: int | None = PydField(default=None, description="Нижняя граница даты создания (Unix time, сек.)")
    to_date: int | None = PydField(default=None, description="Верхняя граница даты создания (Unix time, сек.)")
    limit: int | None = PydField(default=None, description="Лимит элементов выборки")
    offset: int | None = PydField(default=None, description="Смещение выборки")
    include_staff_private: bool | None = PydField(default=None, description="Включать Staff-ограниченные сообщения (если есть права): Private и System с action_code = StaffNoticeAdded")


class ChatMessageGetAround(RegosModel):
    "Модель получения окна сообщений вокруг выбранного сообщения."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    chat_id: str | None = PydField(default=None, description="UUID чата")
    id: str | None = PydField(default=None, description="UUID целевого сообщения")
    limit_before: int | None = PydField(default=None, description="Количество сообщений до целевого сообщения")
    limit_after: int | None = PydField(default=None, description="Количество сообщений после целевого сообщения")
    include_staff_private: bool | None = PydField(default=None, description="Включать приватные Staff-сообщения, если есть права")


class ChatMessageGetFiles(RegosModel):
    "Модель фильтров для получения файлов сообщений чата."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    chat_id: str | None = PydField(default=None, description="UUID чата")
    author_entity_type: ChatEntityTypeEnum | None = PydField(default=None, description="Тип автора сообщения")
    author_entity_id: int | None = PydField(default=None, description="ID автора сообщения")
    kind: ChatMessageFileKind | None = PydField(default=None, description="Тип файлов для фильтрации")
    from_date: int | None = PydField(default=None, description="Нижняя граница даты создания сообщения (Unix time, сек.)")
    to_date: int | None = PydField(default=None, description="Верхняя граница даты создания сообщения (Unix time, сек.)")
    include_staff_private: bool | None = PydField(default=None, description="Включать Staff-ограниченные сообщения (если есть права): Private и System с action_code = StaffNoticeAdded")
    limit: int | None = PydField(default=None, description="Лимит элементов выборки")
    offset: int | None = PydField(default=None, description="Смещение выборки")


class ChatMessageGetPinned(RegosModel):
    "Модель получения закрепленных сообщений чата."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    chat_id: str | None = PydField(default=None, description="UUID чата")
    limit: int | None = PydField(default=None, description="Лимит элементов выборки")
    offset: int | None = PydField(default=None, description="Смещение выборки")
    include_staff_private: bool | None = PydField(default=None, description="Включать приватные Staff-сообщения, если есть права")


class ChatMessageGetReactions(RegosModel):
    "Модель получения пользователей, поставивших реакции на сообщение."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str | None = PydField(default=None, description="UUID сообщения")
    reaction: str | None = PydField(default=None, description="Фильтр по реакции")
    limit: int | None = PydField(default=None, description="Лимит элементов выборки")
    offset: int | None = PydField(default=None, description="Смещение выборки")


class ChatMessageGetReadUsers(RegosModel):
    "Модель получения пользователей, прочитавших сообщение."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str | None = PydField(default=None, description="UUID сообщения")
    limit: int | None = PydField(default=None, description="Лимит элементов выборки")
    offset: int | None = PydField(default=None, description="Смещение выборки")


class ChatMessageMarkRead(RegosModel):
    "Модель отметки сообщений чата как прочитанных."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    chat_id: str | None = PydField(default=None, description="UUID чата")
    last_read_message_id: str | None = PydField(default=None, description="UUID последнего сообщения, до которого нужно отметить сообщения прочитанными включительно")


class ChatMessageMarkSent(RegosModel):
    "Модель проставления внешнего идентификатора отправленного сообщения."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str | None = PydField(default=None, description="UUID сообщения")
    external_message_id: str | None = PydField(default=None, description="Внешний ID сообщения")


class ChatMessageReaction(RegosModel):
    "Агрегированная реакция сообщения чата."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    reaction: str | None = PydField(default=None, description="Код реакции.")
    count: int | None = PydField(default=None, description="Количество пользователей с такой реакцией.")
    selected: bool | None = PydField(default=None, description="Признак, что текущий пользователь выбрал эту реакцию.")


class ChatMessageReactionUser(RegosModel):
    "Пользователь, поставивший реакцию на сообщение."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    user_id: int | None = PydField(default=None, description="Идентификатор пользователя.")
    user_name: str | None = PydField(default=None, description="Имя пользователя.")
    user_photo_url: str | None = PydField(default=None, description="URL фотографии пользователя.")
    reaction: str | None = PydField(default=None, description="Код реакции.")
    created_date: int | None = PydField(default=None, description="Дата установки реакции в Unix time.")


class ChatMessageReactionUserRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ChatMessageReactionUser] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class ChatMessageReadUser(RegosModel):
    "Пользователь, прочитавший сообщение."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    user_id: int | None = PydField(default=None, description="Идентификатор пользователя.")
    user_name: str | None = PydField(default=None, description="Имя пользователя.")
    user_photo_url: str | None = PydField(default=None, description="URL фотографии пользователя.")
    read_date: int | None = PydField(default=None, description="Дата прочтения в Unix time.")


class ChatMessageReadUserRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ChatMessageReadUser] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class ChatMessageRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ChatMessage] | Error | None = PydField(default=None, description="Массив результата.")


class ChatMessageRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ChatMessage] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class ChatMessageSearch(RegosModel):
    "Модель поиска сообщений в чате."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    chat_id: str | None = PydField(default=None, description="UUID чата")
    query: str | None = PydField(default=None, description="Поисковая строка; необязательна, если задан диапазон дат")
    from_date: int | None = PydField(default=None, description="Нижняя граница даты создания (Unix time, сек.)")
    to_date: int | None = PydField(default=None, description="Верхняя граница даты создания (Unix time, сек.)")
    limit: int | None = PydField(default=None, description="Лимит элементов выборки")
    offset: int | None = PydField(default=None, description="Смещение выборки")
    include_staff_private: bool | None = PydField(default=None, description="Включать приватные Staff-сообщения (если есть права)")


class ChatMessageSetPinned(RegosModel):
    "Модель изменения признака закрепления сообщения."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str | None = PydField(default=None, description="UUID сообщения")
    pinned: bool | None = PydField(default=None, description="true - закрепить сообщение, false - снять закрепление")


class ChatMessageSetReaction(RegosModel):
    "Модель переключения реакции текущего пользователя на сообщение."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str | None = PydField(default=None, description="UUID сообщения")
    reaction: str | None = PydField(default=None, description="Код реакции")


class ChatMessageSuggest(RegosModel):
    "Модель ephemeral-подсказок для быстрого ответа в чате."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    chat_id: str | None = PydField(default=None, description="UUID чата")
    author_entity_type: ChatEntityTypeEnum | None = PydField(default=None, description="Тип автора подсказок, только ChatBot")
    author_entity_id: int | None = PydField(default=None, description="Идентификатор чат-бота-автора")
    suggestions: list[str] | None = PydField(default=None, description="Подсказки быстрого ответа")
    source_message_id: str | None = PydField(default=None, description="UUID сообщения, к которому относятся подсказки")


class ChatMessageTypeEnum(str, Enum):
    "Тип сообщения чата."
    Default = "Default"
    Regular = "Regular"
    System = "System"
    Private = "Private"


class ChatMessageWriting(RegosModel):
    "Модель события \"пользователь печатает\"."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    chat_id: str | None = PydField(default=None, description="UUID чата")
    author_entity_type: ChatEntityTypeEnum | None = PydField(default=None, description="Тип сущности автора события writing (только вместе с author_entity_id)")
    author_entity_id: int | None = PydField(default=None, description="Идентификатор сущности автора события writing (только вместе с author_entity_type)")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.chat.chat import ChatEntityTypeEnum, ChatParticipantRoleEnum
from schemas.api.common.base import CommonFile, CommonMention, CommonMentionInput, CommonMentionOptions, Error, Insert_uuid_Result, UpdateResult




class ChatMessageAddFileRequest(RegosModel):
    """Compatibility request for ChatMessage/AddFile JSON payloads."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    chat_id: str | None = PydField(default=None)
    name: str | None = PydField(default=None)
    extension: str | None = PydField(default=None)
    data: str | None = PydField(default=None)


ChatMessageAddFileResponse: TypeAlias = ChatMessageAddFileResultRegosObjectResult
ChatMessageAddRequest: TypeAlias = ChatMessageAdd
ChatMessageAddResponse: TypeAlias = Insert_uuid_Result
ChatMessageCallbackRequest: TypeAlias = ChatMessageCallback
ChatMessageCallbackResponse: TypeAlias = UpdateResult
ChatMessageDeleteRequest: TypeAlias = ChatMessageDelete
ChatMessageDeleteResponse: TypeAlias = UpdateResult
ChatMessageEditRequest: TypeAlias = ChatMessageEdit
ChatMessageEditResponse: TypeAlias = UpdateResult
ChatMessageGetAroundRequest: TypeAlias = ChatMessageGetAround
ChatMessageGetAroundResponse: TypeAlias = ChatMessageRegosArrayResult
ChatMessageGetFilesRequest: TypeAlias = ChatMessageGetFiles
ChatMessageGetFilesResponse: TypeAlias = ChatMessageFileRegosOffsettedArrayResult
ChatMessageGetPinnedRequest: TypeAlias = ChatMessageGetPinned
ChatMessageGetPinnedResponse: TypeAlias = ChatMessageRegosOffsettedArrayResult
ChatMessageGetReactionsRequest: TypeAlias = ChatMessageGetReactions
ChatMessageGetReactionsResponse: TypeAlias = ChatMessageReactionUserRegosOffsettedArrayResult
ChatMessageGetReadUsersRequest: TypeAlias = ChatMessageGetReadUsers
ChatMessageGetReadUsersResponse: TypeAlias = ChatMessageReadUserRegosOffsettedArrayResult
ChatMessageGetRequest: TypeAlias = ChatMessageGet
ChatMessageGetResponse: TypeAlias = ChatMessageRegosOffsettedArrayResult
ChatMessageMarkReadRequest: TypeAlias = ChatMessageMarkRead
ChatMessageMarkReadResponse: TypeAlias = UpdateResult
ChatMessageMarkSentRequest: TypeAlias = ChatMessageMarkSent
ChatMessageMarkSentResponse: TypeAlias = UpdateResult
ChatMessageSearchRequest: TypeAlias = ChatMessageSearch
ChatMessageSearchResponse: TypeAlias = ChatMessageRegosOffsettedArrayResult
ChatMessageSetPinnedRequest: TypeAlias = ChatMessageSetPinned
ChatMessageSetPinnedResponse: TypeAlias = UpdateResult
ChatMessageSetReactionRequest: TypeAlias = ChatMessageSetReaction
ChatMessageSetReactionResponse: TypeAlias = UpdateResult
ChatMessageSuggestRequest: TypeAlias = ChatMessageSuggest
ChatMessageSuggestResponse: TypeAlias = UpdateResult
ChatMessageWritingRequest: TypeAlias = ChatMessageWriting
ChatMessageWritingResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['ChatMessage', 'ChatMessageAction', 'ChatMessageAdd', 'ChatMessageAddFileResult', 'ChatMessageAddFileResultRegosObjectResult', 'ChatMessageCallback', 'ChatMessageDelete', 'ChatMessageEdit', 'ChatMessageFile', 'ChatMessageFileRegosOffsettedArrayResult', 'ChatMessageGet', 'ChatMessageGetAround', 'ChatMessageGetFiles', 'ChatMessageGetPinned', 'ChatMessageGetReactions', 'ChatMessageGetReadUsers', 'ChatMessageMarkRead', 'ChatMessageMarkSent', 'ChatMessageReaction', 'ChatMessageReactionUser', 'ChatMessageReactionUserRegosOffsettedArrayResult', 'ChatMessageReadUser', 'ChatMessageReadUserRegosOffsettedArrayResult', 'ChatMessageRegosArrayResult', 'ChatMessageRegosOffsettedArrayResult', 'ChatMessageSearch', 'ChatMessageSetPinned', 'ChatMessageSetReaction', 'ChatMessageSuggest', 'ChatMessageWriting', 'ChatMessageAddFileRequest']


__all__ = [
    'ChatMessage',
    'ChatMessageAction',
    'ChatMessageAdd',
    'ChatMessageAddFileResult',
    'ChatMessageAddFileResultRegosObjectResult',
    'ChatMessageCallback',
    'ChatMessageDelete',
    'ChatMessageEdit',
    'ChatMessageFile',
    'ChatMessageFileKind',
    'ChatMessageFileRegosOffsettedArrayResult',
    'ChatMessageGet',
    'ChatMessageGetAround',
    'ChatMessageGetFiles',
    'ChatMessageGetPinned',
    'ChatMessageGetReactions',
    'ChatMessageGetReadUsers',
    'ChatMessageMarkRead',
    'ChatMessageMarkSent',
    'ChatMessageReaction',
    'ChatMessageReactionUser',
    'ChatMessageReactionUserRegosOffsettedArrayResult',
    'ChatMessageReadUser',
    'ChatMessageReadUserRegosOffsettedArrayResult',
    'ChatMessageRegosArrayResult',
    'ChatMessageRegosOffsettedArrayResult',
    'ChatMessageSearch',
    'ChatMessageSetPinned',
    'ChatMessageSetReaction',
    'ChatMessageSuggest',
    'ChatMessageTypeEnum',
    'ChatMessageWriting',
    'ChatMessageAddFileRequest',
    'ChatMessageGetRequest',
    'ChatMessageGetResponse',
    'ChatMessageGetFilesRequest',
    'ChatMessageGetFilesResponse',
    'ChatMessageAddRequest',
    'ChatMessageAddResponse',
    'ChatMessageAddFileResponse',
    'ChatMessageEditRequest',
    'ChatMessageEditResponse',
    'ChatMessageDeleteRequest',
    'ChatMessageDeleteResponse',
    'ChatMessageMarkReadRequest',
    'ChatMessageMarkReadResponse',
    'ChatMessageMarkSentRequest',
    'ChatMessageMarkSentResponse',
    'ChatMessageWritingRequest',
    'ChatMessageWritingResponse',
    'ChatMessageSuggestRequest',
    'ChatMessageSuggestResponse',
    'ChatMessageSearchRequest',
    'ChatMessageSearchResponse',
    'ChatMessageSetPinnedRequest',
    'ChatMessageSetPinnedResponse',
    'ChatMessageGetPinnedRequest',
    'ChatMessageGetPinnedResponse',
    'ChatMessageGetAroundRequest',
    'ChatMessageGetAroundResponse',
    'ChatMessageSetReactionRequest',
    'ChatMessageSetReactionResponse',
    'ChatMessageCallbackRequest',
    'ChatMessageCallbackResponse',
    'ChatMessageGetReactionsRequest',
    'ChatMessageGetReactionsResponse',
    'ChatMessageGetReadUsersRequest',
    'ChatMessageGetReadUsersResponse'
]
