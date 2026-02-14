from .._base_resource import BaseResource
from .._types import ContentType, PatchOperation, TargetType
from ..models.vault import DocumentMap, NoteJson, VaultDirectory


class VaultResource(BaseResource):
    async def get(
        self,
        path: str,
        *,
        content_type: ContentType = ContentType.MARKDOWN,
    ) -> str | NoteJson | DocumentMap:
        response = await self._client.request(
            "GET",
            f"/vault/{path}",
            headers={"Accept": content_type.value},
        )
        if content_type == ContentType.NOTE_JSON:
            return NoteJson.model_validate(response.json())
        if content_type == ContentType.DOCUMENT_MAP:
            return DocumentMap.model_validate(response.json())
        return response.text

    async def create(self, path: str, content: str) -> None:
        await self._client.request(
            "PUT",
            f"/vault/{path}",
            content=content,
            headers={"Content-Type": ContentType.MARKDOWN},
        )

    async def append(self, path: str, content: str) -> None:
        await self._client.request(
            "POST",
            f"/vault/{path}",
            content=content,
            headers={"Content-Type": ContentType.MARKDOWN},
        )

    async def patch(
        self,
        path: str,
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
            f"/vault/{path}",
            content=content,
            headers=headers,
        )

    async def delete(self, path: str) -> None:
        await self._client.request("DELETE", f"/vault/{path}")

    async def list(self, path: str = "") -> VaultDirectory:
        trailing = f"{path}/" if path else ""
        response = await self._client.request("GET", f"/vault/{trailing}")
        return VaultDirectory.model_validate(response.json())

    async def get_json(self, path: str) -> NoteJson:
        result = await self.get(path, content_type=ContentType.NOTE_JSON)
        assert isinstance(result, NoteJson)
        return result

    async def get_document_map(self, path: str) -> DocumentMap:
        result = await self.get(path, content_type=ContentType.DOCUMENT_MAP)
        assert isinstance(result, DocumentMap)
        return result
