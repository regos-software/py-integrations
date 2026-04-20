"""Chat message service."""

from __future__ import annotations

from typing import Optional

from schemas.api.chat.chat_message import (
    ChatMessageAddFileRequest,
    ChatMessageAddFileResponse,
    ChatMessageAddRequest,
    ChatMessageAddResponse,
    ChatMessageDeleteRequest,
    ChatMessageDeleteResponse,
    ChatMessageEditRequest,
    ChatMessageEditResponse,
    ChatMessageGetRequest,
    ChatMessageGetResponse,
    ChatMessageMarkReadRequest,
    ChatMessageMarkReadResponse,
    ChatMessageMarkSentRequest,
    ChatMessageMarkSentResponse,
    ChatMessageSearchRequest,
    ChatMessageSearchResponse,
    ChatMessageSuggestRequest,
    ChatMessageSuggestResponse,
    ChatMessageWritingRequest,
    ChatMessageWritingResponse,
)


class ChatMessageService:
    PATH_GET = "ChatMessage/Get"
    PATH_ADD = "ChatMessage/Add"
    PATH_DELETE = "ChatMessage/Delete"
    PATH_EDIT = "ChatMessage/Edit"
    PATH_SEARCH = "ChatMessage/Search"
    PATH_WRITING = "ChatMessage/Writing"
    PATH_ADD_FILE = "ChatMessage/AddFile"
    PATH_SUGGEST = "ChatMessage/Suggest"
    PATH_MARK_READ = "ChatMessage/MarkRead"
    PATH_MARK_SENT = "ChatMessage/MarkSent"

    def __init__(self, api):
        self.api = api

    async def get(self, req: ChatMessageGetRequest) -> ChatMessageGetResponse:
        return await self.api.call(self.PATH_GET, req, ChatMessageGetResponse)

    async def add(self, req: ChatMessageAddRequest) -> ChatMessageAddResponse:
        return await self.api.call(self.PATH_ADD, req, ChatMessageAddResponse)

    async def delete(self, req: ChatMessageDeleteRequest) -> ChatMessageDeleteResponse:
        return await self.api.call(self.PATH_DELETE, req, ChatMessageDeleteResponse)

    async def edit(self, req: ChatMessageEditRequest) -> ChatMessageEditResponse:
        return await self.api.call(self.PATH_EDIT, req, ChatMessageEditResponse)

    async def search(self, req: ChatMessageSearchRequest) -> ChatMessageSearchResponse:
        return await self.api.call(self.PATH_SEARCH, req, ChatMessageSearchResponse)

    async def writing(self, req: ChatMessageWritingRequest) -> ChatMessageWritingResponse:
        return await self.api.call(self.PATH_WRITING, req, ChatMessageWritingResponse)

    async def add_file(
        self, req: ChatMessageAddFileRequest
    ) -> ChatMessageAddFileResponse:
        return await self.api.call(self.PATH_ADD_FILE, req, ChatMessageAddFileResponse)

    async def add_file_multipart(
        self,
        *,
        chat_id: str,
        file_name: str,
        file_bytes: bytes,
        name: Optional[str] = None,
        extension: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> ChatMessageAddFileResponse:
        data = {
            "chat_id": chat_id,
            "name": name,
            "extension": extension,
        }
        files = {
            "file": (
                file_name,
                file_bytes,
                content_type or "application/octet-stream",
            )
        }
        return await self.api.call_multipart(
            self.PATH_ADD_FILE,
            data,
            files,
            ChatMessageAddFileResponse,
        )

    async def suggest(self, req: ChatMessageSuggestRequest) -> ChatMessageSuggestResponse:
        return await self.api.call(self.PATH_SUGGEST, req, ChatMessageSuggestResponse)

    async def mark_read(
        self, req: ChatMessageMarkReadRequest
    ) -> ChatMessageMarkReadResponse:
        return await self.api.call(self.PATH_MARK_READ, req, ChatMessageMarkReadResponse)

    async def mark_sent(
        self, req: ChatMessageMarkSentRequest
    ) -> ChatMessageMarkSentResponse:
        return await self.api.call(self.PATH_MARK_SENT, req, ChatMessageMarkSentResponse)
