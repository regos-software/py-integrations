"""REGOS API service for Item."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ItemService(RegosAPIService):
    PATH_GET = "Item/Get"
    PATH_GET_SHORT = "Item/GetShort"
    PATH_GET_EXT = "Item/GetExt"
    PATH_ADD = "Item/Add"
    PATH_COPY = "Item/Copy"
    PATH_EDIT = "Item/Edit"
    PATH_DELETE_MARK = "Item/DeleteMark"
    PATH_DELETE = "Item/Delete"
    PATH_CHECK_CODE = "Item/CheckCode"
    PATH_GET_CODE = "Item/GetCode"
    PATH_SEARCH = "Item/Search"
    PATH_GET_QUANTITY = "Item/GetQuantity"
    PATH_GET_QUANTITY_POS = "Item/GetQuantityPos"
    PATH_GET_CURRENT_QUANTITY = "Item/GetCurrentQuantity"
    PATH_MATCH = "Item/Match"
    PATH_IMPORT_ = "Item/Import"
    PATH_SET_ICPS = "Item/SetIcps"
    PATH_REPLACE_ICPS = "Item/ReplaceIcps"
    PATH_GET_WITHOUT_ICPS = "Item/GetWithoutICPS"
    PATH_SET_ICPS_FROM_SERVER = "Item/SetICPSFromServer"
    PATH_SET_LABELED_MARK = "Item/SetLabeledMark"
    PATH_FILL_ICPS_BY_BARCODE = "Item/FillICPSByBarcode"
    PATH_GET_PACKAGES_BY_ICPS = "Item/GetPackagesByICPS"
    PATH_GET_COMPOUND = "Item/GetCompound"
    PATH_ADD_TO_COMPOUND = "Item/AddToCompound"
    PATH_DELETE_FROM_COMPOUND = "Item/DeleteFromCompound"
    REQUEST_MODELS = {
        'add': models.ItemAdd,
        'add_to_compound': models.ItemAddToCompound,
        'check_code': models.ItemCodeCheckIn,
        'copy': models.ItemAddCopy,
        'delete': models.ItemDelete,
        'delete_from_compound': models.ItemDeleteFromCompound,
        'delete_mark': models.ItemDeleteMark,
        'edit': models.ItemEdit,
        'get': models.ItemGet,
        'get_code': models.ItemCodeGet,
        'get_compound': models.ItemCompoundGet,
        'get_current_quantity': models.ItemCurrentQuantityGet,
        'get_ext': models.ItemExtGet,
        'get_packages_by_icps': models.ItemOFDPackagesGet,
        'get_quantity': models.ItemGetQuantityIncome,
        'get_quantity_pos': models.ItemGetQuantityPosIncome,
        'get_short': models.ItemGet,
        'get_without_icps': models.GetWithoutICPSRequest,
        'import_': models.ImportItems,
        'match': models.ItemMatchingRequest,
        'replace_icps': models.ItemReplaceICPS,
        'search': models.ItemSearch,
        'set_icps': models.ItemSetICPS,
    }

    async def get(self, req: models.ItemGet | dict[str, Any]) -> models.ItemRegosOffsettedArrayResult:
        """POST Item/Get."""
        return await self._call(self.PATH_GET, req, models.ItemRegosOffsettedArrayResult)

    async def get_short(self, req: models.ItemGet | dict[str, Any]) -> models.ItemShortRegosOffsettedArrayResult:
        """POST Item/GetShort."""
        return await self._call(self.PATH_GET_SHORT, req, models.ItemShortRegosOffsettedArrayResult)

    async def get_ext(self, req: models.ItemExtGet | dict[str, Any]) -> models.ItemExtRegosOffsettedArrayResult:
        """POST Item/GetExt."""
        return await self._call(self.PATH_GET_EXT, req, models.ItemExtRegosOffsettedArrayResult)

    async def add(self, req: models.ItemAdd | dict[str, Any]) -> models.InsertResult:
        """POST Item/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def copy(self, req: models.ItemAddCopy | dict[str, Any]) -> models.InsertResult:
        """POST Item/Copy."""
        return await self._call(self.PATH_COPY, req, models.InsertResult)

    async def edit(self, req: models.ItemEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Item/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.ItemDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST Item/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.ItemDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Item/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def check_code(self, req: models.ItemCodeCheckIn | dict[str, Any]) -> models.ItemCodeCheckOutRegosObjectResult:
        """POST Item/CheckCode."""
        return await self._call(self.PATH_CHECK_CODE, req, models.ItemCodeCheckOutRegosObjectResult)

    async def get_code(self, req: models.ItemCodeGet | dict[str, Any]) -> models.ItemCodeGetRegosObjectResult:
        """POST Item/GetCode."""
        return await self._call(self.PATH_GET_CODE, req, models.ItemCodeGetRegosObjectResult)

    async def search(self, req: models.ItemSearch | dict[str, Any]) -> models.Int64ArrayRegosObjectResult:
        """POST Item/Search."""
        return await self._call(self.PATH_SEARCH, req, models.Int64ArrayRegosObjectResult)

    async def get_quantity(self, req: models.ItemGetQuantityIncome | dict[str, Any]) -> models.ItemGetQuantityOutcomeRegosArrayResult:
        """POST Item/GetQuantity."""
        return await self._call(self.PATH_GET_QUANTITY, req, models.ItemGetQuantityOutcomeRegosArrayResult)

    async def get_quantity_pos(self, req: models.ItemGetQuantityPosIncome | dict[str, Any]) -> models.ItemGetQuantityPosOutcomeRegosArrayResult:
        """POST Item/GetQuantityPos."""
        return await self._call(self.PATH_GET_QUANTITY_POS, req, models.ItemGetQuantityPosOutcomeRegosArrayResult)

    async def get_current_quantity(self, req: models.ItemCurrentQuantityGet | dict[str, Any]) -> models.ItemCurrentQuantityRegosArrayResult:
        """POST Item/GetCurrentQuantity."""
        return await self._call(self.PATH_GET_CURRENT_QUANTITY, req, models.ItemCurrentQuantityRegosArrayResult)

    async def match(self, req: models.ItemMatchingRequest | dict[str, Any]) -> models.ItemMatchingResponseArrayRegosObjectResult:
        """POST Item/Match."""
        return await self._call(self.PATH_MATCH, req, models.ItemMatchingResponseArrayRegosObjectResult)

    async def import_(self, req: models.ImportItems | dict[str, Any]) -> models.ItemImportDataResponseArrayRegosObjectResult:
        """POST Item/Import."""
        return await self._call(self.PATH_IMPORT_, req, models.ItemImportDataResponseArrayRegosObjectResult)

    async def set_icps(self, req: models.ItemSetICPS | dict[str, Any]) -> models.BooleanRegosObjectResult:
        """POST Item/SetIcps."""
        return await self._call(self.PATH_SET_ICPS, req, models.BooleanRegosObjectResult)

    async def replace_icps(self, req: models.ItemReplaceICPS | dict[str, Any]) -> models.BooleanRegosObjectResult:
        """POST Item/ReplaceIcps."""
        return await self._call(self.PATH_REPLACE_ICPS, req, models.BooleanRegosObjectResult)

    async def get_without_icps(self, req: models.GetWithoutICPSRequest | dict[str, Any]) -> models.ItemWithoutICPSShortRegosOffsettedArrayResult:
        """POST Item/GetWithoutICPS."""
        return await self._call(self.PATH_GET_WITHOUT_ICPS, req, models.ItemWithoutICPSShortRegosOffsettedArrayResult)

    async def set_icps_from_server(self, req: list[models.ItemWithoutICPSShort] | list[dict[str, Any]]) -> models.ItemWithoutICPSRegosArrayResult:
        """POST Item/SetICPSFromServer."""
        return await self._call(self.PATH_SET_ICPS_FROM_SERVER, req, models.ItemWithoutICPSRegosArrayResult)

    async def set_labeled_mark(self, body: dict[str, Any] | None = None) -> models.BooleanRegosObjectResult:
        """POST Item/SetLabeledMark."""
        return await self._call(self.PATH_SET_LABELED_MARK, body or {}, models.BooleanRegosObjectResult)

    async def fill_icps_by_barcode(self, req: list[models.ItemWithoutICPSShort] | list[dict[str, Any]]) -> models.ItemWithoutICPSRegosArrayResult:
        """POST Item/FillICPSByBarcode."""
        return await self._call(self.PATH_FILL_ICPS_BY_BARCODE, req, models.ItemWithoutICPSRegosArrayResult)

    async def get_packages_by_icps(self, req: models.ItemOFDPackagesGet | dict[str, Any]) -> models.ItemOFDPackageRegosArrayResult:
        """POST Item/GetPackagesByICPS."""
        return await self._call(self.PATH_GET_PACKAGES_BY_ICPS, req, models.ItemOFDPackageRegosArrayResult)

    async def get_compound(self, req: models.ItemCompoundGet | dict[str, Any]) -> models.ItemCompoundRegosArrayResult:
        """POST Item/GetCompound."""
        return await self._call(self.PATH_GET_COMPOUND, req, models.ItemCompoundRegosArrayResult)

    async def add_to_compound(self, req: models.ItemAddToCompound | dict[str, Any]) -> models.UpdateResult:
        """POST Item/AddToCompound."""
        return await self._call(self.PATH_ADD_TO_COMPOUND, req, models.UpdateResult)

    async def delete_from_compound(self, req: models.ItemDeleteFromCompound | dict[str, Any]) -> models.UpdateResult:
        """POST Item/DeleteFromCompound."""
        return await self._call(self.PATH_DELETE_FROM_COMPOUND, req, models.UpdateResult)

    async def import_items(self, req: Any):
        """Compatibility alias for Item/Import."""
        return await self.import_(req)

__all__ = ['ItemService']
