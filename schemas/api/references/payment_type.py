"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class PaymentType(RegosModel):
    "Модель, описывающая формы оплаты"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id формы оплаты")
    name: str | None = PydField(default=None, description="Наименование формы оплаты")
    account: Account | None = PydField(default=None, description="Счет, используемый для формы оплаты")
    shortkey: int | None = PydField(default=None, description="Горячая клавиша, используемая для формы оплаты")
    is_cash: bool | None = PydField(default=None, description="Метка о том, что оплата наличными")
    kkm_code: int | None = PydField(default=None, description="Код платежа в ККМ (-1 означает, что платеж не регистрируется в ККМ)")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unixtime в секундах")
    enabled: PaymentTypeEnabled | None = PydField(default=None, description="Метка о том, что форма оплаты доступна для использования. Принимаемые значения: <true | 1> (Доступна везде),\n<frontoffice | 2> (Доступна только в кассе), <backoffice | 3> (доступна только в Бэкофисе), <false |\n4> (недоступна)")
    image_url: str | None = PydField(default=None, description="URL изображения платёжной системы")


class PaymentTypeAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование формы оплаты")
    account_id: int | None = PydField(default=None, description="Id счета, используемого для формы оплаты")
    is_cash: bool | None = PydField(default=None, description="Метка о том, что оплата наличными")
    kkm_code: int | None = PydField(default=None, description="Код платежа в ККМ (-1 означает, что платеж не регистрируется в ККМ)")
    shortkey: int | None = PydField(default=None, description="Горячая клавиша, используемая для формы оплаты")
    enabled: PaymentTypeEnabled | None = PydField(default=None, description="Метка о том, что форма оплаты доступна для использования. Принимаемые значения: <true | 1> (Доступна везде),\n<frontoffice | 2> (Доступна только в кассе), <backoffice | 3> (доступна только в Бэкофисе), <false |\n4> (недоступна)")


class PaymentTypeArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[PaymentType] | Error | None = PydField(default=None, description="Объект результата.")


class PaymentTypeDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id формы оплаты")


class PaymentTypeEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id формы оплаты")
    name: str | None = PydField(default=None, description="Наименование формы оплаты")
    account_id: int | None = PydField(default=None, description="Id счета, используемого для формы оплаты")
    is_cash: bool | None = PydField(default=None, description="Метка о том, что оплата наличными")
    kkm_code: int | None = PydField(default=None, description="Код платежа в ККМ (-1 означает, что платеж не регистрируется в ККМ)")
    shortkey: int | None = PydField(default=None, description="Горячая клавиша, используемая для формы оплаты")
    enabled: PaymentTypeEnabled | None = PydField(default=None, description="Метка о том, что форма оплаты доступна для использования. Принимаемые значения: <true | 1> (Доступна везде),\n<frontoffice | 2> (Доступна только в кассе), <backoffice | 3> (доступна только в Бэкофисе), <false |\n4> (недоступна)")


class PaymentTypeEnabled(str, Enum):
    True_ = "True"
    Frontoffice = "Frontoffice"
    Backoffice = "Backoffice"
    False_ = "False"


class PaymentTypeGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id форм оплаты")
    account_ids: list[int] | None = PydField(default=None, description="Массив id счетов, используемых для форм оплаты")
    enabled: PaymentTypeEnabled | None = PydField(default=None, description="Метка о том, что форма оплаты доступна для использования. Принимаемые значения: <true | 1> (Доступна везде),\n<frontoffice | 2> (Доступна только в кассе), <backoffice | 3> (доступна только в Бэкофисе), <false |\n4> (недоступна)")
    is_cash: bool | None = PydField(default=None, description="Фильтр по признаку оплаты наличными")


class PaymentTypeImage(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None)
    payment_type_id: int | None = PydField(default=None)
    width: int | None = PydField(default=None)
    height: int | None = PydField(default=None)
    size: int | None = PydField(default=None)
    url: str | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


class PaymentTypeImageGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="IВ изоюражения")
    payment_type_ids: list[int] | None = PydField(default=None, description="ID формы оплаты")


class PaymentTypeImageRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[PaymentTypeImage] | Error | None = PydField(default=None, description="Массив результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Base_ID, Error, InsertResult, UpdateResult
from schemas.api.references.account import Account


PaymentTypeAddImageResponse: TypeAlias = UpdateResult
PaymentTypeAddRequest: TypeAlias = PaymentTypeAdd
PaymentTypeAddResponse: TypeAlias = InsertResult
PaymentTypeDeleteImageRequest: TypeAlias = Base_ID
PaymentTypeDeleteImageResponse: TypeAlias = UpdateResult
PaymentTypeDeleteRequest: TypeAlias = PaymentTypeDelete
PaymentTypeDeleteResponse: TypeAlias = UpdateResult
PaymentTypeEditRequest: TypeAlias = PaymentTypeEdit
PaymentTypeEditResponse: TypeAlias = UpdateResult
PaymentTypeGetImageRequest: TypeAlias = PaymentTypeImageGet
PaymentTypeGetImageResponse: TypeAlias = PaymentTypeImageRegosArrayResult
PaymentTypeGetRequest: TypeAlias = PaymentTypeGet
PaymentTypeGetResponse: TypeAlias = PaymentTypeArrayRegosObjectResult


_MODEL_NAMES = ['PaymentType', 'PaymentTypeAdd', 'PaymentTypeArrayRegosObjectResult', 'PaymentTypeDelete', 'PaymentTypeEdit', 'PaymentTypeGet', 'PaymentTypeImage', 'PaymentTypeImageGet', 'PaymentTypeImageRegosArrayResult']


__all__ = [
    'PaymentType',
    'PaymentTypeAdd',
    'PaymentTypeArrayRegosObjectResult',
    'PaymentTypeDelete',
    'PaymentTypeEdit',
    'PaymentTypeEnabled',
    'PaymentTypeGet',
    'PaymentTypeImage',
    'PaymentTypeImageGet',
    'PaymentTypeImageRegosArrayResult',
    'PaymentTypeGetRequest',
    'PaymentTypeGetResponse',
    'PaymentTypeAddRequest',
    'PaymentTypeAddResponse',
    'PaymentTypeEditRequest',
    'PaymentTypeEditResponse',
    'PaymentTypeDeleteRequest',
    'PaymentTypeDeleteResponse',
    'PaymentTypeGetImageRequest',
    'PaymentTypeGetImageResponse',
    'PaymentTypeAddImageResponse',
    'PaymentTypeDeleteImageRequest',
    'PaymentTypeDeleteImageResponse'
]
