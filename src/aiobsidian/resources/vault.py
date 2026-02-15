from typing import Literal, overload

from .._base_resource import ContentResource
from .._types import ContentType, PatchOperation, TargetType
from ..models.vault import DocumentMap, NoteJson, VaultDirectory


class VaultResource(ContentResource):
    """Operations on files and directories in the vault."""

    _BASE_URL = "/vault"

    @overload
    async def get(
        self,
        path: str,
        *,
        content_type: Literal[ContentType.MARKDOWN] = ...,
    ) -> str: ...

    @overload
    async def get(
        self,
        path: str,
        *,
        content_type: Literal[ContentType.NOTE_JSON],
    ) -> NoteJson: ...

    @overload
    async def get(
        self,
        path: str,
        *,
        content_type: Literal[ContentType.DOCUMENT_MAP],
    ) -> DocumentMap: ...

    async def get(
        self,
        path: str,
        *,
        content_type: ContentType = ContentType.MARKDOWN,
    ) -> str | NoteJson | DocumentMap:
        """Get the content of a vault file.

        Args:
            path: Path to the file relative to the vault root
                (e.g. `"Notes/hello.md"`).
            content_type: Desired response format. Use
                `ContentType.MARKDOWN` for raw text,
                `ContentType.NOTE_JSON` for structured JSON, or
                `ContentType.DOCUMENT_MAP` for headings/blocks.

        Returns:
            File content as `str`, `NoteJson`, or `DocumentMap`
            depending on the requested content type.

        Raises:
            NotFoundError: If the file does not exist.
        """
        return await self._get_content(f"{self._BASE_URL}/{path}", content_type)

    async def update(self, path: str, content: str) -> None:
        """Create or replace a file in the vault.

        Args:
            path: Path for the file relative to the vault root.
            content: Markdown content to write.
        """
        await self._client.request(
            "PUT",
            f"{self._BASE_URL}/{path}",
            content=content,
            headers={"Content-Type": ContentType.MARKDOWN},
        )

    async def append(self, path: str, content: str) -> None:
        """Append content to the end of a vault file.

        Args:
            path: Path to the file relative to the vault root.
            content: Markdown content to append.

        Raises:
            NotFoundError: If the file does not exist.
        """
        await self._append_content(f"{self._BASE_URL}/{path}", content)

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
        """Patch a specific section of a vault file.

        Args:
            path: Path to the file relative to the vault root.
            content: Content to insert or replace.
            operation: How to apply the content (`append`, `prepend`,
                or `replace`).
            target_type: What to target (`heading`, `block`, or
                `frontmatter`).
            target: The target identifier (e.g. heading text, block ID,
                or frontmatter field name).
            target_delimiter: Delimiter for nested targets.

        Raises:
            NotFoundError: If the file does not exist.
        """
        await self._patch_content(
            f"{self._BASE_URL}/{path}",
            content,
            operation=operation,
            target_type=target_type,
            target=target,
            target_delimiter=target_delimiter,
        )

    async def delete(self, path: str) -> None:
        """Delete a file from the vault.

        Args:
            path: Path to the file relative to the vault root.

        Raises:
            NotFoundError: If the file does not exist.
        """
        await self._client.request("DELETE", f"{self._BASE_URL}/{path}")

    async def list(self, path: str = "") -> VaultDirectory:
        """List files in a vault directory.

        Args:
            path: Directory path relative to the vault root.
                Empty string for the root directory.

        Returns:
            A `VaultDirectory` containing the list of file paths.
        """
        path = path.strip("/")
        trailing = f"{path}/" if path else ""
        response = await self._client.request("GET", f"{self._BASE_URL}/{trailing}")
        return VaultDirectory.model_validate(response.json())
