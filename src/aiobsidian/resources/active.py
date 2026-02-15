from typing import Literal, overload

from .._base_resource import ContentResource
from .._types import ContentType, PatchOperation, TargetType
from ..models.vault import DocumentMap, NoteJson


class ActiveFileResource(ContentResource):
    """Operations on the currently active (open) file in Obsidian."""

    _BASE_URL = "/active/"

    @overload
    async def get(
        self,
        *,
        content_type: Literal[ContentType.MARKDOWN] = ...,
    ) -> str: ...

    @overload
    async def get(
        self,
        *,
        content_type: Literal[ContentType.NOTE_JSON],
    ) -> NoteJson: ...

    @overload
    async def get(
        self,
        *,
        content_type: Literal[ContentType.DOCUMENT_MAP],
    ) -> DocumentMap: ...

    async def get(
        self,
        *,
        content_type: ContentType = ContentType.MARKDOWN,
    ) -> str | NoteJson | DocumentMap:
        """Get the content of the active file.

        Args:
            content_type: Desired response format. Use
                `ContentType.MARKDOWN` for raw text,
                `ContentType.NOTE_JSON` for structured JSON, or
                `ContentType.DOCUMENT_MAP` for headings/blocks.

        Returns:
            File content as `str`, `NoteJson`, or `DocumentMap`
            depending on the requested content type.
        """
        return await self._get_content(self._BASE_URL, content_type)

    async def update(self, content: str) -> None:
        """Replace the entire content of the active file.

        Args:
            content: New Markdown content for the file.
        """
        await self._client.request(
            "PUT",
            self._BASE_URL,
            content=content,
            headers={"Content-Type": ContentType.MARKDOWN},
        )

    async def append(self, content: str) -> None:
        """Append content to the end of the active file.

        Args:
            content: Markdown content to append.
        """
        await self._append_content(self._BASE_URL, content)

    async def patch(
        self,
        content: str,
        *,
        operation: PatchOperation,
        target_type: TargetType,
        target: str,
        target_delimiter: str = "::",
    ) -> None:
        """Patch a specific section of the active file.

        Args:
            content: Content to insert or replace.
            operation: How to apply the content (`append`, `prepend`,
                or `replace`).
            target_type: What to target (`heading`, `block`, or
                `frontmatter`).
            target: The target identifier.
            target_delimiter: Delimiter for nested targets.
        """
        await self._patch_content(
            self._BASE_URL,
            content,
            operation=operation,
            target_type=target_type,
            target=target,
            target_delimiter=target_delimiter,
        )

    async def delete(self) -> None:
        """Delete the currently active file."""
        await self._client.request("DELETE", self._BASE_URL)
