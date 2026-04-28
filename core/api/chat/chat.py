"""Chat service."""

from schemas.api.chat.chat import (
    ChatAddBotRequest,
    ChatAddBotResponse,
    ChatAddParticipantRequest,
    ChatAddParticipantResponse,
    ChatAddRequest,
    ChatAddResponse,
    ChatEditRequest,
    ChatEditResponse,
    ChatGetRequest,
    ChatGetResponse,
    ChatRemoveParticipantsRequest,
    ChatRemoveParticipantsResponse,
    ChatSetParticipantsRequest,
    ChatSetParticipantsResponse,
)


class ChatService:
    PATH_GET = "Chat/Get"
    PATH_ADD = "Chat/Add"
    PATH_EDIT = "Chat/Edit"
    PATH_REMOVE_PARTICIPANTS = "Chat/RemoveParticipants"
    PATH_SET_PARTICIPANTS = "Chat/SetParticipants"
    PATH_ADD_PARTICIPANT = "Chat/AddParticipant"
    PATH_ADD_BOT = "Chat/AddBot"

    def __init__(self, api):
        self.api = api

    async def get(self, req: ChatGetRequest) -> ChatGetResponse:
        return await self.api.call(self.PATH_GET, req, ChatGetResponse)

    async def add(self, req: ChatAddRequest) -> ChatAddResponse:
        return await self.api.call(self.PATH_ADD, req, ChatAddResponse)

    async def edit(self, req: ChatEditRequest) -> ChatEditResponse:
        return await self.api.call(self.PATH_EDIT, req, ChatEditResponse)

    async def remove_participants(
        self, req: ChatRemoveParticipantsRequest
    ) -> ChatRemoveParticipantsResponse:
        return await self.api.call(
            self.PATH_REMOVE_PARTICIPANTS,
            req,
            ChatRemoveParticipantsResponse,
        )

    async def set_participants(
        self, req: ChatSetParticipantsRequest
    ) -> ChatSetParticipantsResponse:
        return await self.api.call(
            self.PATH_SET_PARTICIPANTS,
            req,
            ChatSetParticipantsResponse,
        )

    async def add_participant(
        self, req: ChatAddParticipantRequest
    ) -> ChatAddParticipantResponse:
        return await self.api.call(
            self.PATH_ADD_PARTICIPANT,
            req,
            ChatAddParticipantResponse,
        )

    async def add_bot(self, req: ChatAddBotRequest) -> ChatAddBotResponse:
        return await self.api.call(self.PATH_ADD_BOT, req, ChatAddBotResponse)
