from typing import List, Iterable
from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.docs.retail_payment import DocRetailPaymentGetRequest, DocRetailPayment

logger = setup_logger("docs.RetailPayment")


class DocRetailPaymentService:
    PATH_GET = "DocRetailPayment/Get"

    def __init__(self, api):
        self.api = api

    async def get(self, req: DocRetailPaymentGetRequest) -> List[DocRetailPayment]:
        resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            return []
        return [DocRetailPayment.model_validate(x) for x in resp.result]

    async def get_by_uuids(self, uuids: Iterable) -> List[DocRetailPayment]:
        return await self.get(DocRetailPaymentGetRequest(uuids=list(uuids)))

    async def get_by_doc_sale_uuid(self, doc_sale_uuid: str) -> List[DocRetailPayment]:
        return await self.get(DocRetailPaymentGetRequest(doc_sale_uuid=doc_sale_uuid))
