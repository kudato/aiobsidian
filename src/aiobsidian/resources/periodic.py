from typing import Literal, overload

from .._base_resource import ContentResource
from .._types import ContentType, PatchOperation, Period, TargetType
from ..models.vault import DocumentMap, NoteJson


class PeriodicNotesResource(ContentResource):
    """Operations on periodic notes (daily, weekly, monthly, quarterly, yearly)."""

    _BASE_URL = "/periodic"

    @overload
    async def get(
        self,
        period: Period,
        *,
        content_type: Literal[ContentType.MARKDOWN] = ...,
    ) -> str: ...

    @overload
    async def get(
        self,
        period: Period,
        *,
        content_type: Literal[ContentType.NOTE_JSON],
    ) -> NoteJson: ...

    @overload
    async def get(
        self,
        period: Period,
        *,
        content_type: Literal[ContentType.DOCUMENT_MAP],
    ) -> DocumentMap: ...

    async def get(
        self,
        period: Period,
        *,
        content_type: ContentType = ContentType.MARKDOWN,
    ) -> str | NoteJson | DocumentMap:
        """Get the content of a periodic note.

        Args:
            period: The time period (e.g. `Period.DAILY`).
            content_type: Desired response format.

        Returns:
            Note content as `str`, `NoteJson`, or `DocumentMap`
            depending on the requested content type.
        """
        return await self._get_content(f"{self._BASE_URL}/{period}/", content_type)

    async def update(self, period: Period, content: str) -> None:
        """Replace the entire content of a periodic note.

        If the note does not exist, it will be created.

        Args:
            period: The time period.
            content: New Markdown content for the note.
        """
        await self._client.request(
            "PUT",
            f"{self._BASE_URL}/{period}/",
            content=content,
            headers={"Content-Type": ContentType.MARKDOWN},
        )

    async def append(self, period: Period, content: str) -> None:
        """Append content to the end of a periodic note.

        Args:
            period: The time period.
            content: Markdown content to append.
        """
        await self._append_content(f"{self._BASE_URL}/{period}/", content)

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
        """Patch a specific section of a periodic note.

        Args:
            period: The time period.
            content: Content to insert or replace.
            operation: How to apply the content (`append`, `prepend`,
                or `replace`).
            target_type: What to target (`heading`, `block`, or
                `frontmatter`).
            target: The target identifier.
            target_delimiter: Delimiter for nested targets.
        """
        await self._patch_content(
            f"{self._BASE_URL}/{period}/",
            content,
            operation=operation,
            target_type=target_type,
            target=target,
            target_delimiter=target_delimiter,
        )

    async def delete(self, period: Period) -> None:
        """Delete a periodic note.

        Args:
            period: The time period of the note to delete.
        """
        await self._client.request("DELETE", f"{self._BASE_URL}/{period}/")
