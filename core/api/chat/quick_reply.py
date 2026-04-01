"""Chat quick reply service."""

from schemas.api.chat.quick_reply import (
    QuickReplyAddRequest,
    QuickReplyAddResponse,
    QuickReplyDeleteRequest,
    QuickReplyDeleteResponse,
    QuickReplyGetRequest,
    QuickReplyGetResponse,
)


class QuickReplyService:
    PATH_GET = "QuickReply/Get"
    PATH_ADD = "QuickReply/Add"
    PATH_DELETE = "QuickReply/Delete"

    def __init__(self, api):
        self.api = api

    async def get(self, req: QuickReplyGetRequest) -> QuickReplyGetResponse:
        return await self.api.call(self.PATH_GET, req, QuickReplyGetResponse)

    async def add(self, req: QuickReplyAddRequest) -> QuickReplyAddResponse:
        return await self.api.call(self.PATH_ADD, req, QuickReplyAddResponse)

    async def delete(self, req: QuickReplyDeleteRequest) -> QuickReplyDeleteResponse:
        return await self.api.call(self.PATH_DELETE, req, QuickReplyDeleteResponse)
