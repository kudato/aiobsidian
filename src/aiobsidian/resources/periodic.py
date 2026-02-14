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
        return await self._get_content(f"/periodic/{period}/", content_type)

    async def update(self, period: Period, content: str) -> None:
        await self._client.request(
            "PUT",
            f"/periodic/{period}/",
            content=content,
            headers={"Content-Type": ContentType.MARKDOWN},
        )

    async def append(self, period: Period, content: str) -> None:
        await self._append_content(f"/periodic/{period}/", content)

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
        await self._patch_content(
            f"/periodic/{period}/",
            content,
            operation=operation,
            target_type=target_type,
            target=target,
            target_delimiter=target_delimiter,
        )

    async def delete(self, period: Period) -> None:
        await self._client.request("DELETE", f"/periodic/{period}/")
