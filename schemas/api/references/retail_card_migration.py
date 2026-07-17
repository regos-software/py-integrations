"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class RetailCardMigrationHistory(RegosModel):
    "Описание истории перемещения карты"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID")
    date: int | None = PydField(default=None, description="дата перемещения карты с одной промоакции в другую в unixtime")
    type: RetailCardMigrationHistoryType | None = PydField(default=None, description="тип пермещения")
    promo_old: int | None = PydField(default=None, description="ID старой промоакции")
    promo_old_string: str | None = PydField(default=None, description="название старой промоакции")
    promo_new: int | None = PydField(default=None, description="ID новой промоакции")
    promo_new_string: str | None = PydField(default=None, description="название новой промоакции")


class RetailCardMigrationHistoryGet(RegosModel):
    "Модель для получения данных по истории миграции по карте покупателя"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    card_id: int | None = PydField(default=None, description="-")


class RetailCardMigrationHistoryRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[RetailCardMigrationHistory] | Error | None = PydField(default=None, description="Массив результата.")


class RetailCardMigrationHistoryType(str, Enum):
    "тип перемещения"
    Default = "Default"
    Auto = "Auto"
    Manual = "Manual"


class RetailCardMigrationSetting(RegosModel):
    "модель для описания настройки задачи по миграции розничных карт"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID")
    deleted: bool | None = PydField(default=None, description="метка удаления")
    task_id: int | None = PydField(default=None, description="ID задачи, к которой прикреплена настройка")
    type: RetailCardMigrationSettingType | None = PydField(default=None, description="Тип настройки: <ItemQuantity | 1> - количество купленной номенклатуры, <ItemAmount | 2> - сумма купленного, <SalesCount | 3> - количество чеков продаж")
    period_type: RetailCardMigrationSettingPeriod | None = PydField(default=None, description="Период выполнения задач: <Month | 1> - месяц, предшествующий дате выполнения задачи на миграцию, <Quarter |\n2> - квартал, предшествующий дате выполнения задачи на миграцию, <Year | 3> - год, предшествующий дате\nвыполнения задачи на миграцию, <Current_Month | 4> - текущий месяц, <Current_Quarter | 5> - текущий квартал,\n<Current_Year | 6> - текущий год")
    period: int | None = PydField(default=None, description="Значение периода. Если период - текущий месяц (квартал, год), то значение игнорируется")
    comparison: RetailCardMigrationSettingComparisonType | None = PydField(default=None, description="Тип сравнения в настройках: <Larger | 1> - больше, <Less | 2> - меньше, <Equal | 3> - равно,\n<EqualLarger | 4> - больше или равно, <EqualLess | 5> - меньше или равно")
    value: _Decimal | None = PydField(default=None, description="Значение для сравнения")
    order: int | None = PydField(default=None, description="Порядок выполнения (от 1 до 10)")


class RetailCardMigrationSettingBase(RegosModel):
    "Базовая модель для описания настроек задачи по миграции розничных карт"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    task_id: int | None = PydField(default=None, description="ID задачи, к которой прикреплена настройка")
    type: RetailCardMigrationSettingType | None = PydField(default=None, description="Тип настройки: <ItemQuantity | 1> - количество купленной номенклатуры, <ItemAmount | 2> - сумма купленного, <SalesCount | 3> - количество чеков продаж")
    period_type: RetailCardMigrationSettingPeriod | None = PydField(default=None, description="Период выполнения задач: <Month | 1> - месяц, предшествующий дате выполнения задачи на миграцию, <Quarter |\n2> - квартал, предшествующий дате выполнения задачи на миграцию, <Year | 3> - год, предшествующий дате\nвыполнения задачи на миграцию, <Current_Month | 4> - текущий месяц, <Current_Quarter | 5> - текущий квартал,\n<Current_Year | 6> - текущий год")
    period: int | None = PydField(default=None, description="Значение периода. Если период - текущий месяц (квартал, год), то значение игнорируется")
    comparison: RetailCardMigrationSettingComparisonType | None = PydField(default=None, description="Тип сравнения в настройках: <Larger | 1> - больше, <Less | 2> - меньше, <Equal | 3> - равно,\n<EqualLarger | 4> - больше или равно, <EqualLess | 5> - меньше или равно")
    value: _Decimal | None = PydField(default=None, description="Значение для сравнения")
    order: int | None = PydField(default=None, description="Порядок выполнения (от 1 до 10)")


