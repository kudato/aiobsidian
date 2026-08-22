from __future__ import annotations

from typing import Literal, overload

from pydantic import BaseModel

from .._types import ContentType, JsonValue, PatchOperation, TargetType
from ..models.vault import DocumentMap, NoteJson
from ._base import ContentResource


class _Listing(BaseModel):
    """The envelope the listing endpoint wraps its one list in.

    Private on purpose: callers get the list itself, so the wrapper
    only has to survive as far as `list()` reading `.files` off it.

    Attributes:
        files: Entries of the folder, a subfolder ending in a slash.
    """

    files: list[str]


class VaultResource(ContentResource):
    """Operations on files and directories in the vault."""

    __slots__ = ()

    _BASE_URL = "/vault"

    # Opening a note is a vault operation with an endpoint of its own.
    _OPEN_URL = "/open"

    @overload
    async def read(
        self,
        path: str,
        *,
        content_type: Literal[ContentType.MARKDOWN] = ...,
    ) -> str: ...

    @overload
    async def read(
        self,
        path: str,
        *,
        content_type: Literal[ContentType.NOTE_JSON],
    ) -> NoteJson: ...

    @overload
    async def read(
        self,
        path: str,
        *,
        content_type: Literal[ContentType.DOCUMENT_MAP],
    ) -> DocumentMap: ...

    @overload
    async def read(
        self,
        path: str,
        *,
        content_type: ContentType,
    ) -> str | NoteJson | DocumentMap: ...

    async def read(
        self,
        path: str,
        *,
        content_type: ContentType = ContentType.MARKDOWN,
    ) -> str | NoteJson | DocumentMap:
        """Read the content of a vault file.

        Args:
            path: Path to the file relative to the vault root
                (e.g. `"Notes/hello.md"`). A leading slash is ignored.
            content_type: Desired response format. Use
                `ContentType.MARKDOWN` for raw text,
                `ContentType.NOTE_JSON` for structured JSON, or
                `ContentType.DOCUMENT_MAP` for headings/blocks.

        Returns:
            File content as `str`, `NoteJson`, or `DocumentMap`
            depending on the requested content type.

        Raises:
            APINotFoundError: If the file does not exist.
            APIParseError: If a JSON content type was asked for and the
                body does not fit it.
        """
        return await self._get_content(
            f"{self._BASE_URL}/{self._encode_path(path)}", content_type
        )

    async def open(self, path: str, *, new_leaf: bool = False) -> None:
        """Open a file in the Obsidian UI.

        Warning:
            This is not a read-only operation. If the file does not
            exist, Obsidian creates an empty note at `path` and opens
            that — the call succeeds instead of raising.

        Args:
            path: Path to the file relative to the vault root.
                A leading slash is ignored.
            new_leaf: If `True`, open the file in a new tab.
        """
        params = {"newLeaf": "true"} if new_leaf else {}
        await self._client.request(
            "POST", f"{self._OPEN_URL}/{self._encode_path(path)}", params=params
        )

    async def write(self, path: str, content: str) -> None:
        """Create or replace a file in the vault.

        Args:
            path: Path for the file relative to the vault root.
                A leading slash is ignored.
            content: Markdown content to write.
        """
        await self._client.request(
            "PUT",
            f"{self._BASE_URL}/{self._encode_path(path)}",
            content=content,
            headers={"Content-Type": ContentType.MARKDOWN},
        )

    async def append(self, path: str, content: str) -> None:
        """Append content to the end of a vault file.

        Args:
            path: Path to the file relative to the vault root.
                A leading slash is ignored.
            content: Markdown content to append.

        Raises:
            APINotFoundError: If the file does not exist.
        """
        await self._append_content(
            f"{self._BASE_URL}/{self._encode_path(path)}", content
        )

    async def patch(
        self,
        path: str,
        content: JsonValue,
        *,
        operation: PatchOperation,
        target_type: TargetType,
        target: str,
        target_delimiter: str = "::",
    ) -> None:
        """Patch a specific section of a vault file.

        Args:
            path: Path to the file relative to the vault root.
                A leading slash is ignored.
            content: Markdown text for a `heading` or `block` target.
                For a `frontmatter` target this is the field's value:
                a `str` is stored verbatim, any other JSON type
                (list, dict, number, bool, `None`) is serialized and
                stored as that type.
            operation: How to apply the content (`append`, `prepend`,
                or `replace`).
            target_type: What to target (`heading`, `block`, or
                `frontmatter`).
            target: The target identifier — heading text, the bare block
                id (no `^`), or the frontmatter key.
            target_delimiter: Delimiter joining the parts of a nested
                heading target.

        Raises:
            APINotFoundError: If the file does not exist.
            TypeError: If `content` is not a `str` while targeting a
                heading or a block.
        """
        await self._patch_content(
            f"{self._BASE_URL}/{self._encode_path(path)}",
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
                A leading slash is ignored.

        Raises:
            APINotFoundError: If the file does not exist.
        """
        await self._client.request(
            "DELETE", f"{self._BASE_URL}/{self._encode_path(path)}"
        )

    async def list(self, folder: str = "") -> list[str]:
        """List the entries of one vault folder.

        The listing is one level deep and names both files and
        subfolders, a subfolder with a trailing slash. `ObsidianCLI`
        splits the same ground differently: its `list()` walks the tree
        and reports only files, and folders have `folders()` to
        themselves.

        Args:
            folder: Folder path relative to the vault root. Empty
                string for the vault root.

        Returns:
            Names of the entries, relative to `folder`.

        Raises:
            APIParseError: If the body is not the listing envelope.
        """
        encoded = self._encode_path(folder)
        trailing = f"{encoded}/" if encoded else ""
        response = await self._client.request("GET", f"{self._BASE_URL}/{trailing}")
        return self._parse_as(response, _Listing).files
