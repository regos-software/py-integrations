"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class User(RegosModel):
    "Модель, описывающая пользователя и его параметры"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id пользователя в системе")
    full_name: str | None = PydField(default=None, description="ФИО")
    main_phone: str | None = PydField(default=None, description="телефон для авторизации пользователя")
    internal_phone: str | None = PydField(default=None, description="Внутренний телефон пользователя (поле может быть null)")
    user_group: UserGroup | None = PydField(default=None, description="Группа пользователя")
    enable_hints: bool | None = PydField(default=None, description="Показывать подсказки или нет")
    system: bool | None = PydField(default=None, description="пользователь системный или нет")
    sub: str | None = PydField(default=None, description="UUID пользователя в едином профиле (может быть null)")
    photo_url: str | None = PydField(default=None, description="Ссылка на фотографию (аватар) пользователя")
    fields: list[FieldValue] | None = PydField(default=None, description="Значения дополнительных полей пользователя")
    seller_barcode: str | None = PydField(default=None, description="Штрих-код продавца")
    first_name: str | None = PydField(default=None)
    last_name: str | None = PydField(default=None)
    middle_name: str | None = PydField(default=None)
    sex: SexEnum | None = PydField(default=None, description="enum для перечесление пола")
    date_of_birth: str | None = PydField(default=None)
    address: str | None = PydField(default=None)
    phones: str | None = PydField(default=None)
    email: str | None = PydField(default=None)
    description: str | None = PydField(default=None)
    login: str | None = PydField(default=None)
    can_authorize: bool | None = PydField(default=None)
    active: bool | None = PydField(default=None)
    language_code: str | None = PydField(default=None)
    last_update: int | None = PydField(default=None, description="Дата последнего обновления в Unix time")


class UserAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    group_id: int | None = PydField(default=None, description="ID группы пользователей в системе")
    new_password: str | None = PydField(default=None, description="Новый пароль пользователя в системе")
    new_password_confirm: str | None = PydField(default=None, description="Подтверждение пароля пользователя в системе")
    fields: list[FieldValueAdd] | None = PydField(default=None, description="Значения дополнительных полей пользователя")
    first_name: str | None = PydField(default=None)
    last_name: str | None = PydField(default=None)
    middle_name: str | None = PydField(default=None)
    sex: SexEnum | None = PydField(default=None, description="enum для перечесление пола")
    date_of_birth: str | None = PydField(default=None)
    address: str | None = PydField(default=None)
    phones: str | None = PydField(default=None)
    email: str | None = PydField(default=None)
    description: str | None = PydField(default=None)
    login: str | None = PydField(default=None)
    can_authorize: bool | None = PydField(default=None)
    active: bool | None = PydField(default=None)
    language_code: str | None = PydField(default=None)


class UserAddGlobal(RegosModel):
    "Модель для добавления глобального пользовтеля"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    phone: str | None = PydField(default=None, description="Номер телефона пользователя")
    group_id: int | None = PydField(default=None, description="ID группы пользователей в системе")


class UserAddGlobalResposne(RegosModel):
    "Ответ метода добавления глобального пользховатлея"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    send_registration: bool | None = PydField(default=None, description="флаг показывающий, что пользователю было отправлено сообщение о регистрации")
    user_id: int | None = PydField(default=None, description="id пользователя")


class UserAddGlobalResposneRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: UserAddGlobalResposne | Error | None = PydField(default=None, description="Объект результата.")


class UserCheckLoginIn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    login: str | None = PydField(default=None, description="Логин пользователя в систему")