class RetailCardMigrationSettingComparisonType(str, Enum):
    "тип сравнения в настройках"
    Default = "Default"
    Larger = "Larger"
    Less = "Less"
    Equal = "Equal"
    EqualLarger = "EqualLarger"
    EqualLess = "EqualLess"


class RetailCardMigrationSettingCondition(RegosModel):
    "модель для описания дополнительных условий настройки задачи по миграции розничных карт"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None)
    name: str | None = PydField(default=None, description="наименование поля занчения")
    setting_id: int | None = PydField(default=None, description="ID настройки, к которой относится дополнительное условие")
    type: RetailCardMigrationSettingConditionType | None = PydField(default=None, description="тип дополнительного условия")
    value: int | None = PydField(default=None, description="значение")
    exclude: bool | None = PydField(default=None, description="метка исключения. если true - то означает, что объект по доп условию будет исключён.")


class RetailCardMigrationSettingConditionBase(RegosModel):
    "базовая модель для описания дополнительных услових настройки задачи по миграции розничных карт"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    setting_id: int | None = PydField(default=None, description="ID настройки, к которой относится дополнительное условие")
    type: RetailCardMigrationSettingConditionType | None = PydField(default=None, description="тип дополнительного условия")
    value: int | None = PydField(default=None, description="значение")
    exclude: bool | None = PydField(default=None, description="метка исключения. если true - то означает, что объект по доп условию будет исключён.")


class RetailCardMigrationSettingConditionGet(RegosModel):
    "модель для получения дополнительных условий для настройки задачи по миграции рохничных карт"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="ID условий")
    setting_id: int | None = PydField(default=None, description="ID настройки для которой получает условие")


class RetailCardMigrationSettingConditionRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[RetailCardMigrationSettingCondition] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class RetailCardMigrationSettingConditionType(str, Enum):
    "тип условией в дополнительных условиях настройки"
    Default = "Default"
    Items = "Items"
    Item_Groups = "Item_Groups"
    Stocks = "Stocks"


class RetailCardMigrationSettingEdit(RegosModel):
    "модель для редактирвоания настройки задачи по миграции розничных карт"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID начтройки у задачи по перемещению карт покупателя")
    period_type: RetailCardMigrationSettingPeriod | None = PydField(default=None, description="Период выполнения задач: <Month | 1> - месяц, предшествующий дате выполнения задачи на миграцию, <Quarter |\n2> - квартал, предшествующий дате выполнения задачи на миграцию, <Year | 3> - год, предшествующий дате\nвыполнения задачи на миграцию, <Current_Month | 4> - текущий месяц, <Current_Quarter | 5> - текущий квартал,\n<Current_Year | 6> - текущий год")
    period: int | None = PydField(default=None, description="Значение периода. Если период - текущий месяц (квартал, год), то значение игнорируется")
    comparison: RetailCardMigrationSettingComparisonType | None = PydField(default=None, description="Тип сравнения в настройках: <Larger | 1> - больше, <Less | 2> - меньше, <Equal | 3> - равно,\n<EqualLarger | 4> - больше или равно, <EqualLess | 5> - меньше или равно")
    value: _Decimal | None = PydField(default=None, description="Значение для сравнения")
    order: int | None = PydField(default=None, description="Порядок выполнения (от 1 до 10)")


class RetailCardMigrationSettingGet(RegosModel):
    "модель для получения данных по настройке"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID настроек задач на перемещение")
    task_id: int | None = PydField(default=None, description="ID задачи по перемещению карты покупателя")


class RetailCardMigrationSettingPeriod(str, Enum):
    "период за который расчитываются условия"
    Default = "Default"
    Month = "Month"
    Quarter = "Quarter"
    Year = "Year"
    Current_Month = "Current_Month"
    Current_Quarter = "Current_Quarter"
    Current_Year = "Current_Year"


class RetailCardMigrationSettingRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[RetailCardMigrationSetting] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class RetailCardMigrationSettingType(str, Enum):
    "типы настроек"
    Default = "Default"
    ItemQuantity = "ItemQuantity"
    ItemAmount = "ItemAmount"
    SalesCount = "SalesCount"


