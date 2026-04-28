"""File service."""

from schemas.api.files.file import FileGetRequest, FileGetResponse


class FileService:
    PATH_GET = "File/Get"

    def __init__(self, api):
        self.api = api

    async def get(self, req: FileGetRequest) -> FileGetResponse:
        return await self.api.call(self.PATH_GET, req, FileGetResponse)
