"""REGOS API service for PromoBonus."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PromoBonusService(RegosAPIService):
    PATH_CREATE_PAYMENT = "PromoBonus/CreatePayment"
    PATH_PERFORM_PAYMENT = "PromoBonus/PerformPayment"
    PATH_CREATE_ENROLLMENT = "PromoBonus/CreateEnrollment"
    PATH_PERFORM_ENROLLMENT = "PromoBonus/PerformEnrollment"
    PATH_CANCEL_PAYMENT = "PromoBonus/CancelPayment"
    PATH_CREATE_MANUAL_INCOME_OPERATION = "PromoBonus/CreateManualIncomeOperation"
    PATH_CREATE_MANUAL_OUTCOME_OPERATION = "PromoBonus/CreateManualOutcomeOperation"
    PATH_GET = "PromoBonus/Get"
    REQUEST_MODELS = {
        'cancel_payment': models.PromoBonusCancelPayment,
        'create_enrollment': models.PromoBonusCreateEnrollment,
        'create_manual_income_operation': models.PromoBonusCreateManualOperation,
        'create_manual_outcome_operation': models.PromoBonusCreateManualOperation,
        'create_payment': models.PromoBonusCreatePayment,
        'get': models.PromoBonusGet,
        'perform_enrollment': models.PromoBonusPerformEnrollment,
        'perform_payment': models.PromoBonusPerformPayment,
    }

    async def create_payment(self, req: models.PromoBonusCreatePayment | dict[str, Any]) -> models.Insert_uuid_Result:
        """POST PromoBonus/CreatePayment."""
        return await self._call(self.PATH_CREATE_PAYMENT, req, models.Insert_uuid_Result)

    async def perform_payment(self, req: models.PromoBonusPerformPayment | dict[str, Any]) -> models.UpdateResult:
        """POST PromoBonus/PerformPayment."""
        return await self._call(self.PATH_PERFORM_PAYMENT, req, models.UpdateResult)

    async def create_enrollment(self, req: models.PromoBonusCreateEnrollment | dict[str, Any]) -> models.Insert_uuid_Result:
        """POST PromoBonus/CreateEnrollment."""
        return await self._call(self.PATH_CREATE_ENROLLMENT, req, models.Insert_uuid_Result)

    async def perform_enrollment(self, req: models.PromoBonusPerformEnrollment | dict[str, Any]) -> models.UpdateResult:
        """POST PromoBonus/PerformEnrollment."""
        return await self._call(self.PATH_PERFORM_ENROLLMENT, req, models.UpdateResult)

    async def cancel_payment(self, req: models.PromoBonusCancelPayment | dict[str, Any]) -> models.UpdateResult:
        """POST PromoBonus/CancelPayment."""
        return await self._call(self.PATH_CANCEL_PAYMENT, req, models.UpdateResult)

    async def create_manual_income_operation(self, req: models.PromoBonusCreateManualOperation | dict[str, Any]) -> models.UpdateResult:
        """POST PromoBonus/CreateManualIncomeOperation."""
        return await self._call(self.PATH_CREATE_MANUAL_INCOME_OPERATION, req, models.UpdateResult)

    async def create_manual_outcome_operation(self, req: models.PromoBonusCreateManualOperation | dict[str, Any]) -> models.UpdateResult:
        """POST PromoBonus/CreateManualOutcomeOperation."""
        return await self._call(self.PATH_CREATE_MANUAL_OUTCOME_OPERATION, req, models.UpdateResult)

    async def get(self, req: models.PromoBonusGet | dict[str, Any]) -> models.RetailCardOperationRegosObjectResult:
        """POST PromoBonus/Get."""
        return await self._call(self.PATH_GET, req, models.RetailCardOperationRegosObjectResult)

__all__ = ['PromoBonusService']