class UserCheckLoginOut(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    enable: bool | None = PydField(default=None)


class UserCheckLoginOutRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: UserCheckLoginOut | Error | None = PydField(default=None, description="Объект результата.")


class UserDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id пользователя в системе")


class UserEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID пользователя в системе")
    group_id: int | None = PydField(default=None, description="ID группы пользователей в системе")
    internal_phone: str | None = PydField(default=None, description="Внутренний телефон пользователя. применяется только для глобальных пользователей")
    fields: list[FieldValueEdit] | None = PydField(default=None, description="Изменения значений дополнительных полей пользователя")
    first_name: str | None = PydField(default=None)
    last_name: str | None = PydField(default=None)
    middle_name: str | None = PydField(default=None)
    sex: SexEnum | None = PydField(default=None, description="enum для перечесление пола")
    date_of_birth: str | None = PydField(default=None)
    address: str | None = PydField(default=None)
    phones: str | None = PydField(default=None)
    email: str | None = PydField(default=None)
    description: str | None = PydField(default=None)
    login: str | None = PydField(default=None)
    can_authorize: bool | None = PydField(default=None)
    active: bool | None = PydField(default=None)
    language_code: str | None = PydField(default=None)


class UserGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id пользователей")
    group_ids: list[int] | None = PydField(default=None, description="Массив id групп пользователей")
    gender: SexEnum | None = PydField(default=None, description="Пол пользователя: <None | 1> - не указан, <Male | 2> - мужской, <Female | 3> - женский")
    can_authorize: bool | None = PydField(default=None, description="Метка пользователя для возможности авторизации в системе")
    active: bool | None = PydField(default=None, description="Метка пользователя для выполнения действий в системе")
    language_code: str | None = PydField(default=None, description="Код языка пользователя")
    sub: str | None = PydField(default=None, description="UUID пользователя в едином профиле")
    sort_orders: list[User_SortOrder] | None = PydField(default=None, description="Сортировака выходных параметров")
    filters: list[Filter] | None = PydField(default=None, description="Дополнительные фильтры по стандартным и дополнительным полям пользователя")
    seller_barcode: str | None = PydField(default=None, description="Штрихкод продавца")
    search: str | None = PydField(default=None, description="Строка поиска по полям: first_name - имя, middle_name - отчество, last_name - фамилия, main_phone - основной телефон, phones - доп. телефон")
    internal_phone: str | None = PydField(default=None, description="Фильтр по внутреннему телефону пользователя (доступно для БД версии 365+)")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class UserImage(RegosModel):
    "Модель, описывающая изображения пользователя"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    user_id: int | None = PydField(default=None, description="Id пользователя")
    id: int | None = PydField(default=None)
    width: int | None = PydField(default=None)
    height: int | None = PydField(default=None)
    size: int | None = PydField(default=None)
    file: str | None = PydField(default=None)
    url: str | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


class UserImageDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)


class UserImageGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user_id: int | None = PydField(default=None, description="ID пользователя")
    ids: list[int] | None = PydField(default=None)
    include_data: bool | None = PydField(default=None)
    compress_data: bool | None = PydField(default=None)


class UserImageRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[UserImage] | Error | None = PydField(default=None, description="Массив результата.")


class UserPasswordChange(RegosModel):
    "входящий модель для изменения пароля пользователя"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user_id: int | None = PydField(default=None, description="ID пользователя в системе")
    new_password: str | None = PydField(default=None, description="Новый пароль пользователя в формате base64")
    new_password_confirm: str | None = PydField(default=None, description="Подтверждение нового пароля пользователя в формате base64")