class RetailCardMigrationTask(RegosModel):
    "модель для описания задачи по миграции розничных карт"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID")
    promo_from: PromoProgram | None = PydField(default=None, description="промо программа из которой миграция")
    promo_to: PromoProgram | None = PydField(default=None, description="промо программа в которую миграция")
    last_run: int | None = PydField(default=None, description="Время последнего запуска в unixtime. 0 - задача не выполнялась")
    start_date: int | None = PydField(default=None, description="Дата начала выполнения задачи в unixtime")
    end_date: int | None = PydField(default=None, description="Дата завершения выполнения задачи, если 0 - то задача бессрочная")
    run_period_type: RetailCardMigrationTaskPeriod | None = PydField(default=None, description="тип периода выполнения задачи")
    run_period: int | None = PydField(default=None, description="значение периода выполнения задачи")
    order: int | None = PydField(default=None, description="порядок выполнения (от а до я)")


class RetailCardMigrationTaskAdd(RegosModel):
    "модель для добавления задачи по миграции розничных карт"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    promo_from_id: int | None = PydField(default=None, description="ID программы лояльности, из которой перемещение")
    promo_to_id: int | None = PydField(default=None, description="ID программы лояльности, в которую перемещение")
    start_date: int | None = PydField(default=None, description="Дата начала выполнения задачи в unixtime")
    end_date: int | None = PydField(default=None, description="Дата завершения выполнения задачи, если 0 - то задача бессрочная")
    run_period_type: RetailCardMigrationTaskPeriod | None = PydField(default=None, description="тип периода выполнения задачи")
    run_period: int | None = PydField(default=None, description="значение периода выполнения задачи")
    order: int | None = PydField(default=None, description="порядок выполнения (от а до я)")


class RetailCardMigrationTaskEdit(RegosModel):
    "модель для редактирования задачи по миграции розничных карт"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID задачи по перемещению карт покупателей")
    promo_from_id: int | None = PydField(default=None, description="ID программы лояльности, из которой перемещение")
    promo_to_id: int | None = PydField(default=None, description="ID программы лояльности, в которую перемещение")
    start_date: int | None = PydField(default=None, description="Дата начала выполнения задачи в unixtime")
    end_date: int | None = PydField(default=None, description="Дата завершения выполнения задачи, если 0 - то задача бессрочная")
    run_period_type: RetailCardMigrationTaskPeriod | None = PydField(default=None, description="тип периода выполнения задачи")
    run_period: int | None = PydField(default=None, description="значение периода выполнения задачи")
    order: int | None = PydField(default=None, description="порядок выполнения (от а до я)")


