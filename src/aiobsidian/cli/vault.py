from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLIVaultResource(BaseCLIResource):
    """CLI resource for vault file operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def read(self, path: str) -> str:
        """Read the content of a vault file.

        Args:
            path: Path to the file relative to the vault root.

        Returns:
            File content as a string.
        """
        return await self._cli._execute("read", params={"path": path})

    async def create(
        self,
        path: str,
        content: str,
        *,
        name: str | None = None,
        template: str | None = None,
        overwrite: bool = False,
        silent: bool = False,
    ) -> None:
        """Create a new file in the vault.

        Args:
            path: Path for the new file relative to the vault root.
            content: File content.
            name: Display name for the note.
            template: Template to use for the new file.
            overwrite: If ``True``, overwrite an existing file.
            silent: If ``True``, suppress output.
        """
        params: dict[str, str] = {"path": path, "content": content}
        if name is not None:
            params["name"] = name
        if template is not None:
            params["template"] = template
        flags: list[str] = []
        if overwrite:
            flags.append("--overwrite")
        if silent:
            flags.append("--silent")
        await self._cli._execute(
            "create", params=params, flags=flags or None
        )

    async def append(
        self, path: str, content: str, *, inline: bool = False
    ) -> None:
        """Append content to a vault file.

        Args:
            path: Path to the file relative to the vault root.
            content: Content to append.
            inline: If ``True``, append inline without a newline separator.
        """
        flags = ["--inline"] if inline else None
        await self._cli._execute(
            "append", params={"path": path, "content": content}, flags=flags
        )

    async def prepend(self, path: str, content: str) -> None:
        """Prepend content to a vault file.

        Args:
            path: Path to the file relative to the vault root.
            content: Content to prepend.
        """
        await self._cli._execute("prepend", params={"path": path, "content": content})

    async def move(self, path: str, to: str) -> None:
        """Move a vault file to a new location.

        Args:
            path: Current path relative to the vault root.
            to: Destination path relative to the vault root.
        """
        await self._cli._execute("move", params={"path": path, "to": to})

    async def rename(self, path: str, new_name: str) -> None:
        """Rename a vault file.

        Args:
            path: Current path relative to the vault root.
            new_name: New file name (without directory prefix).
        """
        await self._cli._execute("rename", params={"path": path, "new-name": new_name})

    async def delete(self, path: str, *, permanent: bool = False) -> None:
        """Delete a vault file.

        Args:
            path: Path to the file relative to the vault root.
            permanent: If ``True``, permanently delete instead of moving
                to trash.
        """
        flags = ["--permanent"] if permanent else None
        await self._cli._execute("delete", params={"path": path}, flags=flags)

    async def info(self) -> dict[str, Any]:
        """Get vault information.

        Returns:
            Vault details including name and configuration.
        """
        output = await self._cli._execute("vault")
        result: dict[str, Any] = json.loads(output)
        return result

    async def file_info(self, path: str) -> dict[str, Any]:
        """Get information about a file.

        Args:
            path: Path to the file relative to the vault root.

        Returns:
            File metadata.
        """
        output = await self._cli._execute("file", params={"path": path})
        result: dict[str, Any] = json.loads(output)
        return result

    async def folder_info(self, path: str) -> dict[str, Any]:
        """Get information about a folder.

        Args:
            path: Path to the folder relative to the vault root.

        Returns:
            Folder metadata.
        """
        output = await self._cli._execute("folder", params={"path": path})
        result: dict[str, Any] = json.loads(output)
        return result

    async def folders(self, path: str = "") -> list[str]:
        """List folders in the vault.

        Args:
            path: Directory path relative to the vault root.
                  Empty string lists all folders.

        Returns:
            List of folder paths.
        """
        params = {"path": path} if path else None
        output = await self._cli._execute("folders", params=params)
        result: list[str] = json.loads(output)
        return result

    async def wordcount(self, path: str) -> dict[str, Any]:
        """Get word and character count for a file.

        Args:
            path: Path to the file relative to the vault root.

        Returns:
            Word count statistics.
        """
        output = await self._cli._execute("wordcount", params={"file": path})
        result: dict[str, Any] = json.loads(output)
        return result

    async def list(
        self,
        path: str = "",
        *,
        ext: str | None = None,
        folder: str | None = None,
    ) -> list[str]:
        """List files in the vault.

        Args:
            path: Directory path relative to the vault root.
                  Empty string lists all files.
            ext: Filter by file extension (e.g. ``"md"``).
            folder: Filter by folder path.

        Returns:
            List of file paths.
        """
        params: dict[str, str] = {}
        if path:
            params["path"] = path
        if ext is not None:
            params["ext"] = ext
        if folder is not None:
            params["folder"] = folder
        output = await self._cli._execute("files", params=params or None)
        result: list[str] = json.loads(output)
        return result
