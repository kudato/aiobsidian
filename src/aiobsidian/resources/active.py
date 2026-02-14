from .._base_resource import BaseResource
from .._types import ContentType, PatchOperation, TargetType
from ..models.vault import DocumentMap, NoteJson


class ActiveFileResource(BaseResource):
    async def get(
        self,
        *,
        content_type: ContentType = ContentType.MARKDOWN,
    ) -> str | NoteJson | DocumentMap:
        return await self._get_content("/active/", content_type)

    async def update(self, content: str) -> None:
        await self._client.request(
            "PUT",
            "/active/",
            content=content,
            headers={"Content-Type": ContentType.MARKDOWN},
        )

    async def append(self, content: str) -> None:
        await self._append_content("/active/", content)

    async def patch(
        self,
        content: str,
        *,
        operation: PatchOperation,
        target_type: TargetType,
        target: str,
        target_delimiter: str = "::",
    ) -> None:
        await self._patch_content(
            "/active/",
            content,
            operation=operation,
            target_type=target_type,
            target=target,
            target_delimiter=target_delimiter,
        )

    async def delete(self) -> None:
        await self._client.request("DELETE", "/active/")

    async def get_json(self) -> NoteJson:
        result = await self.get(content_type=ContentType.NOTE_JSON)
        assert isinstance(result, NoteJson)
        return result

    async def get_document_map(self) -> DocumentMap:
        result = await self.get(content_type=ContentType.DOCUMENT_MAP)
        assert isinstance(result, DocumentMap)
        return result
