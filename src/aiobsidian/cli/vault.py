from __future__ import annotations

from .._exceptions import CLIParseError
from ._base import BaseCLIResource


class CLIVaultResource(BaseCLIResource):
    """CLI resource for vault file operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def open(self, path: str) -> None:
        """Open a file in the Obsidian UI.

        Args:
            path: Path to the file relative to the vault root.
        """
        await self._cli._execute("open", params={"path": path})

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
            flags.append("overwrite")
        if silent:
            flags.append("silent")
        await self._cli._execute("create", params=params, flags=flags or None)

    async def append(self, path: str, content: str, *, inline: bool = False) -> None:
        """Append content to a vault file.

        Args:
            path: Path to the file relative to the vault root.
            content: Content to append.
            inline: If ``True``, append inline without a newline separator.
        """
        flags = ["inline"] if inline else None
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
        flags = ["permanent"] if permanent else None
        await self._cli._execute("delete", params={"path": path}, flags=flags)

    async def info(self) -> dict[str, str]:
        """Get vault information.

        Returns:
            Vault details keyed by field name: ``name``, ``path``, ``files``,
            ``folders`` and ``size``.
        """
        output = await self._cli._execute("vault")
        return self._parse_fields("vault", output)

    async def file_info(self, path: str) -> dict[str, str]:
        """Get information about a file.

        Args:
            path: Path to the file relative to the vault root.

        Returns:
            File metadata keyed by field name: ``path``, ``name``,
            ``extension``, ``size``, ``created`` and ``modified``.
        """
        output = await self._cli._execute("file", params={"path": path})
        return self._parse_fields("file", output)

    async def folder_info(self, path: str) -> dict[str, str]:
        """Get information about a folder.

        Args:
            path: Path to the folder relative to the vault root.

        Returns:
            Folder metadata keyed by field name: ``path``, ``files``,
            ``folders`` and ``size``.
        """
        output = await self._cli._execute("folder", params={"path": path})
        return self._parse_fields("folder", output)

    async def folders(self, folder: str = "") -> list[str]:
        """List folders in the vault.

        Args:
            folder: Parent folder path relative to the vault root.
                    Empty string lists all folders.

        Returns:
            List of folder paths.
        """
        params = {"folder": folder} if folder else None
        output = await self._cli._execute("folders", params=params)
        return self._parse_lines(output)

    async def wordcount(self, path: str) -> dict[str, int]:
        """Get word and character count for a file.

        Args:
            path: Path to the file relative to the vault root.

        Returns:
            Mapping with the ``words`` and ``characters`` counts.

        Raises:
            CLIParseError: If a count is not a number.
        """
        output = await self._cli._execute("wordcount", params={"file": path})
        fields = self._parse_fields("wordcount", output, separator=":")
        try:
            return {key: int(value) for key, value in fields.items()}
        except ValueError as exc:
            raise CLIParseError("wordcount", output) from exc

    async def list(self, folder: str = "", *, ext: str | None = None) -> list[str]:
        """List files in the vault.

        Args:
            folder: Folder path relative to the vault root. Empty string
                    lists every file in the vault.
            ext: Filter by file extension (e.g. ``"md"``).

        Returns:
            List of file paths.
        """
        params: dict[str, str] = {}
        if folder:
            params["folder"] = folder
        if ext is not None:
            params["ext"] = ext
        output = await self._cli._execute("files", params=params or None)
        return self._parse_lines(output)
