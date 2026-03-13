"""Chat message service."""

from schemas.api.chat.chat_message import (
    ChatMessageAddFileRequest,
    ChatMessageAddFileResponse,
    ChatMessageAddRequest,
    ChatMessageAddResponse,
    ChatMessageGetRequest,
    ChatMessageGetResponse,
    ChatMessageMarkSentRequest,
    ChatMessageMarkSentResponse,
)


class ChatMessageService:
    PATH_GET = "ChatMessage/Get"
    PATH_ADD = "ChatMessage/Add"
    PATH_ADD_FILE = "ChatMessage/AddFile"
    PATH_MARK_SENT = "ChatMessage/MarkSent"

    def __init__(self, api):
        self.api = api

    async def get(self, req: ChatMessageGetRequest) -> ChatMessageGetResponse:
        return await self.api.call(self.PATH_GET, req, ChatMessageGetResponse)

    async def add(self, req: ChatMessageAddRequest) -> ChatMessageAddResponse:
        return await self.api.call(self.PATH_ADD, req, ChatMessageAddResponse)

    async def add_file(
        self, req: ChatMessageAddFileRequest
    ) -> ChatMessageAddFileResponse:
        return await self.api.call(self.PATH_ADD_FILE, req, ChatMessageAddFileResponse)

    async def mark_sent(
        self, req: ChatMessageMarkSentRequest
    ) -> ChatMessageMarkSentResponse:
        return await self.api.call(self.PATH_MARK_SENT, req, ChatMessageMarkSentResponse)
