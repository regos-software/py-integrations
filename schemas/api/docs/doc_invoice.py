"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocInvoice(RegosModel):
    "Модель, описывающая счёт-фактуру"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID счёт-фактуры")
    date: int | None = PydField(default=None, description="Дата")
    code: str | None = PydField(default=None, description="Код счёт-фактуры")
    invoice_type: DocInvoiceTypeEnum | None = PydField(default=None, description="Типы документа счёт-фактуры: <Income | 1> - Входящая счёт-фактура, <Outcome | 2> - Исходящая счёт-фактура, <Corrective | 3> - Корректировачная")
    corrected_date: int | None = PydField(default=None, description="Дата документа от которого идёт возврат")
    corrected_code: str | None = PydField(default=None, description="Код документа от которого идёт возврат")
    contract: DocContractShort | None = PydField(default=None, description="Договор")
    firm: Firm | None = PydField(default=None, description="Предприятие")
    partner: Partner | None = PydField(default=None, description="Контрагент")
    currency: Currency | None = PydField(default=None, description="Валюта")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    amount: _Decimal | None = PydField(default=None, description="Сумма")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    attached_user: User | None = PydField(default=None, description="Ответственный пользователь")
    base_document_id: int | None = PydField(default=None, description="ID документа, на основании которого создана счёт-фактура")
    document_type: int | None = PydField(default=None, description="Тип документа, на основании которого создана счёт-фактура")
    description: str | None = PydField(default=None, description="Примечание")
    uuid: str | None = PydField(default=None, description="UUID счёт-фактуры")
    external_code: str | None = PydField(default=None, description="Уникальный код ответа от сервиса faktura.uz")
    status: DocInvoiceStatusEnum | None = PydField(default=None, description="<New | 1> - Счёт-фактура создана, <InSentProgress | 2> - В процессе отпраки, <Sent | 3> - Отправлена,\n<InReceivedProgress | 4> - В процессе получения, <Received | 5> - Получнеа, <ErrorSent | 6> - Ошибка\nотправки, <ErrorReceived | 7> - Ошибка получения, <Unknown | 8> - Статус не известен")
    error: str | None = PydField(default=None, description="Ошибки при отпраке док-та на сервис faktura.uz")
    blocked: bool | None = PydField(default=None, description="Заблокирована ли счёт-фактура для редактирования: true - Заблокирована, false - Не заблокирована")
    current_user_blocked: bool | None = PydField(default=None, description="Заблокирована ли счёт-фактура текущим пользователем для редактирования: true - Заблокирована, false - Не заблокирована")
    performed: bool | None = PydField(default=None, description="Проведена ли счёт-фактура: true - Проведена, false - Не проведена")
    deleted_mark: bool | None = PydField(default=None, description="Помечена ли на удалние счёт-фактура: true - Помечена на удаление, false - Не помечена на удаление")
    last_update: int | None = PydField(default=None, description="Дата изменения в unix time")


class DocInvoiceAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    code: str | None = PydField(default=None, description="Код счёт-фактуры")
    date: int | None = PydField(default=None, description="Дата")
    corrected_date: int | None = PydField(default=None, description="Дата документа от которого идёт возврат")
    corrected_code: str | None = PydField(default=None, description="Код документа от которого идёт возвра")
    document_id: int | None = PydField(default=None, description="ID документа, на основании которого создаётся счёт-фактура")
    document_type_id: int | None = PydField(default=None, description="ID типа документа, на основании которого создаётся счёт-фактура")
    contract_id: int | None = PydField(default=None, description="ID договора")
    firm_id: int | None = PydField(default=None, description="ID предприятия")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    currency_id: int | None = PydField(default=None, description="ID вылюты")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    description: str | None = PydField(default=None, description="Примечание")
    invoice_type: DocInvoiceTypeEnum | None = PydField(default=None, description="Типы документа счёт-фактуры: <Income | 1> - Входящая счёт-фактура, <Outcome | 2> - Исходящая счёт-фактура, <Corrective | 3> - Корректировачная")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя. По умалчанию - текущий пользователь")