class RetailCardMigrationTaskGet(RegosModel):
    "модель для получения задач по перемещению карт покупателей"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID задач на перемещение")
    promo_from_ids: list[int] | None = PydField(default=None, description="Массив ID программ лояльности, из которых перемещение")
    promo_to_ids: list[int] | None = PydField(default=None, description="Массив ID программ лояльности, в которые перемещение")
    sort_orders: list[BaseSortColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по наименованиям программ лояльности источника и назначения")
    limit: int | None = PydField(default=None, description="Количество элементов выборки, возвращаемых при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class RetailCardMigrationTaskPeriod(str, Enum):
    "периоды выполнения задач"
    Default = "Default"
    Day = "Day"
    Week = "Week"
    Month = "Month"
    Quarter = "Quarter"
    Year = "Year"


class RetailCardMigrationTaskRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[RetailCardMigrationTask] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import BaseSortColumn, Base_ID, Error, InsertResult, UpdateResult
from schemas.api.references.promo_program import PromoProgram


RetailCardMigrationSettingConditionAddRequest: TypeAlias = RetailCardMigrationSettingConditionBase
RetailCardMigrationSettingConditionAddResponse: TypeAlias = InsertResult
RetailCardMigrationSettingConditionDeleteRequest: TypeAlias = Base_ID
RetailCardMigrationSettingConditionDeleteResponse: TypeAlias = UpdateResult
RetailCardMigrationSettingConditionGetRequest: TypeAlias = RetailCardMigrationSettingConditionGet
RetailCardMigrationSettingConditionGetResponse: TypeAlias = RetailCardMigrationSettingConditionRegosOffsettedArrayResult
RetailCardMigrationSettingsAddRequest: TypeAlias = RetailCardMigrationSettingBase
RetailCardMigrationSettingsAddResponse: TypeAlias = InsertResult
RetailCardMigrationSettingsDeleteRequest: TypeAlias = Base_ID
RetailCardMigrationSettingsDeleteResponse: TypeAlias = UpdateResult
RetailCardMigrationSettingsEditRequest: TypeAlias = RetailCardMigrationSettingEdit
RetailCardMigrationSettingsEditResponse: TypeAlias = UpdateResult
RetailCardMigrationSettingsGetRequest: TypeAlias = RetailCardMigrationSettingGet
RetailCardMigrationSettingsGetResponse: TypeAlias = RetailCardMigrationSettingRegosOffsettedArrayResult
RetailCardMigrationTasksAddRequest: TypeAlias = RetailCardMigrationTaskAdd
RetailCardMigrationTasksAddResponse: TypeAlias = InsertResult
RetailCardMigrationTasksDeleteRequest: TypeAlias = Base_ID
RetailCardMigrationTasksDeleteResponse: TypeAlias = UpdateResult
RetailCardMigrationTasksEditRequest: TypeAlias = RetailCardMigrationTaskEdit
RetailCardMigrationTasksEditResponse: TypeAlias = UpdateResult
RetailCardMigrationTasksGetRequest: TypeAlias = RetailCardMigrationTaskGet
RetailCardMigrationTasksGetResponse: TypeAlias = RetailCardMigrationTaskRegosOffsettedArrayResult


_MODEL_NAMES = ['RetailCardMigrationHistory', 'RetailCardMigrationHistoryGet', 'RetailCardMigrationHistoryRegosArrayResult', 'RetailCardMigrationSetting', 'RetailCardMigrationSettingBase', 'RetailCardMigrationSettingCondition', 'RetailCardMigrationSettingConditionBase', 'RetailCardMigrationSettingConditionGet', 'RetailCardMigrationSettingConditionRegosOffsettedArrayResult', 'RetailCardMigrationSettingEdit', 'RetailCardMigrationSettingGet', 'RetailCardMigrationSettingRegosOffsettedArrayResult', 'RetailCardMigrationTask', 'RetailCardMigrationTaskAdd', 'RetailCardMigrationTaskEdit', 'RetailCardMigrationTaskGet', 'RetailCardMigrationTaskRegosOffsettedArrayResult']


__all__ = [
    'RetailCardMigrationHistory',
    'RetailCardMigrationHistoryGet',
    'RetailCardMigrationHistoryRegosArrayResult',
    'RetailCardMigrationHistoryType',
    'RetailCardMigrationSetting',
    'RetailCardMigrationSettingBase',
    'RetailCardMigrationSettingComparisonType',
    'RetailCardMigrationSettingCondition',
    'RetailCardMigrationSettingConditionBase',
    'RetailCardMigrationSettingConditionGet',
    'RetailCardMigrationSettingConditionRegosOffsettedArrayResult',
    'RetailCardMigrationSettingConditionType',
    'RetailCardMigrationSettingEdit',
    'RetailCardMigrationSettingGet',
    'RetailCardMigrationSettingPeriod',
    'RetailCardMigrationSettingRegosOffsettedArrayResult',
    'RetailCardMigrationSettingType',
    'RetailCardMigrationTask',
    'RetailCardMigrationTaskAdd',
    'RetailCardMigrationTaskEdit',
    'RetailCardMigrationTaskGet',
    'RetailCardMigrationTaskPeriod',
    'RetailCardMigrationTaskRegosOffsettedArrayResult',
    'RetailCardMigrationTasksGetRequest',
    'RetailCardMigrationTasksGetResponse',
    'RetailCardMigrationTasksAddRequest',
    'RetailCardMigrationTasksAddResponse',
    'RetailCardMigrationTasksEditRequest',
    'RetailCardMigrationTasksEditResponse',
    'RetailCardMigrationTasksDeleteRequest',
    'RetailCardMigrationTasksDeleteResponse',
    'RetailCardMigrationSettingsGetRequest',
    'RetailCardMigrationSettingsGetResponse',
    'RetailCardMigrationSettingsAddRequest',
    'RetailCardMigrationSettingsAddResponse',
    'RetailCardMigrationSettingsEditRequest',
    'RetailCardMigrationSettingsEditResponse',
    'RetailCardMigrationSettingsDeleteRequest',
    'RetailCardMigrationSettingsDeleteResponse',
    'RetailCardMigrationSettingConditionGetRequest',
    'RetailCardMigrationSettingConditionGetResponse',
    'RetailCardMigrationSettingConditionAddRequest',
    'RetailCardMigrationSettingConditionAddResponse',
    'RetailCardMigrationSettingConditionDeleteRequest',
    'RetailCardMigrationSettingConditionDeleteResponse'
]
