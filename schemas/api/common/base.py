"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.base import BaseSchema


JToken: TypeAlias = Any


class RegosModel(BaseSchema):
    """Base class for REGOS API Swagger schemas."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class AgregateStatusEnum(str, Enum):
    "статусы агрегации"
    Default = "Default"
    New = "New"
    Prepared = "Prepared"
    Agregated = "Agregated"


class ApiOffsettedResult(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: Any | Error | None = PydField(default=None, description="Результат выполнения запроса.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class ApiResult(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: Any | Error | None = PydField(default=None, description="Результат выполнения запроса.")


class BaseLockAndUnlock(RegosModel):
    "Модель для установки/сняти блокировкиы"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив Id документов поступления от контрагента")


class BaseSortColumn(RegosModel):
    "модель сортировки колонок"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: str | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class Base_ID(RegosModel):
    "Модель данных с ID (для блокировки, разблокировки, проведения, отмены проведения и т.д.)"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="-")


class BooleanRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: bool | Error | None = PydField(default=None, description="Объект результата.")


class CashAmountDetails(RegosModel):
    "Детали по кассе"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    current_amount: _Decimal | None = PydField(default=None, description="Текущая сумма в кассе")
    start_amount: _Decimal | None = PydField(default=None, description="Сумма в кассе на начало периода")
    income: _Decimal | None = PydField(default=None, description="Приход в кассу за период")
    outcome: _Decimal | None = PydField(default=None, description="Расход из кассу за период")
    end_amount: _Decimal | None = PydField(default=None, description="Сумма в кассе на конец периода")


class CashAmountDetailsRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: CashAmountDetails | Error | None = PydField(default=None, description="Объект результата.")


class ColumnSortOrderDirection(str, Enum):
    "enum для перечесление сортировок колонок"
    Default = "Default"
    ASC = "ASC"
    DESC = "DESC"


class CommonFile(RegosModel):
    "Описывает файл, загруженный и хранимый в системе REGOS."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Уникальный идентификатор файла в системе.")
    name: str | None = PydField(default=None, description="Отображаемое имя файла (без пути), то, что видит пользователь.")
    size: int | None = PydField(default=None, description="Размер файла в байтах.")
    extension: str | None = PydField(default=None, description="Расширение файла без точки (например, \"pdf\", \"jpg\").")
    mime_type: str | None = PydField(default=None, description="MIME-тип содержимого файла (например, \"application/pdf\", \"image/jpeg\").\nИспользуется клиентами и сервисами для корректной обработки файла.")
    media_type: CommonFileMediaTypeEnum | None = PydField(default=None, description="Тип медиа для выбора клиентского render-компонента.")
    width: int | None = PydField(default=None, description="Ширина визуального файла в пикселях.")
    height: int | None = PydField(default=None, description="Высота визуального файла в пикселях.")
    duration_ms: int | None = PydField(default=None, description="Длительность audio/video файла в миллисекундах.")
    aspect_ratio: _Decimal | None = PydField(default=None, description="Соотношение сторон, вычисляется как width / height.")
    date: int | None = PydField(default=None, description="Время создания файла (Unix timestamp).\nИспользуется для сортировки и отображения того, когда файл был загружен/создан.")
    user_id: int | None = PydField(default=None, description="Идентификатор пользователя, который создал файл (владелец).")
    access_level: CommonFileAccessLevelEnum | None = PydField(default=None, description="Уровень доступа файла (системный, персональный, общедоступный).\nОпределяет, как и кем файл может быть использован.")
    hash: str | None = PydField(default=None, description="Хеш содержимого файла (SHA-256).\nИспользуется для проверки целостности и предотвращения создания дубликатов.")
    folder: CommonFolder | None = PydField(default=None, description="Объект папки файла.\nЗаполняется только при версии БД 365 и выше.\nДля старых версий БД может быть null.")
    folder_id: int | None = PydField(default=None, description="Идентификатор папки файла (legacy-поле для обратной совместимости).\nДля новых клиентов предпочтительно использовать поле Regos_API.Models.Catalog.CommonFile.folder.")
    url: str | None = PydField(default=None, description="Публичный URL для доступа к файлу (прямой или временно подписанный).")
    last_update: int | None = PydField(default=None, description="Время последнего обновления метаданных или содержимого файла (Unix timestamp).\nПомогает отслеживать актуальность данных о файле.")


class CommonFileAccessLevelEnum(str, Enum):
    "Уровень доступа к файлу."
    system = "system"
    personal = "personal"
    public = "public"


class CommonFileMediaTypeEnum(str, Enum):
    "Тип медиа для выбора клиентского render-компонента."
    unknown = "unknown"
    image = "image"
    video = "video"
    audio = "audio"
    document = "document"
    archive = "archive"
    text = "text"
    other = "other"


class CommonFolder(RegosModel):
    "Модель папки для хранения файлов."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Идентификатор папки.")
    name: str | None = PydField(default=None, description="Наименование папки.")
    path: str | None = PydField(default=None, description="Полный путь папки в древовидной структуре.\nГенерируется автоматически на стороне сервера.")
    parent_id: int | None = PydField(default=None, description="Идентификатор родительской папки.\nДля корневой папки значение равно null.")
    user_id: int | None = PydField(default=None, description="Идентификатор владельца папки.")
    access_level: CommonFileAccessLevelEnum | None = PydField(default=None, description="Уровень доступа к папке.")
    date: int | None = PydField(default=None, description="Дата создания папки (Unix timestamp).")
    last_update: int | None = PydField(default=None, description="Дата последнего обновления папки (Unix timestamp).")
    deleted: bool | None = PydField(default=None, description="Флаг мягкого удаления папки.")


class CommonMention(RegosModel):
    "CommonMention описывает структурированное упоминание пользователя в текстовом поле"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID упоминания")
    source_entity_type: MentionSourceEntityTypeEnum | None = PydField(default=None, description="Тип сущности-источника: ChatMessage, ProjectTask, Lead, Deal, Ticket")
    source_entity_id: str | None = PydField(default=None, description="ID записи-источника")
    source_field: str | None = PydField(default=None, description="Поле источника: text или description")
    mentioned_entity_type: MentionedEntityTypeEnum | None = PydField(default=None, description="Тип упомянутой сущности: User")
    mentioned_entity_id: int | None = PydField(default=None, description="ID упомянутой сущности")
    offset: int | None = PydField(default=None, description="Начальная позиция фрагмента в тексте")
    length: int | None = PydField(default=None, description="Длина фрагмента в тексте")
    text: str | None = PydField(default=None, description="Видимый текст упоминания, например @Алиса")
    mentioned_entity_name: str | None = PydField(default=None, description="Имя упомянутой сущности для отображения")
    mentioned_entity_photo_url: str | None = PydField(default=None, description="Фото или аватар упомянутой сущности")
    read: bool | None = PydField(default=None, description="Признак прочтения упоминания упомянутой сущностью")
    read_date: int | None = PydField(default=None, description="Дата прочтения (Unix time, сек.)")
    created_user_id: int | None = PydField(default=None, description="ID пользователя, создавшего упоминание")
    created_date: int | None = PydField(default=None, description="Дата создания (Unix time, сек.)")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения (Unix time, сек.)")


class CommonMentionInput(RegosModel):
    "Входной контракт одного @-упоминания, которое клиент передает вместе с текстовым полем."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    mentioned_entity_type: MentionedEntityTypeEnum | None = PydField(default=None, description="Тип упомянутой сущности; если не указан, сервер трактует значение как User.")
    mentioned_entity_id: int | None = PydField(default=None, description="ID упомянутого пользователя.")
    offset: int | None = PydField(default=None, description="Позиция начала упоминания в переданном тексте.")
    length: int | None = PydField(default=None, description="Длина фрагмента упоминания в переданном тексте.")
    text: str | None = PydField(default=None, description="Фрагмент текста упоминания; должен совпадать с offset/length.")


class CommonMentionOptions(RegosModel):
    "Опции обработки упоминаний при сохранении текста."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    add_missing_users_to_context: bool | None = PydField(default=None, description="Если true, сервер может добавить упомянутых пользователей в контекст сущности\nпри наличии соответствующего права на участников или наблюдателей.")


class ContractDirection(str, Enum):
    All = "All"
    Income = "Income"
    Outcome = "Outcome"


class CrmEntityTypeEnum(str, Enum):
    Default = "Default"
    Lead = "Lead"
    Deal = "Deal"
    Client = "Client"
    Ticket = "Ticket"


class DataType(str, Enum):
    "Перечисление типов данных (используется в настройках)"
    Integer = "Integer"
    Float = "Float"
    String = "String"
    DateTime = "DateTime"


class DecimalRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: _Decimal | Error | None = PydField(default=None, description="Объект результата.")


class DiscountAction(str, Enum):
    Default = "Default"
    Discount = "Discount"
    Allowance = "Allowance"


class DiscountOperation(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None)
    document_id: int | None = PydField(default=None)
    action: DiscountAction | None = PydField(default=None)
    type: DiscountType | None = PydField(default=None)
    percent: _Decimal | None = PydField(default=None)
    amount: _Decimal | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


class DiscountOperationAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None, description="ID документа возврата от контрагента")
    document_type_id__: int | None = PydField(default=None, alias="_document_type_id_", description="Служебный ID типа документа, заполняется контроллером")
    action: DiscountAction | None = PydField(default=None, description="Тип: <Discount | 1> - Скидка, <Allowance | 2> - Надбавка")
    type: DiscountType | None = PydField(default=None, description="Тип скидки: <Percent | 1> - Процентная , <Amount | 2> - Числовая")
    percent: _Decimal | None = PydField(default=None, description="Процент скидки")
    amount: _Decimal | None = PydField(default=None, description="Сумма скидки")


class DiscountOperationDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID скидки/надбавки документа возврата от контрагента")
    document_type_id__: int | None = PydField(default=None, alias="_document_type_id_", description="Служебный ID типа документа, заполняется контроллером")


class DiscountOperationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID скидок/надбавок документов возврата от контрагента")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов возврата от контрагента")
    document_type_id__: int | None = PydField(default=None, alias="_document_type_id_", description="Служебный ID типа документа, заполняется контроллером")


class DiscountOperationRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DiscountOperation] | Error | None = PydField(default=None, description="Массив результата.")


class DiscountType(str, Enum):
    Default = "Default"
    Percent = "Percent"
    Amount = "Amount"


class DocsOperationsCopy(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    doc_from_id: int | None = PydField(default=None, description="Id документа из которого перемещается операция")
    doc_to_id: int | None = PydField(default=None, description="Id документа в который перемещается операция")


class DocsOperationsMovement(RegosModel):
    "propisan v fayle mdl_doc.cs"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="-")
    doc_from_id: int | None = PydField(default=None, description="-")
    doc_to_id: int | None = PydField(default=None, description="-")


class Error(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    error: int | None = PydField(default=None)
    description: str | None = PydField(default=None)


class ErrorResult(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: Error | None = PydField(default=None, description="Описание бизнес-ошибки.")


class Insert(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    new_id: int | None = PydField(default=None, description="ID созданной записи.")


class InsertResult(RegosModel):
    "модель возврата данных при insert данных"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: Insert | Error | None = PydField(default=None, description="Результат создания записи.")


class Insert_uuid(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    new_uuid: str | None = PydField(default=None, description="UUID созданной записи.")


class Insert_uuid_Result(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: Insert_uuid | Error | None = PydField(default=None, description="Результат создания записи с UUID.")


class Int64RegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: int | Error | None = PydField(default=None, description="Объект результата.")


class LegalStatus(str, Enum):
    "Юридческий статус"
    Default = "Default"
    Legal = "Legal"
    Natural = "Natural"


class Location(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    longitude: _Decimal | None = PydField(default=None)
    latitude: _Decimal | None = PydField(default=None)


class MentionSourceEntityTypeEnum(str, Enum):
    "Тип сущности, в текстовом поле которой сохранено упоминание."
    Default = "Default"
    ChatMessage = "ChatMessage"
    ProjectTask = "ProjectTask"
    Lead = "Lead"
    Deal = "Deal"
    Ticket = "Ticket"


class MentionedEntityTypeEnum(str, Enum):
    "Тип сущности, на которую указывает упоминание; сейчас поддерживаются пользователи."
    Default = "Default"
    User = "User"


class ObjectRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: Any | Error | None = PydField(default=None, description="Объект результата.")


class OkResult(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")


class Permission(RegosModel):
    "Модель, описывающая права доступа пользователей"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id права доступа")
    permission_group: PermissionGroup | None = PydField(default=None, description="Группа прав доступа")
    name: str | None = PydField(default=None, description="Наименование права доступа")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    default_value: bool | None = PydField(default=None, description="Значение права доступа по-умолчанию")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class SetPriceByPriceType_Model(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None, description="Id документа отгрузки контрагенту")
    price_type_id: int | None = PydField(default=None, description="Id вида цены")


class SexEnum(str, Enum):
    "enum для перечесление пола"
    none = "none"
    male = "male"
    female = "female"


class SingleArrayOffsettedResult(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: Any | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class SingleArrayResult(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: Any | Error | None = PydField(default=None, description="Массив результата.")


class SingleObjectResult(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: Any | Error | None = PydField(default=None, description="Объект результата.")


class StringRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: str | Error | None = PydField(default=None, description="Объект результата.")


class Table(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None)
    name: str | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


class Update(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    row_affected: int | None = PydField(default=None, description="Количество фактически изменённых записей.")
    ids: list[Any] | None = PydField(default=None, description="ID фактически изменённых записей.")


class UpdateResult(RegosModel):
    "модель возврата данных при update данных"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: Update | Error | None = PydField(default=None, description="Результат изменения данных.")


class VatCalculationTypeEnum(str, Enum):
    No = "No"
    Exclude = "Exclude"
    Include = "Include"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.rbac.permission_group import PermissionGroup


_MODEL_NAMES = ['ApiOffsettedResult', 'ApiResult', 'BaseLockAndUnlock', 'BaseSortColumn', 'Base_ID', 'BooleanRegosObjectResult', 'CashAmountDetails', 'CashAmountDetailsRegosObjectResult', 'CommonFile', 'CommonFolder', 'CommonMention', 'CommonMentionInput', 'CommonMentionOptions', 'DecimalRegosObjectResult', 'DiscountOperation', 'DiscountOperationAdd', 'DiscountOperationDelete', 'DiscountOperationGet', 'DiscountOperationRegosArrayResult', 'DocsOperationsCopy', 'DocsOperationsMovement', 'Error', 'ErrorResult', 'Insert', 'InsertResult', 'Insert_uuid', 'Insert_uuid_Result', 'Int64RegosObjectResult', 'Location', 'ObjectRegosObjectResult', 'OkResult', 'Permission', 'SetPriceByPriceType_Model', 'SingleArrayOffsettedResult', 'SingleArrayResult', 'SingleObjectResult', 'StringRegosObjectResult', 'Table', 'Update', 'UpdateResult']


__all__ = [
    'JToken',
    'RegosModel',
    'AgregateStatusEnum',
    'ApiOffsettedResult',
    'ApiResult',
    'BaseLockAndUnlock',
    'BaseSortColumn',
    'Base_ID',
    'BooleanRegosObjectResult',
    'CashAmountDetails',
    'CashAmountDetailsRegosObjectResult',
    'ColumnSortOrderDirection',
    'CommonFile',
    'CommonFileAccessLevelEnum',
    'CommonFileMediaTypeEnum',
    'CommonFolder',
    'CommonMention',
    'CommonMentionInput',
    'CommonMentionOptions',
    'ContractDirection',
    'CrmEntityTypeEnum',
    'DataType',
    'DecimalRegosObjectResult',
    'DiscountAction',
    'DiscountOperation',
    'DiscountOperationAdd',
    'DiscountOperationDelete',
    'DiscountOperationGet',
    'DiscountOperationRegosArrayResult',
    'DiscountType',
    'DocsOperationsCopy',
    'DocsOperationsMovement',
    'Error',
    'ErrorResult',
    'Insert',
    'InsertResult',
    'Insert_uuid',
    'Insert_uuid_Result',
    'Int64RegosObjectResult',
    'LegalStatus',
    'Location',
    'MentionSourceEntityTypeEnum',
    'MentionedEntityTypeEnum',
    'ObjectRegosObjectResult',
    'OkResult',
    'Permission',
    'SetPriceByPriceType_Model',
    'SexEnum',
    'SingleArrayOffsettedResult',
    'SingleArrayResult',
    'SingleObjectResult',
    'StringRegosObjectResult',
    'Table',
    'Update',
    'UpdateResult',
    'VatCalculationTypeEnum'
]
