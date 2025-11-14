from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator

from schemas.api.base import APIBaseResponse, BaseSchema
from schemas.api.common.sort_orders import SortOrders

from .partner_group import PartnerGroup


class LegalStatus(str, Enum):
    """
    Юридический статус контрагента.
    Значения по спецификации:
      - Legal   — юр. лицо
      - Natural — физ. лицо
    """

    Legal = "Legal"
    Natural = "Natural"


class Partner(BaseSchema):
    """Рид-модель контрагента."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., ge=1, description="ID контрагента.")
    group: PartnerGroup = PydField(..., description="Группа контрагента.")
    legal_status: LegalStatus = PydField(
        ..., description="Юридический статус (Legal|Natural)."
    )

    name: str = PydField(..., description="Короткое наименование контрагента.")
    fullname: Optional[str] = PydField(
        default=None, description="Полное наименование контрагента."
    )
    boss_name: Optional[str] = PydField(
        default=None, description="ФИО руководителя (если указано)."
    )

    address: Optional[str] = PydField(
        default=None, description="Адрес расположения контрагента."
    )
    phones: Optional[str] = PydField(
        default=None, description="Контактные телефоны (свободный формат)."
    )
    description: Optional[str] = PydField(
        default=None, description="Примечание к контрагенту."
    )

    inn: Optional[str] = PydField(default=None, description="ИНН.")
    bank_name: Optional[str] = PydField(
        default=None, description="Наименование банка обслуживающего счёта."
    )
    mfo: Optional[str] = PydField(default=None, description="МФО банка.")
    rs: Optional[str] = PydField(default=None, description="Расчётный счёт.")
    oked: Optional[str] = PydField(default=None, description="ОКЭД.")
    vat_index: Optional[str] = PydField(default=None, description="VAT индекс.")

    deleted_mark: bool = PydField(..., description="Флаг пометки на удаление.")
    last_update: int = PydField(
        ..., ge=0, description="Метка последнего изменения (unixtime, сек)."
    )

    @field_validator(
        "name",
        "fullname",
        "boss_name",
        "address",
        "phones",
        "description",
        "inn",
        "bank_name",
        "mfo",
        "rs",
        "oked",
        "vat_index",
        mode="before",
    )
    @classmethod
    def _strip_strings(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


class PartnerGetRequest(BaseSchema):
    """Параметры выборки контрагентов."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по списку ID контрагентов."
    )
    group_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по группам контрагентов."
    )
    legal_statuses: Optional[List[LegalStatus]] = PydField(
        default=None, description="Фильтр по юридическому статусу."
    )
    deleted_mark: Optional[bool] = PydField(
        default=None, description="Только помеченные/непомеченные на удаление."
    )
    search: Optional[str] = PydField(
        default=None, description="Поиск по названию/ИНН/телефону."
    )
    sort_orders: Optional[SortOrders] = PydField(
        default=None, description="Набор правил сортировки результата."
    )
    limit: Optional[int] = PydField(
        default=None, ge=1, description="Количество записей в выдаче."
    )
    offset: Optional[int] = PydField(
        default=None, ge=0, description="Смещение для пагинации."
    )

    @field_validator("search", mode="before")
    @classmethod
    def _strip_search(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


class PartnerGetResponse(APIBaseResponse[List[Partner]]):
    """Ответ на запрос списка контрагентов."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "LegalStatus",
    "Partner",
    "PartnerGetRequest",
    "PartnerGetResponse",
]
