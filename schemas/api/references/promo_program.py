"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class PromoProgram(RegosModel):
    "Модель, описывающая промоакции"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id промоакции")
    name: str | None = PydField(default=None, description="Наименование промоакции")
    type: PromoProgramType | None = PydField(default=None, description="Тип промоакции")
    active: bool | None = PydField(default=None, description="Метка о том, что промоакция активная")
    days: list[int] | None = PydField(default=None, description="Дни недели, в которые промоакция активна")
    start_time: str | None = PydField(default=None, description="Время начала промоакции: ЧЧ:ММ:СС")
    end_time: str | None = PydField(default=None, description="Время окончания промоакции: ЧЧ:ММ:СС")
    start_date: str | None = PydField(default=None, description="Дата начала промоакции: ГГГГ:ММ:ДД")
    end_date: str | None = PydField(default=None, description="Дата окончания промоакции: ГГГГ:ММ:ДД")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    sub_type: int | None = PydField(default=None, description="Если программа лояльности внешняя, то это поле должно быть заполнено")
    priority: int | None = PydField(default=None, description="Приоритет (применения промо-акции)")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unixtime в секундах")


class PromoProgramAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование промоакции")
    type_id: int | None = PydField(default=None, description="Id типа промоакции")
    sub_type: int | None = PydField(default=None, description="Тип внешней системы лояльности")
    active: bool | None = PydField(default=None, description="Метка о том, что промоакция активная")
    days: list[int] | None = PydField(default=None, description="Дни недели, в которые промоакция активна")
    start_time: str | None = PydField(default=None, description="Время начала промоакции: ЧЧ:ММ:СС")
    end_time: str | None = PydField(default=None, description="Время окончания промоакции: ЧЧ:ММ:СС")
    start_date: str | None = PydField(default=None, description="Дата начала промоакции: ГГГГ:ММ:ДД")
    end_date: str | None = PydField(default=None, description="Дата окончания промоакции: ГГГГ:ММ:ДД")
    priority: int | None = PydField(default=None, description="Порядок (применения промо-акции)")
    description: str | None = PydField(default=None, description="Дополнительное описание")


class PromoProgramArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[PromoProgram] | Error | None = PydField(default=None, description="Объект результата.")


class PromoProgramDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id промоакции")


class PromoProgramEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="id группы")
    name: str | None = PydField(default=None, description="Наименование промоакции")
    active: bool | None = PydField(default=None, description="Метка о том, что промоакция активная")
    days: list[int] | None = PydField(default=None, description="Дни недели, в которые промоакция активна")
    start_time: str | None = PydField(default=None, description="Время начала промоакции: ЧЧ:ММ:СС")
    end_time: str | None = PydField(default=None, description="Время окончания промоакции: ЧЧ:ММ:СС")
    start_date: str | None = PydField(default=None, description="Дата начала промоакции: ГГГГ:ММ:ДД")
    end_date: str | None = PydField(default=None, description="Дата окончания промоакции: ГГГГ:ММ:ДД")
    priority: int | None = PydField(default=None, description="Приоритет (применения промо-акции)")
    description: str | None = PydField(default=None, description="Дополнительное описание")


class PromoProgramGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id промоакций")
    type_ids: list[int] | None = PydField(default=None, description="Массив id типов промоакций")
    allowed_retail_card: bool | None = PydField(default=None, description="Можно ли к данной программе привязать карты покупателя (карты покупателя можно привязать колько к Бонусной системеtype=1)")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult
from schemas.api.references.promo_program_type import PromoProgramType


PromoProgramAddRequest: TypeAlias = PromoProgramAdd
PromoProgramAddResponse: TypeAlias = InsertResult
PromoProgramDeleteRequest: TypeAlias = PromoProgramDelete
PromoProgramDeleteResponse: TypeAlias = UpdateResult
PromoProgramEditRequest: TypeAlias = PromoProgramEdit
PromoProgramEditResponse: TypeAlias = UpdateResult
PromoProgramGetRequest: TypeAlias = PromoProgramGet
PromoProgramGetResponse: TypeAlias = PromoProgramArrayRegosObjectResult


_MODEL_NAMES = ['PromoProgram', 'PromoProgramAdd', 'PromoProgramArrayRegosObjectResult', 'PromoProgramDelete', 'PromoProgramEdit', 'PromoProgramGet']


__all__ = [
    'PromoProgram',
    'PromoProgramAdd',
    'PromoProgramArrayRegosObjectResult',
    'PromoProgramDelete',
    'PromoProgramEdit',
    'PromoProgramGet',
    'PromoProgramGetRequest',
    'PromoProgramGetResponse',
    'PromoProgramAddRequest',
    'PromoProgramAddResponse',
    'PromoProgramEditRequest',
    'PromoProgramEditResponse',
    'PromoProgramDeleteRequest',
    'PromoProgramDeleteResponse'
]