class UserPhoneChangeConfirmRequest(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID пользователя")
    phone: str | None = PydField(default=None, description="Новый телефон пользователя")
    confirm_code: str | None = PydField(default=None, description="Код подтверждения")


class UserPhoneChangeRequest(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID пользователя")
    phone: str | None = PydField(default=None, description="Новый телефон пользователя")


class UserRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[User] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class User_SortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: User_SortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class User_SortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    FirstName = "FirstName"
    MiddleName = "MiddleName"
    LastName = "LastName"
    Sex = "Sex"
    DateOfBirth = "DateOfBirth"
    Address = "Address"
    MainPhone = "MainPhone"
    Phones = "Phones"
    Email = "Email"
    Description = "Description"
    Login = "Login"
    GroupName = "GroupName"
    CanAuthorize = "CanAuthorize"
    Active = "Active"
    TimeZone = "TimeZone"
    LanguageCode = "LanguageCode"
    LastUpdate = "LastUpdate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ApiResult, ColumnSortOrderDirection, Error, InsertResult, SexEnum, UpdateResult
from schemas.api.common.filter import Filter
from schemas.api.rbac.user_group import UserGroup
from schemas.api.rbac.user_permission import UserPermissionGet, UserPermissionShortRegosArrayResult
from schemas.api.references.field import FieldValue, FieldValueAdd, FieldValueEdit


UserAddGlobalRequest: TypeAlias = UserAddGlobal
UserAddGlobalResponse: TypeAlias = UserAddGlobalResposneRegosObjectResult
UserAddImageResponse: TypeAlias = UpdateResult
UserAddRequest: TypeAlias = UserAdd
UserAddResponse: TypeAlias = InsertResult
UserCheckLoginRequest: TypeAlias = UserCheckLoginIn
UserCheckLoginResponse: TypeAlias = UserCheckLoginOutRegosObjectResult
UserDeleteImageRequest: TypeAlias = UserImageDelete
UserDeleteImageResponse: TypeAlias = UpdateResult
UserDeleteRequest: TypeAlias = UserDelete
UserDeleteResponse: TypeAlias = UpdateResult
UserEditRequest: TypeAlias = UserEdit
UserEditResponse: TypeAlias = UpdateResult
UserGetImageRequest: TypeAlias = UserImageGet
UserGetImageResponse: TypeAlias = UserImageRegosArrayResult
UserGetPermissionsRequest: TypeAlias = UserPermissionGet
UserGetPermissionsResponse: TypeAlias = UserPermissionShortRegosArrayResult
UserGetRequest: TypeAlias = UserGet
UserGetResponse: TypeAlias = UserRegosOffsettedArrayResult
UserPasswordChangeRequest: TypeAlias = UserPasswordChange
UserPasswordChangeResponse: TypeAlias = UpdateResult
UserPhoneChangeConfirmResponse: TypeAlias = ApiResult
UserPhoneChangeResponse: TypeAlias = ApiResult


_MODEL_NAMES = ['User', 'UserAdd', 'UserAddGlobal', 'UserAddGlobalResposne', 'UserAddGlobalResposneRegosObjectResult', 'UserCheckLoginIn', 'UserCheckLoginOut', 'UserCheckLoginOutRegosObjectResult', 'UserDelete', 'UserEdit', 'UserGet', 'UserImage', 'UserImageDelete', 'UserImageGet', 'UserImageRegosArrayResult', 'UserPasswordChange', 'UserPhoneChangeConfirmRequest', 'UserPhoneChangeRequest', 'UserRegosOffsettedArrayResult', 'User_SortOrder']


__all__ = [
    'User',
    'UserAdd',
    'UserAddGlobal',
    'UserAddGlobalResposne',
    'UserAddGlobalResposneRegosObjectResult',
    'UserCheckLoginIn',
    'UserCheckLoginOut',
    'UserCheckLoginOutRegosObjectResult',
    'UserDelete',
    'UserEdit',
    'UserGet',
    'UserImage',
    'UserImageDelete',
    'UserImageGet',
    'UserImageRegosArrayResult',
    'UserPasswordChange',
    'UserPhoneChangeConfirmRequest',
    'UserPhoneChangeRequest',
    'UserRegosOffsettedArrayResult',
    'User_SortOrder',
    'User_SortOrderColumn',
    'UserGetPermissionsRequest',
    'UserGetPermissionsResponse',
    'UserGetRequest',
    'UserGetResponse',
    'UserAddGlobalRequest',
    'UserAddGlobalResponse',
    'UserAddRequest',
    'UserAddResponse',
    'UserEditRequest',
    'UserEditResponse',
    'UserDeleteRequest',
    'UserDeleteResponse',
    'UserCheckLoginRequest',
    'UserCheckLoginResponse',
    'UserPasswordChangeRequest',
    'UserPasswordChangeResponse',
    'UserGetImageRequest',
    'UserGetImageResponse',
    'UserAddImageResponse',
    'UserDeleteImageRequest',
    'UserDeleteImageResponse',
    'UserPhoneChangeResponse',
    'UserPhoneChangeConfirmResponse'
]
