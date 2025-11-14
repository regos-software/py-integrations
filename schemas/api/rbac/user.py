from __future__ import annotations

from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator

from schemas.api.base import APIBaseResponse, BaseSchema
from schemas.api.common.sort_orders import SortOrders


class UserGroup(BaseSchema):
    """Группа пользователей RBAC."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., description="ID группы.")
    parent_id: Optional[int] = PydField(
        default=None, description="ID родительской группы."
    )
    name: str = PydField(..., description="Наименование группы.")
    child_count: int = PydField(..., ge=0, description="Количество дочерних групп.")
    last_update: int = PydField(
        ..., ge=0, description="Метка последнего обновления (unixtime, сек)."
    )

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


class User(BaseSchema):
    """Сотрудник (пользователь RBAC)."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., ge=1, description="ID пользователя.")
    full_name: Optional[str] = PydField(default=None, description="Полное имя.")
    main_phone: Optional[str] = PydField(default=None, description="Основной телефон.")
    user_group: Optional[UserGroup] = PydField(
        default=None, description="Группа пользователя."
    )
    enable_hints: Optional[bool] = PydField(
        default=None, description="Разрешены ли подсказки в интерфейсе."
    )
    system: Optional[bool] = PydField(
        default=None, description="Системная запись (не редактируется)."
    )
    seller_barcode: Optional[str] = PydField(
        default=None, description="Штрихкод продавца (если настроен)."
    )
    last_update: int = PydField(
        ..., ge=0, description="Метка последнего обновления (unixtime, сек)."
    )

    first_name: Optional[str] = PydField(default=None, description="Имя.")
    last_name: Optional[str] = PydField(default=None, description="Фамилия.")
    middle_name: Optional[str] = PydField(default=None, description="Отчество.")
    sex: Optional[str] = PydField(default="none", description="Пол пользователя.")
    date_of_birth: Optional[str] = PydField(
        default=None, description="Дата рождения в формате YYYY-MM-DD."
    )

    address: Optional[str] = PydField(default=None, description="Адрес проживания.")
    phones: Optional[str] = PydField(
        default=None, description="Дополнительные телефоны."
    )
    email: Optional[str] = PydField(default=None, description="Email пользователя.")
    description: Optional[str] = PydField(default=None, description="Комментарий.")
    login: Optional[str] = PydField(default=None, description="Логин для авторизации.")
    can_authorize: Optional[bool] = PydField(
        default=None, description="Может ли пользователь авторизоваться."
    )
    active: Optional[bool] = PydField(
        default=None, description="Активен ли пользователь."
    )
    language_code: Optional[str] = PydField(
        default=None, description="Язык интерфейса пользователя."
    )

    @field_validator(
        "full_name",
        "first_name",
        "last_name",
        "middle_name",
        "main_phone",
        "address",
        "phones",
        "email",
        "description",
        "login",
        "language_code",
        "seller_barcode",
        mode="before",
    )
    @classmethod
    def _strip_strings(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


class UserGetRequest(BaseSchema):
    """Параметры выборки пользователей."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по списку идентификаторов пользователей."
    )
    group_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по группам пользователей."
    )
    active: Optional[bool] = PydField(
        default=None, description="Возвращать только активных/неактивных пользователей."
    )
    can_authorize: Optional[bool] = PydField(
        default=None, description="Фильтр по возможности авторизации."
    )
    search: Optional[str] = PydField(
        default=None,
        description="Поиск по ФИО, логину, телефону или email.",
    )
    sort_orders: Optional[SortOrders] = PydField(
        default=None, description="Набор правил сортировки результата."
    )
    limit: Optional[int] = PydField(
        default=None,
        ge=1,
        description="Количество записей в выдаче (пагинация).",
    )
    offset: Optional[int] = PydField(
        default=None,
        ge=0,
        description="Смещение для пагинации.",
    )

    @field_validator("search", mode="before")
    @classmethod
    def _strip_search(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


class UserGetResponse(APIBaseResponse[List[User]]):
    """Ответ на запрос списка пользователей."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "UserGroup",
    "User",
    "UserGetRequest",
    "UserGetResponse",
]
