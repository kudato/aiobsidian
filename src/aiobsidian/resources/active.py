from .._base_resource import BaseResource
from .._types import ContentType, PatchOperation, TargetType
from ..models.vault import DocumentMap, NoteJson


class ActiveFileResource(BaseResource):
    async def get(
        self,
        *,
        content_type: ContentType = ContentType.MARKDOWN,
    ) -> str | NoteJson | DocumentMap:
        response = await self._client.request(
            "GET",
            "/active/",
            headers={"Accept": content_type.value},
        )
        if content_type == ContentType.NOTE_JSON:
            return NoteJson.model_validate(response.json())
        if content_type == ContentType.DOCUMENT_MAP:
            return DocumentMap.model_validate(response.json())
        return response.text

    async def update(self, content: str) -> None:
        await self._client.request(
            "PUT",
            "/active/",
            content=content,
            headers={"Content-Type": ContentType.MARKDOWN},
        )

    async def append(self, content: str) -> None:
        await self._client.request(
            "POST",
            "/active/",
            content=content,
            headers={"Content-Type": ContentType.MARKDOWN},
        )

    async def patch(
        self,
        content: str,
        *,
        operation: PatchOperation,
        target_type: TargetType,
        target: str,
        target_delimiter: str = "::",
    ) -> None:
        headers: dict[str, str] = {
            "Content-Type": ContentType.MARKDOWN,
            "Operation": operation.value,
            "Target-Type": target_type.value,
            "Target": target,
            "Target-Delimiter": target_delimiter,
        }
        if target_type == TargetType.FRONTMATTER:
            headers["Content-Type"] = "application/json"

        await self._client.request(
            "PATCH",
            "/active/",
            content=content,
            headers=headers,
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
