"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocRetailSaleExt(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    session: DocCashSession | None = PydField(default=None, description="Модель, описывающая кассовые смены")
    uuid: str | None = PydField(default=None, description="UUID чека")
    date: int | None = PydField(default=None, description="Дата создания чека в Unix time")
    code: str | None = PydField(default=None, description="Код чека")
    status: DocChequeStatusEnum | None = PydField(default=None, description="Статус чека: <Opened | 1> - Открыт, <Paying | 2> - В процессе оплаты, <Closed | 3> - Закрыт,\n<Delayed | 4> - Отложен, <DelayedPayment | 5> - Отложен в процессе оплаты, <Canceled | 6> -\nАннулирован")
    cashier: User | None = PydField(default=None, description="Кассир")
    is_return: bool | None = PydField(default=None, description="Метка о том, что чек является чеком возврата")
    seller: User | None = PydField(default=None, description="Продавец")
    return_reason: RetailReturnReason | None = PydField(default=None, description="Причина возврата")
    card: RetailCard | None = PydField(default=None, description="Карта покупателя")
    amount: _Decimal | None = PydField(default=None, description="Сумма чека")
    agregate_status: AgregateStatusEnum | None = PydField(default=None, description="Статус агрегации чека: <New | 1 - Новый, <Prepared | 2 - Готов к агрегации, <Agregated | 3 - Агрегирован")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class RetailOperationList(RegosModel):
    "! МОДЕЛЬ УСТАРЕВШАЯ - будет удалена в ноябре 2025 года"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID операции")
    has_storno: bool | None = PydField(default=None, description="Метка о том, что операция является сторнирующей")
    storno_uuid: str | None = PydField(default=None, description="UUID сторнированной операции")
    document: DocRetailSaleExt | None = PydField(default=None, description="Документ розничной торговли")
    stock_id: int | None = PydField(default=None, description="ID склада")
    item: Item | None = PydField(default=None, description="Номенклатура")
    order: int | None = PydField(default=None, description="Позиция операции в документе продажи")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    price: _Decimal | None = PydField(default=None, description="Цена номенклатуры")
    price2: _Decimal | None = PydField(default=None, description="Цена номенклатуры без скидки")
    promo_id: int | None = PydField(default=None, description="ID промоакции")
    vat_value: _Decimal | None = PydField(default=None, description="Значение ставки НДС в процентах")
    last_update: int | None = PydField(default=None, description="Время последнего изменения записи в формате unix time")


class RetailOperationListGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    operating_cash_ids: list[int] | None = PydField(default=None, description="Массив ID касс")
    retail_card_ids: list[int] | None = PydField(default=None, description="Массив ID карт покупателей")
    customer_ids: list[int] | None = PydField(default=None, description="Массив ID покупателей")
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    search: str | None = PydField(default=None, description="Поиск про значениям параметров: item/name - Наименование номенклатуры, item/articul - Артикул номенклатуры, item/code -\nКод номенклатуры, document/code - Код чека, document/card/barcode_value - Штрих-код карты покупателя,\ndocument/card/customer/full_name - ФИО покупателя")
    limit: int | None = PydField(default=None, description="Количество возвращаемых элементов выборки")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class RetailOperationListRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[RetailOperationList] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import AgregateStatusEnum, Error
from schemas.api.docs.doc_cash_session import DocCashSession
from schemas.api.docs.doc_cheque import DocChequeStatusEnum
from schemas.api.rbac.user import User
from schemas.api.references.item import Item
from schemas.api.references.retail_card import RetailCard
from schemas.api.references.retail_return_reason import RetailReturnReason


RetailOperationListGetRequest: TypeAlias = RetailOperationListGet
RetailOperationListGetResponse: TypeAlias = RetailOperationListRegosOffsettedArrayResult


_MODEL_NAMES = ['DocRetailSaleExt', 'RetailOperationList', 'RetailOperationListGet', 'RetailOperationListRegosOffsettedArrayResult']


__all__ = [
    'DocRetailSaleExt',
    'RetailOperationList',
    'RetailOperationListGet',
    'RetailOperationListRegosOffsettedArrayResult',
    'RetailOperationListGetRequest',
    'RetailOperationListGetResponse'
]
