from .._base_resource import BaseResource
from .._types import ContentType, PatchOperation, Period, TargetType
from ..models.vault import DocumentMap, NoteJson


class PeriodicNotesResource(BaseResource):
    async def get(
        self,
        period: Period,
        *,
        content_type: ContentType = ContentType.MARKDOWN,
    ) -> str | NoteJson | DocumentMap:
        response = await self._client.request(
            "GET",
            f"/periodic/{period}/",
            headers={"Accept": content_type.value},
        )
        if content_type == ContentType.NOTE_JSON:
            return NoteJson.model_validate(response.json())
        if content_type == ContentType.DOCUMENT_MAP:
            return DocumentMap.model_validate(response.json())
        return response.text

    async def update(self, period: Period, content: str) -> None:
        await self._client.request(
            "PUT",
            f"/periodic/{period}/",
            content=content,
            headers={"Content-Type": ContentType.MARKDOWN},
        )

    async def append(self, period: Period, content: str) -> None:
        await self._client.request(
            "POST",
            f"/periodic/{period}/",
            content=content,
            headers={"Content-Type": ContentType.MARKDOWN},
        )

    async def patch(
        self,
        period: Period,
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
            f"/periodic/{period}/",
            content=content,
            headers=headers,
        )

    async def delete(self, period: Period) -> None:
        await self._client.request("DELETE", f"/periodic/{period}/")
