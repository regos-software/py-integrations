"""REGOS API service for Report."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ReportService(RegosAPIService):
    PATH_GET = "Report/Get"
    PATH_GET_REQUEST = "Report/GetRequest"
    PATH_ADD_REQUEST = "Report/AddRequest"
    PATH_GET_PREPARED = "Report/GetPrepared"
    PATH_REMOVE_PREPARED = "Report/RemovePrepared"
    PATH_SET_PREPARED = "Report/SetPrepared"
    PATH_SET_ERROR = "Report/SetError"
    REQUEST_MODELS = {
        'add_request': models.ReportAddRequest,
        'get': models.ReportGet,
        'get_prepared': models.ReportPreparedGet,
        'get_request': models.ReportRequestGet,
        'remove_prepared': models.ReportPreparedRemove,
        'set_error': models.ReportSetError,
        'set_prepared': models.ReportSetPrepared,
    }

    async def get(self, req: models.ReportGet | dict[str, Any]) -> models.ReportArrayRegosObjectResult:
        """POST Report/Get."""
        return await self._call(self.PATH_GET, req, models.ReportArrayRegosObjectResult)

    async def get_request(self, req: models.ReportRequestGet | dict[str, Any]) -> models.ReportRequestArrayRegosObjectResult:
        """POST Report/GetRequest."""
        return await self._call(self.PATH_GET_REQUEST, req, models.ReportRequestArrayRegosObjectResult)

    async def add_request(self, req: models.ReportAddRequest | dict[str, Any]) -> models.Insert_uuid_Result:
        """POST Report/AddRequest."""
        return await self._call(self.PATH_ADD_REQUEST, req, models.Insert_uuid_Result)

    async def get_prepared(self, req: models.ReportPreparedGet | dict[str, Any]) -> models.ReportPreparedArrayRegosObjectResult:
        """POST Report/GetPrepared."""
        return await self._call(self.PATH_GET_PREPARED, req, models.ReportPreparedArrayRegosObjectResult)

    async def remove_prepared(self, req: models.ReportPreparedRemove | dict[str, Any]) -> models.UpdateResult:
        """POST Report/RemovePrepared."""
        return await self._call(self.PATH_REMOVE_PREPARED, req, models.UpdateResult)

    async def set_prepared(self, req: models.ReportSetPrepared | dict[str, Any]) -> models.UpdateResult:
        """POST Report/SetPrepared."""
        return await self._call(self.PATH_SET_PREPARED, req, models.UpdateResult)

    async def set_error(self, req: models.ReportSetError | dict[str, Any]) -> models.UpdateResult:
        """POST Report/SetError."""
        return await self._call(self.PATH_SET_ERROR, req, models.UpdateResult)

__all__ = ['ReportService']