class DocInvoiceAddOnBase(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_type_id: int | None = PydField(default=None, description="ID типа документа, на основании которого создаётся счёт-фактура")
    document_id: int | None = PydField(default=None, description="ID документа, на основании которого создаётся счёт-фактура")
    code: str | None = PydField(default=None, description="Код счёт-фактуры")
    date: int | None = PydField(default=None, description="Дата")
    corrected_date: int | None = PydField(default=None, description="Дата документа от которого идёт возврат")
    corrected_code: str | None = PydField(default=None, description="Код документа от которого идёт возвра")
    description: str | None = PydField(default=None, description="Примечание")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя. По умалчанию - текущий пользователь")


class DocInvoiceColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocInvoiceColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocInvoiceColumns(str, Enum):
    Default = "Default"
    Id = "Id"
    Date = "Date"
    Code = "Code"
    PartnerName = "PartnerName"
    FirmName = "FirmName"
    CurrencyName = "CurrencyName"
    ContractName = "ContractName"
    Amount = "Amount"
    VatCalculationType = "VatCalculationType"
    AttacheUserName = "AttacheUserName"
    PriceTypeName = "PriceTypeName"
    Blocked = "Blocked"
    Performed = "Performed"
    DeletedMark = "DeletedMark"
    LastUpdate = "LastUpdate"


class DocInvoiceDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID счёт-фактуры")


class DocInvoiceDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id счёт-фактуры")


class DocInvoiceEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID счёт-фактуры")
    date: int | None = PydField(default=None, description="Дата")
    code: str | None = PydField(default=None, description="Код счёт-фактуры")
    corrected_date: int | None = PydField(default=None, description="Дата документа от которого идёт возврат")
    corrected_code: str | None = PydField(default=None, description="Код документа от которого идёт возвра")
    document_id: int | None = PydField(default=None, description="ID документа, на основании которого создаётся счёт-фактура")
    document_type_id: int | None = PydField(default=None, description="ID типа документа, на основании которого создаётся счёт-фактура")
    contract_id: int | None = PydField(default=None, description="ID договора")
    firm_id: int | None = PydField(default=None, description="ID предприятия")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    currency_id: int | None = PydField(default=None, description="ID вылюты")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    description: str | None = PydField(default=None, description="Примечание")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя. По умалчанию - текущий пользователь")


class DocInvoiceFromRoaming(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: str | None = PydField(default=None, description="id документа в системе ЭДО")
    roaming_id: str | None = PydField(default=None, description="id документа в системе ГНК")
    name: str | None = PydField(default=None, description="наименование счёт фактуры")
    partner_name: str | None = PydField(default=None, description="наименование контрагента")
    partner_inn: str | None = PydField(default=None, description="ИНН контрагента")
    contract: str | None = PydField(default=None, description="Договор")
    firm: str | None = PydField(default=None, description="предприятие")
    date: _DateTime | None = PydField(default=None, description="Дата документа")
    create_date: _DateTime | None = PydField(default=None, description="Дата создания счёт фактуры")
    update_date: _DateTime | None = PydField(default=None, description="Дата последнего изменения счёт фактуры")
    amount: _Decimal | None = PydField(default=None, description="Сумма счёт фактуры")


class DocInvoiceFromRoamingGet(RegosModel):
    "Получение документов от роуминга"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    firm_id: int | None = PydField(default=None, description="ID предприятия")
    start_date: int | None = PydField(default=None, description="Начало периода в формате Unix time в секундах")
    end_date: int | None = PydField(default=None, description="Конец периода в формате Unix time в секундах")
    limit: int | None = PydField(default=None, description="Количество возвращаемых элементов выборки")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocInvoiceFromRoamingImport(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str | None = PydField(default=None, description="ID документа в системе провайдера для получения")
    firm_id: int | None = PydField(default=None, description="ID предприятия, которое делает получение")


class DocInvoiceFromRoamingRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocInvoiceFromRoaming] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class DocInvoiceGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    invoice_type: DocInvoiceTypeEnum | None = PydField(default=None, description="Типы документа счёт-фактуры: <Income | 1> - Входящая счёт-фактура, <Outcome | 2> - Исходящая счёт-фактура, <Corrective | 3> - Корректировачная")
    ids: list[int] | None = PydField(default=None, description="Массив ID документов установки цен")
    contract_ids: list[int] | None = PydField(default=None, description="Массив ID договоров")
    firm_ids: list[int] | None = PydField(default=None, description="Массив ID пердприятий")
    partner_ids: list[int] | None = PydField(default=None, description="Массив ID контрагентов")
    external_code: str | None = PydField(default=None, description="Внешний код (id) документа")
    attached_user_ids: list[int] | None = PydField(default=None, description="Массив ID ответственных пользователей")
    performed: bool | None = PydField(default=None, description="Проведён ли документ: true - Проведён, false - Не проведён")
    blocked: bool | None = PydField(default=None, description="Заблокирован ли документ: true - Заблокирован, false - Не заблокирован")
    deleted_mark: bool | None = PydField(default=None, description="Помечен ли документ на удаление: true - Помечен на удаление, false - Не помечен на удаление")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    sort_orders: list[DocInvoiceColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по полям: code - Код счёт-фактуры, Partner/name - ФИО контрагента, Firm/name - Наименование предприятия,\nContract/name - Наименование договора, User/name - ФИО ответственного пользователя")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocInvoiceLockAndUnlock(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID счёт-фактур")


class DocInvoicePerformAndCancel(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID счёт-фактуры")


class DocInvoiceRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocInvoice] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class DocInvoiceSend(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_ids: list[int] | None = PydField(default=None, description="Массив ID счёт-фактур")
    firm_id: int | None = PydField(default=None, description="ID предприятия, от имени которого отправляется счёт-фактура")


class DocInvoiceSetExternalData(RegosModel):
    "Модель для установки статуса отправки документа"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None, description="-")
    integration_key: str | None = PydField(default=None, description="Устаревшее поле. Если передан одновременно с connected_integration_id, используется connected_integration_id")
    connected_integration_id: str | None = PydField(default=None, description="ID подключённой интеграции. Имеет приоритет над integration_key")
    external_id: str | None = PydField(default=None, description="-")
    roaming_id: str | None = PydField(default=None, description="-")


class DocInvoiceSetStatus(RegosModel):
    "Модель для установки статуса отправки документа"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None, description="-")
    status: DocInvoiceStatusEnum | None = PydField(default=None, description="-")
    error_message: str | None = PydField(default=None, description="-")


class DocInvoiceStatusEnum(str, Enum):
    "Статусы счёт фактуры"
    Default = "Default"
    New = "New"
    InSentProgress = "InSentProgress"
    Sent = "Sent"
    InReceivedProgress = "InReceivedProgress"
    Received = "Received"
    ErrorSent = "ErrorSent"
    ErrorReceived = "ErrorReceived"
    Unknown = "Unknown"


class DocInvoiceTypeEnum(str, Enum):
    "Типы документов счёт фактуры"
    Default = "Default"
    Income = "Income"
    Outcome = "Outcome"
    Corrective = "Corrective"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, SingleObjectResult, UpdateResult, VatCalculationTypeEnum
from schemas.api.docs.doc_contract import DocContractShort
from schemas.api.rbac.user import User
from schemas.api.references.currency import Currency
from schemas.api.references.firm import Firm
from schemas.api.references.partner import Partner


DocInvoiceActionResponse: TypeAlias = SingleObjectResult
DocInvoiceAddOnBaseRequest: TypeAlias = DocInvoiceAddOnBase
DocInvoiceAddOnBaseResponse: TypeAlias = InsertResult
DocInvoiceAddRequest: TypeAlias = DocInvoiceAdd
DocInvoiceAddResponse: TypeAlias = InsertResult
DocInvoiceDeleteMarkRequest: TypeAlias = DocInvoiceDeleteMark
DocInvoiceDeleteMarkResponse: TypeAlias = UpdateResult
DocInvoiceDeleteRequest: TypeAlias = DocInvoiceDelete
DocInvoiceDeleteResponse: TypeAlias = UpdateResult
DocInvoiceEditRequest: TypeAlias = DocInvoiceEdit
DocInvoiceEditResponse: TypeAlias = UpdateResult
DocInvoiceGetDocumentsFromRoamingRequest: TypeAlias = DocInvoiceFromRoamingGet
DocInvoiceGetDocumentsFromRoamingResponse: TypeAlias = DocInvoiceFromRoamingRegosOffsettedArrayResult
DocInvoiceGetRequest: TypeAlias = DocInvoiceGet
DocInvoiceGetResponse: TypeAlias = DocInvoiceRegosOffsettedArrayResult
DocInvoiceImportDocumentFromRoamingRequest: TypeAlias = DocInvoiceFromRoamingImport
DocInvoiceImportDocumentFromRoamingResponse: TypeAlias = SingleObjectResult
DocInvoiceLockRequest: TypeAlias = DocInvoiceLockAndUnlock
DocInvoiceLockResponse: TypeAlias = UpdateResult
DocInvoicePerformCancelRequest: TypeAlias = DocInvoicePerformAndCancel
DocInvoicePerformCancelResponse: TypeAlias = UpdateResult
DocInvoicePerformRequest: TypeAlias = DocInvoicePerformAndCancel
DocInvoicePerformResponse: TypeAlias = UpdateResult
DocInvoiceSendRequest: TypeAlias = DocInvoiceSend
DocInvoiceSendResponse: TypeAlias = SingleObjectResult
DocInvoiceSetExternalDataRequest: TypeAlias = DocInvoiceSetExternalData
DocInvoiceSetExternalDataResponse: TypeAlias = SingleObjectResult
DocInvoiceSetStatusRequest: TypeAlias = DocInvoiceSetStatus
DocInvoiceSetStatusResponse: TypeAlias = SingleObjectResult
DocInvoiceStatus: TypeAlias = DocInvoiceStatusEnum
DocInvoiceType: TypeAlias = DocInvoiceTypeEnum
DocInvoiceUnlockRequest: TypeAlias = DocInvoiceLockAndUnlock
DocInvoiceUnlockResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocInvoice', 'DocInvoiceAdd', 'DocInvoiceAddOnBase', 'DocInvoiceColumn', 'DocInvoiceDelete', 'DocInvoiceDeleteMark', 'DocInvoiceEdit', 'DocInvoiceFromRoaming', 'DocInvoiceFromRoamingGet', 'DocInvoiceFromRoamingImport', 'DocInvoiceFromRoamingRegosOffsettedArrayResult', 'DocInvoiceGet', 'DocInvoiceLockAndUnlock', 'DocInvoicePerformAndCancel', 'DocInvoiceRegosOffsettedArrayResult', 'DocInvoiceSend', 'DocInvoiceSetExternalData', 'DocInvoiceSetStatus']


__all__ = [
    'DocInvoice',
    'DocInvoiceAdd',
    'DocInvoiceAddOnBase',
    'DocInvoiceColumn',
    'DocInvoiceColumns',
    'DocInvoiceDelete',
    'DocInvoiceDeleteMark',
    'DocInvoiceEdit',
    'DocInvoiceFromRoaming',
    'DocInvoiceFromRoamingGet',
    'DocInvoiceFromRoamingImport',
    'DocInvoiceFromRoamingRegosOffsettedArrayResult',
    'DocInvoiceGet',
    'DocInvoiceLockAndUnlock',
    'DocInvoicePerformAndCancel',
    'DocInvoiceRegosOffsettedArrayResult',
    'DocInvoiceSend',
    'DocInvoiceSetExternalData',
    'DocInvoiceSetStatus',
    'DocInvoiceStatusEnum',
    'DocInvoiceTypeEnum',
    'DocInvoiceGetRequest',
    'DocInvoiceGetResponse',
    'DocInvoiceAddRequest',
    'DocInvoiceAddResponse',
    'DocInvoiceAddOnBaseRequest',
    'DocInvoiceAddOnBaseResponse',
    'DocInvoiceEditRequest',
    'DocInvoiceEditResponse',
    'DocInvoiceDeleteMarkRequest',
    'DocInvoiceDeleteMarkResponse',
    'DocInvoiceDeleteRequest',
    'DocInvoiceDeleteResponse',
    'DocInvoiceLockRequest',
    'DocInvoiceLockResponse',
    'DocInvoiceUnlockRequest',
    'DocInvoiceUnlockResponse',
    'DocInvoicePerformRequest',
    'DocInvoicePerformResponse',
    'DocInvoicePerformCancelRequest',
    'DocInvoicePerformCancelResponse',
    'DocInvoiceSendRequest',
    'DocInvoiceSendResponse',
    'DocInvoiceImportDocumentFromRoamingRequest',
    'DocInvoiceImportDocumentFromRoamingResponse',
    'DocInvoiceSetStatusRequest',
    'DocInvoiceSetStatusResponse',
    'DocInvoiceSetExternalDataRequest',
    'DocInvoiceSetExternalDataResponse',
    'DocInvoiceGetDocumentsFromRoamingRequest',
    'DocInvoiceGetDocumentsFromRoamingResponse',
    'DocInvoiceActionResponse',
    'DocInvoiceStatus',
    'DocInvoiceType'
]
