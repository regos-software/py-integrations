"""REGOS API service for ReportRequest."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ReportRequestService(RegosAPIService):
    PATH_GET = "ReportRequest/Get"
    PATH_REPORT0003 = "ReportRequest/Report0003"
    PATH_REPORT0005 = "ReportRequest/Report0005"
    PATH_REPORT0006 = "ReportRequest/Report0006"
    PATH_REPORT0007 = "ReportRequest/Report0007"
    PATH_REPORT0009 = "ReportRequest/Report0009"
    PATH_REPORT0011 = "ReportRequest/Report0011"
    PATH_REPORT0016 = "ReportRequest/Report0016"
    PATH_REPORT0017 = "ReportRequest/Report0017"
    PATH_REPORT0018 = "ReportRequest/Report0018"
    PATH_REPORT0020 = "ReportRequest/Report0020"
    PATH_REPORT0021 = "ReportRequest/Report0021"
    PATH_REPORT0022 = "ReportRequest/Report0022"
    PATH_REPORT0023 = "ReportRequest/Report0023"
    PATH_REPORT0024 = "ReportRequest/Report0024"
    PATH_REPORT0025 = "ReportRequest/Report0025"
    PATH_REPORT0026 = "ReportRequest/Report0026"
    REQUEST_MODELS = {
        'get': models.ReportRequestGet,
        'report0003': models.Report0003Request,
        'report0005': models.Report0005Request,
        'report0006': models.Report0006Request,
        'report0007': models.Report0007Request,
        'report0009': models.Report0009Request,
        'report0011': models.Report0011_Request_Model,
        'report0016': models.Report0016Request,
        'report0017': models.Report0017Request,
        'report0018': models.Report0018Request,
        'report0020': models.Report0020Request,
        'report0021': models.Report0021Request,
        'report0022': models.Report0022Request,
        'report0023': models.Report0023Request,
        'report0024': models.Report0024Request,
        'report0025': models.Report0025_Request,
        'report0026': models.Report0026_Request,
    }

    async def get(self, req: models.ReportRequestGet | dict[str, Any]) -> models.ReportRequestArrayRegosObjectResult:
        """POST ReportRequest/Get."""
        return await self._call(self.PATH_GET, req, models.ReportRequestArrayRegosObjectResult)

    async def report0003(self, req: models.Report0003Request | dict[str, Any]) -> models.SingleObjectResult:
        """POST ReportRequest/Report0003."""
        return await self._call(self.PATH_REPORT0003, req, models.SingleObjectResult)

    async def report0005(self, req: models.Report0005Request | dict[str, Any]) -> models.SingleObjectResult:
        """POST ReportRequest/Report0005."""
        return await self._call(self.PATH_REPORT0005, req, models.SingleObjectResult)

    async def report0006(self, req: models.Report0006Request | dict[str, Any]) -> models.SingleObjectResult:
        """POST ReportRequest/Report0006."""
        return await self._call(self.PATH_REPORT0006, req, models.SingleObjectResult)

    async def report0007(self, req: models.Report0007Request | dict[str, Any]) -> models.SingleObjectResult:
        """POST ReportRequest/Report0007."""
        return await self._call(self.PATH_REPORT0007, req, models.SingleObjectResult)

    async def report0009(self, req: models.Report0009Request | dict[str, Any]) -> models.SingleObjectResult:
        """POST ReportRequest/Report0009."""
        return await self._call(self.PATH_REPORT0009, req, models.SingleObjectResult)

    async def report0011(self, req: models.Report0011_Request_Model | dict[str, Any]) -> models.SingleObjectResult:
        """POST ReportRequest/Report0011."""
        return await self._call(self.PATH_REPORT0011, req, models.SingleObjectResult)

    async def report0016(self, req: models.Report0016Request | dict[str, Any]) -> models.SingleObjectResult:
        """POST ReportRequest/Report0016."""
        return await self._call(self.PATH_REPORT0016, req, models.SingleObjectResult)

    async def report0017(self, req: models.Report0017Request | dict[str, Any]) -> models.SingleObjectResult:
        """POST ReportRequest/Report0017."""
        return await self._call(self.PATH_REPORT0017, req, models.SingleObjectResult)

    async def report0018(self, req: models.Report0018Request | dict[str, Any]) -> models.SingleObjectResult:
        """POST ReportRequest/Report0018."""
        return await self._call(self.PATH_REPORT0018, req, models.SingleObjectResult)

    async def report0020(self, req: models.Report0020Request | dict[str, Any]) -> models.SingleObjectResult:
        """POST ReportRequest/Report0020."""
        return await self._call(self.PATH_REPORT0020, req, models.SingleObjectResult)

    async def report0021(self, req: models.Report0021Request | dict[str, Any]) -> models.SingleObjectResult:
        """POST ReportRequest/Report0021."""
        return await self._call(self.PATH_REPORT0021, req, models.SingleObjectResult)

    async def report0022(self, req: models.Report0022Request | dict[str, Any]) -> models.SingleObjectResult:
        """POST ReportRequest/Report0022."""
        return await self._call(self.PATH_REPORT0022, req, models.SingleObjectResult)

    async def report0023(self, req: models.Report0023Request | dict[str, Any]) -> models.SingleObjectResult:
        """POST ReportRequest/Report0023."""
        return await self._call(self.PATH_REPORT0023, req, models.SingleObjectResult)

    async def report0024(self, req: models.Report0024Request | dict[str, Any]) -> models.SingleObjectResult:
        """POST ReportRequest/Report0024."""
        return await self._call(self.PATH_REPORT0024, req, models.SingleObjectResult)

    async def report0025(self, req: models.Report0025_Request | dict[str, Any]) -> models.SingleObjectResult:
        """POST ReportRequest/Report0025."""
        return await self._call(self.PATH_REPORT0025, req, models.SingleObjectResult)

    async def report0026(self, req: models.Report0026_Request | dict[str, Any]) -> models.SingleObjectResult:
        """POST ReportRequest/Report0026."""
        return await self._call(self.PATH_REPORT0026, req, models.SingleObjectResult)

__all__ = ['ReportRequestService']
