"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Report(RegosModel):
    "Модель, описывающая типы отчетов"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id отчета")
    group: ReportGroup | None = PydField(default=None, description="Группа отчетов")
    name: str | None = PydField(default=None, description="Наименование отчета")
    name_var: str | None = PydField(default=None)
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unixtime в секундах")


class Report0003Request(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Начальная дата")
    end_date: int | None = PydField(default=None, description="Конечная дата")
    currency_ids: list[int] | None = PydField(default=None, description="массив id валют (обязательное если in_base_currency = false, игнорируется если in_base_currency = true)")
    in_base_currency: bool | None = PydField(default=None, description="Отчёт строится в базовой валюте (true) или нет (false)")
    firm_id: int | None = PydField(default=None, description="Предприятие")


class Report0005Request(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="начальная дата")
    end_date: int | None = PydField(default=None, description="конечная дата")
    firm_id: int | None = PydField(default=None, description="id предприятия")
    stock_ids: list[int] | None = PydField(default=None, description="массив id складов")
    currency_id: int | None = PydField(default=None, description="id валюты")


class Report0006Request(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None)
    end_date: int | None = PydField(default=None)
    currency_id: int | None = PydField(default=None, description="Id валюты")
    firm_id: int | None = PydField(default=None, description="Id предприятия")


class Report0007Request(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None)
    end_date: int | None = PydField(default=None)
    firm_id: int | None = PydField(default=None)


class Report0009Request(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None)
    end_date: int | None = PydField(default=None)
    firm_id: int | None = PydField(default=None)


class Report0011CostTypeEnum(str, Enum):
    Default = "Default"
    AVG = "AVG"
    LAST = "LAST"


class Report0011_PeriodInterval(str, Enum):
    Default = "Default"
    Year = "Year"
    Month = "Month"
    Week = "Week"
    Day = "Day"


class Report0011_Request_Model(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: str | None = PydField(default=None)
    end_date: str | None = PydField(default=None)
    item_group_ids: list[int] | None = PydField(default=None)
    firm_id: int | None = PydField(default=None)
    currency_id: int | None = PydField(default=None, description="ID валюты")
    stock_ids: list[int] | None = PydField(default=None)
    type: Report0011_Type | None = PydField(default=None)
    period_interval: Report0011_PeriodInterval | None = PydField(default=None)
    cost_type: Report0011CostTypeEnum | None = PydField(default=None, description="тип расчета себестоимости")


class Report0011_Type(str, Enum):
    Default = "Default"
    WholeSale = "WholeSale"
    Retail = "Retail"


class Report0016Request(RegosModel):
    "Р—апрос на формирование отчёта"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    type: Report0016_Type | None = PydField(default=None, description="тип отчёт")
    data_type: Report0016_DataType | None = PydField(default=None, description="тип данных")
    start_date: int | None = PydField(default=None, description="начало периода")
    end_date: int | None = PydField(default=None, description="конец периода")
    stock_ids: list[int] | None = PydField(default=None, description="склады (необзятельное)")
    item_group_ids: list[int] | None = PydField(default=None, description="группы номенклатуры (не обзятельное)")
    criterion_a: int | None = PydField(default=None, description="значение критерия A")
    criterion_b: int | None = PydField(default=None, description="значение критерия B")


class Report0016_DataType(str, Enum):
    "Enum тип  ABC анализа"
    Turnover = "Turnover"
    Quantity = "Quantity"
    Marginality = "Marginality"


class Report0016_Type(str, Enum):
    All = "All"
    WholeSale = "WholeSale"
    Retail = "Retail"


class Report0017Request(RegosModel):
    "Р—апрос на формирование отчёта"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    type: Report0017_Type | None = PydField(default=None, description="по каким документам считаем")
    data_type: Report0017_DataType | None = PydField(default=None, description="тип данных")
    interval: Report0017_PeriodInterval | None = PydField(default=None, description="тип интервала")
    start_date: int | None = PydField(default=None, description="начало периода")
    end_date: int | None = PydField(default=None, description="конец периода")
    stock_ids: list[int] | None = PydField(default=None, description="склады (необзятельное)")
    item_group_ids: list[int] | None = PydField(default=None, description="группы номенклатуры (не обзятельное)")
    criterion_x: int | None = PydField(default=None, description="значение критерия x")
    criterion_y: int | None = PydField(default=None, description="значение критерия y")


class Report0017_DataType(str, Enum):
    "Enum данные отчёта (по чему считаем)"
    Turnover = "Turnover"
    Quantity = "Quantity"
    Marginality = "Marginality"


class Report0017_PeriodInterval(str, Enum):
    "Enum интервал отчёта"
    Default = "Default"
    Year = "Year"
    Month = "Month"
    Week = "Week"
    Day = "Day"


class Report0017_Type(str, Enum):
    "Enum тип отчёта (по каким документам считаем)"
    All = "All"
    WholeSale = "WholeSale"
    Retail = "Retail"


class Report0018Request(RegosModel):
    "Р—апрос на формирование отчёта"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    type: Report0018_Type | None = PydField(default=None, description="по каким документам считаем")
    data_type: Report0018_DataType | None = PydField(default=None, description="тип данных")
    interval: Report0018_PeriodInterval | None = PydField(default=None, description="тип интервала")
    start_date: int | None = PydField(default=None, description="начало периода")
    end_date: int | None = PydField(default=None, description="конец периода")
    stock_ids: list[int] | None = PydField(default=None, description="склады (необзятельное)")
    item_group_ids: list[int] | None = PydField(default=None, description="группы номенклатуры (не обзятельное)")
    criterion_x: int | None = PydField(default=None, description="значение критерия x")
    criterion_y: int | None = PydField(default=None, description="значение критерия y")
    criterion_a: int | None = PydField(default=None, description="значение критерия A")
    criterion_b: int | None = PydField(default=None, description="значение критерия B")


class Report0018_DataType(str, Enum):
    "Enum данные отчёта (по чему считаем)"
    Turnover = "Turnover"
    Quantity = "Quantity"
    Marginality = "Marginality"


class Report0018_PeriodInterval(str, Enum):
    "Enum интервал отчёта"
    Default = "Default"
    Year = "Year"
    Month = "Month"
    Week = "Week"
    Day = "Day"


class Report0018_Type(str, Enum):
    "Enum тип отчёта (по каким документам считаем)"
    All = "All"
    WholeSale = "WholeSale"
    Retail = "Retail"


class Report0020CostTypeEnum(str, Enum):
    "Перечисление для выбора типа стоимости"
    Default = "Default"
    AVG = "AVG"
    LAST = "LAST"


class Report0020GroupTypeEnum(str, Enum):
    "Перечисление для выбора типа группировки"
    Default = "Default"
    Group = "Group"
    Department = "Department"


class Report0020Request(RegosModel):
    "модель запроса на отчёт"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: int | None = PydField(default=None, description="Дата на которую формируем отчёт")
    firm_id: int | None = PydField(default=None, description="id фирмы")
    stock_ids: list[int] | None = PydField(default=None, description="массив id складов")
    price_type_id: int | None = PydField(default=None, description="id вида цены")
    currency_id: int | None = PydField(default=None, description="id валюты")
    cost_type: Report0020CostTypeEnum | None = PydField(default=None, description="тип расчета себестоимости")
    group_type: Report0020GroupTypeEnum | None = PydField(default=None, description="тип группировки")


class Report0021CostTypeEnum(str, Enum):
    "Перечисление для выбора типа стоимости"
    Default = "Default"
    AVG = "AVG"
    LAST = "LAST"


class Report0021GroupTypeEnum(str, Enum):
    "Перечисление типа группировки"
    Default = "Default"
    ByEmployees = "ByEmployees"
    ByPartners = "ByPartners"


class Report0021Request(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="начальная дата")
    end_date: int | None = PydField(default=None, description="конечная дата")
    firm_id: int | None = PydField(default=None, description="предприятие")
    currency_id: int | None = PydField(default=None, description="ID валюты")
    stock_ids: list[int] | None = PydField(default=None, description="массив id складов (не обяазтаельное)")
    report_type: Report0021TypeEnum | None = PydField(default=None, description="тип отчёта")
    grouping: Report0021GroupTypeEnum | None = PydField(default=None, description="группировка")
    cost_type: Report0021CostTypeEnum | None = PydField(default=None, description="способ расчёта себестоимости")


class Report0021TypeEnum(str, Enum):
    "Перечилсение типов отчёта"
    Default = "Default"
    RetailSale = "RetailSale"
    WholeSale = "WholeSale"


class Report0022Request(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Начальная дата")
    end_date: int | None = PydField(default=None, description="Конечная дата")
    firm_id: int | None = PydField(default=None, description="Предприятие (обязательное)")
    currency_id: int | None = PydField(default=None, description="ID валюты")
    stock_ids: list[int] | None = PydField(default=None, description="массив id складов")
    by_partner: bool | None = PydField(default=None, description="отчёт по контрагентам (true) или нет (false)")
    partner_ids: list[int] | None = PydField(default=None, description="массив id контрагентов (на него обращается внимание при by_partner = true)")


class Report0023Request(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Начальная дата")
    end_date: int | None = PydField(default=None, description="Конечная дата")
    firm_id: int | None = PydField(default=None, description="Предприятие (обязательное)")
    stock_ids: list[int] | None = PydField(default=None, description="массив id складов")


class Report0024CostTypeEnum(str, Enum):
    "Перечисление для выбора типа стоимости"
    Default = "Default"
    AVG = "AVG"
    LAST = "LAST"


class Report0024GroupTypeEnum(str, Enum):
    "Перечисление для выбора типа группировки"
    Default = "Default"
    Group = "Group"
    Department = "Department"


class Report0024Request(RegosModel):
    "модель запроса на отчёт"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Начальная дата")
    end_date: int | None = PydField(default=None, description="Конечная дата")
    firm_id: int | None = PydField(default=None, description="id фирмы")
    sender_stock_id: int | None = PydField(default=None, description="id скалада отправителя")
    price_type_id: int | None = PydField(default=None, description="id вида цены")
    currency_id: int | None = PydField(default=None, description="id валюты")
    cost_type: Report0024CostTypeEnum | None = PydField(default=None, description="тип расчета себестоимости")
    group_type: Report0024GroupTypeEnum | None = PydField(default=None, description="тип группировки")


class Report0025CostTypeEnum(str, Enum):
    Default = "Default"
    AVG = "AVG"
    LAST = "LAST"


class Report0025TypeEnum(str, Enum):
    Default = "Default"
    WholeSale = "WholeSale"
    Retail = "Retail"


class Report0025_Request(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: str | None = PydField(default=None)
    end_date: str | None = PydField(default=None)
    item_group_ids: list[int] | None = PydField(default=None)
    firm_id: int | None = PydField(default=None)
    currency_id: int | None = PydField(default=None, description="ID валюты")
    stock_ids: list[int] | None = PydField(default=None)
    type: Report0025TypeEnum | None = PydField(default=None)
    cost_type: Report0025CostTypeEnum | None = PydField(default=None, description="тип расчета себестоимости")


class Report0026CostTypeEnum(str, Enum):
    Default = "Default"
    AVG = "AVG"
    LAST = "LAST"


class Report0026TypeEnum(str, Enum):
    Default = "Default"
    WholeSale = "WholeSale"
    Retail = "Retail"


class Report0026_Request(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: str | None = PydField(default=None)
    end_date: str | None = PydField(default=None)
    item_group_ids: list[int] | None = PydField(default=None)
    firm_id: int | None = PydField(default=None)
    currency_id: int | None = PydField(default=None, description="ID валюты")
    stock_ids: list[int] | None = PydField(default=None)
    type: Report0026TypeEnum | None = PydField(default=None)
    cost_type: Report0026CostTypeEnum | None = PydField(default=None, description="тип расчета себестоимости")


class ReportAddRequest(RegosModel):
    "Единая модель входа для запроса любого отчета."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    report_id: int | None = PydField(default=None, description="Id отчета из метода Report/Get")
    request_data: Any = PydField(default=None, description="Параметры конкретного отчета. Размер JSON-объекта не должен превышать 4096 символов")


class ReportArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Report] | Error | None = PydField(default=None, description="Объект результата.")


class ReportGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id отчетов")
    group_ids: list[int] | None = PydField(default=None)


class ReportGroup(RegosModel):
    "Модель, описывающая группу отчетов"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id группы отчетов")
    parent_id: int | None = PydField(default=None, description="Id родительской группы отчетов")
    name: str | None = PydField(default=None, description="Наименование группы отчетов")
    name_var: str | None = PydField(default=None)
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unixtime в секундах")


class ReportSetError(RegosModel):
    "Модель для установки статуса ошибки по запросу отчёта."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    request_uuid: str | None = PydField(default=None, description="UUID запроса отчёта")
    api_login: str | None = PydField(default=None, description="ApiLogin аккаунта, в котором нужно установить ошибку")
    message: str | None = PydField(default=None, description="Текст ошибки")


class ReportSetPrepared(RegosModel):
    "Модель для установки подготовленного отчёта из внешнего сервиса."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    request_uuid: str | None = PydField(default=None, description="Uuid запроса отчёта")
    api_login: str | None = PydField(default=None, description="ApiLogin аккаунта, в котором сохраняется результат")
    file: str | None = PydField(default=None, description="Данные файла отчёта в base64")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, Insert_uuid_Result, UpdateResult
from schemas.api.reports.report_prepared import ReportPreparedArrayRegosObjectResult, ReportPreparedGet, ReportPreparedRemove
from schemas.api.reports.report_request import ReportRequestArrayRegosObjectResult, ReportRequestGet


ReportAddRequestRequest: TypeAlias = ReportAddRequest
ReportAddRequestResponse: TypeAlias = Insert_uuid_Result
ReportGetPreparedRequest: TypeAlias = ReportPreparedGet
ReportGetPreparedResponse: TypeAlias = ReportPreparedArrayRegosObjectResult
ReportGetRequest: TypeAlias = ReportGet
ReportGetRequestRequest: TypeAlias = ReportRequestGet
ReportGetRequestResponse: TypeAlias = ReportRequestArrayRegosObjectResult
ReportGetResponse: TypeAlias = ReportArrayRegosObjectResult
ReportRemovePreparedRequest: TypeAlias = ReportPreparedRemove
ReportRemovePreparedResponse: TypeAlias = UpdateResult
ReportSetErrorRequest: TypeAlias = ReportSetError
ReportSetErrorResponse: TypeAlias = UpdateResult
ReportSetPreparedRequest: TypeAlias = ReportSetPrepared
ReportSetPreparedResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['Report', 'Report0003Request', 'Report0005Request', 'Report0006Request', 'Report0007Request', 'Report0009Request', 'Report0011_Request_Model', 'Report0016Request', 'Report0017Request', 'Report0018Request', 'Report0020Request', 'Report0021Request', 'Report0022Request', 'Report0023Request', 'Report0024Request', 'Report0025_Request', 'Report0026_Request', 'ReportAddRequest', 'ReportArrayRegosObjectResult', 'ReportGet', 'ReportGroup', 'ReportSetError', 'ReportSetPrepared']


__all__ = [
    'Report',
    'Report0003Request',
    'Report0005Request',
    'Report0006Request',
    'Report0007Request',
    'Report0009Request',
    'Report0011CostTypeEnum',
    'Report0011_PeriodInterval',
    'Report0011_Request_Model',
    'Report0011_Type',
    'Report0016Request',
    'Report0016_DataType',
    'Report0016_Type',
    'Report0017Request',
    'Report0017_DataType',
    'Report0017_PeriodInterval',
    'Report0017_Type',
    'Report0018Request',
    'Report0018_DataType',
    'Report0018_PeriodInterval',
    'Report0018_Type',
    'Report0020CostTypeEnum',
    'Report0020GroupTypeEnum',
    'Report0020Request',
    'Report0021CostTypeEnum',
    'Report0021GroupTypeEnum',
    'Report0021Request',
    'Report0021TypeEnum',
    'Report0022Request',
    'Report0023Request',
    'Report0024CostTypeEnum',
    'Report0024GroupTypeEnum',
    'Report0024Request',
    'Report0025CostTypeEnum',
    'Report0025TypeEnum',
    'Report0025_Request',
    'Report0026CostTypeEnum',
    'Report0026TypeEnum',
    'Report0026_Request',
    'ReportAddRequest',
    'ReportArrayRegosObjectResult',
    'ReportGet',
    'ReportGroup',
    'ReportSetError',
    'ReportSetPrepared',
    'ReportGetRequest',
    'ReportGetResponse',
    'ReportGetRequestRequest',
    'ReportGetRequestResponse',
    'ReportAddRequestRequest',
    'ReportAddRequestResponse',
    'ReportGetPreparedRequest',
    'ReportGetPreparedResponse',
    'ReportRemovePreparedRequest',
    'ReportRemovePreparedResponse',
    'ReportSetPreparedRequest',
    'ReportSetPreparedResponse',
    'ReportSetErrorRequest',
    'ReportSetErrorResponse'
]
