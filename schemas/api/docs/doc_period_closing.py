"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocPeriodClosing(RegosModel):
    "Модель, описывающая документы закрытия периода"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа закрытия периода")
    close_date: int | None = PydField(default=None, description="Дата закрытия периода в формате unix time в секундах")
    run_date: int | None = PydField(default=None, description="Дата обработки документа закрытия периода в формате unix time в секундах")
    status: str | None = PydField(default=None, description="Статус документа закрытия периода: <WaitingClose | 1> - Ожидание закрытия периода, <WaitingSynchronise | 2>\n- Ожидание синхронизации, <InProcess | 3> - В процессе выполнения, <Closed | 4> - Закрыт, <Canceled |\n5> - Отменён")
    firm: Firm | None = PydField(default=None, description="Предприятие")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    scheduler_uuid: str | None = PydField(default=None, description="UUID планировщика")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")
    status_id: int | None = PydField(default=None, description="ID статуса документа закрытия периода")


class DocPeriodClosingAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    close_date: int | None = PydField(default=None, description="Дата закрытия периода в формате unix time в секундах")
    run_date: int | None = PydField(default=None, description="Дата обработки документа закрытия периода в формате unix time в секундах")
    firm_id: int | None = PydField(default=None, description="ID предприятия")
    description: str | None = PydField(default=None, description="Дополнительное описание")


class DocPeriodClosingCancelClose(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа закрытия периода")


class DocPeriodClosingCheck(RegosModel):
    "модель для ответа для метода проверки возможности создания документа закрытия периода"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None)
    cash_servers: list[DocPeriodClosingCheckStageElement] | None = PydField(default=None)
    operating_cashes: list[DocPeriodClosingCheckStageElement] | None = PydField(default=None)
    copy_: bool | None = PydField(default=None, alias="copy")
    aggregation: bool | None = PydField(default=None)
    has_before_docs_in_work: bool | None = PydField(default=None)
    has_after_docs_done: bool | None = PydField(default=None)


class DocPeriodClosingCheckGet(RegosModel):
    "модель входящих параметров для проверки возможности закрытия периода"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    firm_id: int | None = PydField(default=None, description="ID предприятия")
    close_date: int | None = PydField(default=None, description="Дата предполагаемого закрытия периода в формате Unix time в секундах")


class DocPeriodClosingCheckRegosOffsettedObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult when result is an object."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: DocPeriodClosingCheck | Error | None = PydField(default=None, description="Объект результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class DocPeriodClosingCheckStageElement(RegosModel):
    "модель для описания этапа проверки для возможности создания документа закрытия."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    name: str | None = PydField(default=None)
    status: bool | None = PydField(default=None)


class DocPeriodClosingColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocPeriodClosingColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocPeriodClosingColumns(str, Enum):
    Default = "Default"
    Id = "Id"
    CloseDate = "CloseDate"
    RunDate = "RunDate"
    StatusName = "StatusName"
    FirmName = "FirmName"


class DocPeriodClosingDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа закрытия периода")


class DocPeriodClosingEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id документа закрытия периода")
    close_date: int | None = PydField(default=None, description="Дата закрытия периода в формате unixtime в секундах")
    run_date: int | None = PydField(default=None, description="Дата обработки документа закрытия периода в формате unixtime в секундах")
    firm_id: int | None = PydField(default=None, description="Id предприятия")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    scheduler_uuid: str | None = PydField(default=None, description="UUID ?????? ? ????????????")


class DocPeriodClosingGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID документов закрытия периода")
    status_ids: list[int] | None = PydField(default=None, description="Массив ID статусов документов закрытия периода")
    firm_ids: list[int] | None = PydField(default=None, description="Массив ID предприятий")
    sort_order: list[DocPeriodClosingColumn] | None = PydField(default=None, description="Устаревшая сортировка выходных параметров. Используйте sort_orders")
    sort_orders: list[DocPeriodClosingColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по полям: id - Id документа, Firm/name - Наименование предприятия, Firm/inn - ИНН пердприятия")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocPeriodClosingRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocPeriodClosing] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult
from schemas.api.references.firm import Firm


DocPeriodClosingAddRequest: TypeAlias = DocPeriodClosingAdd
DocPeriodClosingAddResponse: TypeAlias = InsertResult
DocPeriodClosingCancelCloseRequest: TypeAlias = DocPeriodClosingCancelClose
DocPeriodClosingCancelCloseResponse: TypeAlias = UpdateResult
DocPeriodClosingDeleteRequest: TypeAlias = DocPeriodClosingDelete
DocPeriodClosingDeleteResponse: TypeAlias = UpdateResult
DocPeriodClosingEditRequest: TypeAlias = DocPeriodClosingEdit
DocPeriodClosingEditResponse: TypeAlias = UpdateResult
DocPeriodClosingGetRequest: TypeAlias = DocPeriodClosingGet
DocPeriodClosingGetResponse: TypeAlias = DocPeriodClosingRegosOffsettedArrayResult
DocPeriodClosingIsCanDoRequest: TypeAlias = DocPeriodClosingCheckGet
DocPeriodClosingIsCanDoResponse: TypeAlias = DocPeriodClosingCheckRegosOffsettedObjectResult


_MODEL_NAMES = ['DocPeriodClosing', 'DocPeriodClosingAdd', 'DocPeriodClosingCancelClose', 'DocPeriodClosingCheck', 'DocPeriodClosingCheckGet', 'DocPeriodClosingCheckRegosOffsettedObjectResult', 'DocPeriodClosingCheckStageElement', 'DocPeriodClosingColumn', 'DocPeriodClosingDelete', 'DocPeriodClosingEdit', 'DocPeriodClosingGet', 'DocPeriodClosingRegosOffsettedArrayResult']


__all__ = [
    'DocPeriodClosing',
    'DocPeriodClosingAdd',
    'DocPeriodClosingCancelClose',
    'DocPeriodClosingCheck',
    'DocPeriodClosingCheckGet',
    'DocPeriodClosingCheckRegosOffsettedObjectResult',
    'DocPeriodClosingCheckStageElement',
    'DocPeriodClosingColumn',
    'DocPeriodClosingColumns',
    'DocPeriodClosingDelete',
    'DocPeriodClosingEdit',
    'DocPeriodClosingGet',
    'DocPeriodClosingRegosOffsettedArrayResult',
    'DocPeriodClosingIsCanDoRequest',
    'DocPeriodClosingIsCanDoResponse',
    'DocPeriodClosingGetRequest',
    'DocPeriodClosingGetResponse',
    'DocPeriodClosingAddRequest',
    'DocPeriodClosingAddResponse',
    'DocPeriodClosingEditRequest',
    'DocPeriodClosingEditResponse',
    'DocPeriodClosingDeleteRequest',
    'DocPeriodClosingDeleteResponse',
    'DocPeriodClosingCancelCloseRequest',
    'DocPeriodClosingCancelCloseResponse'
]
