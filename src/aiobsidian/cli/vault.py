from __future__ import annotations

import json

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

    async def create(self, path: str, content: str, *, overwrite: bool = False) -> None:
        """Create a new file in the vault.

        Args:
            path: Path for the new file relative to the vault root.
            content: File content.
            overwrite: If ``True``, overwrite an existing file.
        """
        flags = ["--overwrite"] if overwrite else None
        await self._cli._execute(
            "create", params={"path": path, "content": content}, flags=flags
        )

    async def append(self, path: str, content: str) -> None:
        """Append content to a vault file.

        Args:
            path: Path to the file relative to the vault root.
            content: Content to append.
        """
        await self._cli._execute("append", params={"path": path, "content": content})

    async def prepend(self, path: str, content: str) -> None:
        """Prepend content to a vault file.

        Args:
            path: Path to the file relative to the vault root.
            content: Content to prepend.
        """
        await self._cli._execute("prepend", params={"path": path, "content": content})

    async def move(self, path: str, new_path: str) -> None:
        """Move a vault file to a new location.

        Args:
            path: Current path relative to the vault root.
            new_path: Destination path relative to the vault root.
        """
        await self._cli._execute("move", params={"path": path, "new-path": new_path})

    async def rename(self, path: str, new_name: str) -> None:
        """Rename a vault file.

        Args:
            path: Current path relative to the vault root.
            new_name: New file name (without directory prefix).
        """
        await self._cli._execute("rename", params={"path": path, "new-name": new_name})

    async def delete(self, path: str) -> None:
        """Delete a vault file.

        Args:
            path: Path to the file relative to the vault root.
        """
        await self._cli._execute("delete", params={"path": path})

    async def list(self, path: str = "") -> list[str]:
        """List files in the vault.

        Args:
            path: Directory path relative to the vault root.
                  Empty string lists all files.

        Returns:
            List of file paths.
        """
        params = {"path": path} if path else None
        output = await self._cli._execute("files", params=params)
        result: list[str] = json.loads(output)
        return result
