"""REGOS API service for User."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class UserService(RegosAPIService):
    PATH_GET_PERMISSIONS = "User/GetPermissions"
    PATH_GET = "User/Get"
    PATH_ADD_GLOBAL = "User/AddGlobal"
    PATH_ADD = "User/Add"
    PATH_EDIT = "User/Edit"
    PATH_DELETE = "User/Delete"
    PATH_CHECK_LOGIN = "User/CheckLogin"
    PATH_PASSWORD_CHANGE = "User/PasswordChange"
    PATH_GET_IMAGE = "User/GetImage"
    PATH_ADD_IMAGE = "User/AddImage"
    PATH_DELETE_IMAGE = "User/DeleteImage"
    PATH_PHONE_CHANGE = "User/PhoneChange"
    PATH_PHONE_CHANGE_CONFIRM = "User/PhoneChangeConfirm"
    REQUEST_MODELS = {
        'add': models.UserAdd,
        'add_global': models.UserAddGlobal,
        'check_login': models.UserCheckLoginIn,
        'delete': models.UserDelete,
        'delete_image': models.UserImageDelete,
        'edit': models.UserEdit,
        'get': models.UserGet,
        'get_image': models.UserImageGet,
        'get_permissions': models.UserPermissionGet,
        'password_change': models.UserPasswordChange,
        'phone_change': models.UserPhoneChangeRequest,
        'phone_change_confirm': models.UserPhoneChangeConfirmRequest,
    }

    async def get_permissions(self, req: models.UserPermissionGet | dict[str, Any]) -> models.UserPermissionShortRegosArrayResult:
        """POST User/GetPermissions."""
        return await self._call(self.PATH_GET_PERMISSIONS, req, models.UserPermissionShortRegosArrayResult)

    async def get(self, req: models.UserGet | dict[str, Any]) -> models.UserRegosOffsettedArrayResult:
        """POST User/Get."""
        return await self._call(self.PATH_GET, req, models.UserRegosOffsettedArrayResult)

    async def add_global(self, req: models.UserAddGlobal | dict[str, Any]) -> models.UserAddGlobalResposneRegosObjectResult:
        """POST User/AddGlobal."""
        return await self._call(self.PATH_ADD_GLOBAL, req, models.UserAddGlobalResposneRegosObjectResult)

    async def add(self, req: models.UserAdd | dict[str, Any]) -> models.InsertResult:
        """POST User/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.UserEdit | dict[str, Any]) -> models.UpdateResult:
        """POST User/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.UserDelete | dict[str, Any]) -> models.UpdateResult:
        """POST User/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def check_login(self, req: models.UserCheckLoginIn | dict[str, Any]) -> models.UserCheckLoginOutRegosObjectResult:
        """POST User/CheckLogin."""
        return await self._call(self.PATH_CHECK_LOGIN, req, models.UserCheckLoginOutRegosObjectResult)

    async def password_change(self, req: models.UserPasswordChange | dict[str, Any]) -> models.UpdateResult:
        """POST User/PasswordChange."""
        return await self._call(self.PATH_PASSWORD_CHANGE, req, models.UpdateResult)

    async def get_image(self, req: models.UserImageGet | dict[str, Any]) -> models.UserImageRegosArrayResult:
        """POST User/GetImage."""
        return await self._call(self.PATH_GET_IMAGE, req, models.UserImageRegosArrayResult)

    async def add_image(self, body: dict[str, Any] | None = None) -> models.UpdateResult:
        """POST User/AddImage."""
        return await self._call(self.PATH_ADD_IMAGE, body or {}, models.UpdateResult)

    async def delete_image(self, req: models.UserImageDelete | dict[str, Any]) -> models.UpdateResult:
        """POST User/DeleteImage."""
        return await self._call(self.PATH_DELETE_IMAGE, req, models.UpdateResult)

    async def phone_change(self, req: models.UserPhoneChangeRequest | dict[str, Any]) -> models.ApiResult:
        """POST User/PhoneChange."""
        return await self._call(self.PATH_PHONE_CHANGE, req, models.ApiResult)

    async def phone_change_confirm(self, req: models.UserPhoneChangeConfirmRequest | dict[str, Any]) -> models.ApiResult:
        """POST User/PhoneChangeConfirm."""
        return await self._call(self.PATH_PHONE_CHANGE_CONFIRM, req, models.ApiResult)

__all__ = ['UserService']
