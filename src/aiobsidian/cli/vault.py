from __future__ import annotations

from .._exceptions import CLIParseError
from ._base import BaseCLIResource


class CLIVaultResource(BaseCLIResource):
    """CLI resource for vault file operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

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
        content: str = "",
        *,
        name: str | None = None,
        template: str | None = None,
        overwrite: bool = False,
    ) -> None:
        """Create a new file in the vault.

        Content with literal ``\\n`` or ``\\t`` sequences is written in several
        calls, so the file is built up incrementally rather than atomically.

        Args:
            path: Path for the new file relative to the vault root. When
                ``name`` is given this is the folder to create it in.
            content: File content. Cannot be combined with ``template``.
            name: File name, without a directory prefix, appended to
                ``path``.
            template: Template to fill the new file with. The CLI reads
                the template instead of ``content``, never both.
            overwrite: If ``True``, overwrite an existing file.

        Raises:
            ValueError: If both ``content`` and ``template`` are given.
        """
        if content and template is not None:
            raise ValueError(
                "create() takes content or template, not both: "
                "the CLI writes the template and drops the content"
            )
        params: dict[str, str] = {"path": path}
        parts = self._split_content(content)
        if template is not None:
            params["template"] = template
        else:
            params["content"] = parts[0]
        if name is not None:
            params["name"] = name
        flags = ["overwrite"] if overwrite else None
        await self._cli._execute("create", params=params, flags=flags)
        await self._write_parts(
            "append", parts[1:], params={"path": self._created_path(path, name)}
        )

    @staticmethod
    def _created_path(path: str, name: str | None) -> str:
        """Work out where the CLI puts a file it was asked to create.

        `create` joins `path` and `name` when both are given, and adds a
        `.md` extension when the result has none. The rest of a content
        write is appended to that file, not to `path`.

        Args:
            path: Path passed to `create`.
            name: File name passed to `create`, if any.

        Returns:
            Path of the created file, relative to the vault root.
        """
        target = f"{path.rstrip('/')}/{name}" if name is not None else path
        return target if target.rfind(".") > 0 else f"{target}.md"

    async def append(self, path: str, content: str, *, inline: bool = False) -> None:
        """Append content to a vault file.

        Content with literal ``\\n`` or ``\\t`` sequences is written in several
        calls, so the append is not atomic.

        Args:
            path: Path to the file relative to the vault root.
            content: Content to append.
            inline: If ``True``, append inline without a newline separator.
        """
        parts = self._split_content(content)
        flags = ["inline"] if inline else None
        await self._cli._execute(
            "append", params={"path": path, "content": parts[0]}, flags=flags
        )
        await self._write_parts("append", parts[1:], params={"path": path})

    async def prepend(self, path: str, content: str) -> None:
        """Prepend content to a vault file.

        Content with literal ``\\n`` or ``\\t`` sequences is written in several
        calls, so the prepend is not atomic.

        Args:
            path: Path to the file relative to the vault root.
            content: Content to prepend.
        """
        parts = self._split_content(content)
        await self._cli._execute("prepend", params={"path": path, "content": parts[-1]})
        await self._write_parts("prepend", parts[-2::-1], params={"path": path})

    async def move(self, path: str, to: str) -> None:
        """Move a vault file to a new location.

        Args:
            path: Current path relative to the vault root.
            to: Destination path relative to the vault root.
        """
        await self._cli._execute("move", params={"path": path, "to": to})

    async def rename(self, path: str, new_name: str) -> None:
        """Rename a vault file, leaving it in its folder.

        Args:
            path: Current path relative to the vault root.
            new_name: New file name, without a directory prefix. The
                extension is kept when it is omitted.
        """
        await self._cli._execute("rename", params={"path": path, "name": new_name})

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
        output = await self._cli._execute("wordcount", params={"path": path})
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
