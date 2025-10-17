from typing import List, Iterable
from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.docs.cheque_payment import DocChequePaymentGetRequest, DocChequePayment

logger = setup_logger("docs.RetailPayment")


class DocChequePaymentService:
    PATH_GET = "DocChequePayment/Get"

    def __init__(self, api):
        self.api = api

    async def get(
        self, req: DocChequePaymentGetRequest
    ) -> APIBaseResponse[List[DocChequePayment]]:
        resp = await self.api.call(
            self.PATH_GET, req, APIBaseResponse[List[DocChequePayment]]
        )
        return resp

    async def get_by_uuids(
        self, uuids: Iterable
    ) -> APIBaseResponse[List[DocChequePayment]]:
        return await self.get(DocChequePaymentGetRequest(uuids=list(uuids)))

    async def get_by_doc_sale_uuid(
        self, doc_sale_uuid: str
    ) -> APIBaseResponse[List[DocChequePayment]]:
        return await self.get(DocChequePaymentGetRequest(doc_sale_uuid=doc_sale_uuid))
