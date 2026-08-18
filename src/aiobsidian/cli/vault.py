from __future__ import annotations

from typing import Literal

from ..models import FileInfo, FolderInfo, VaultInfo, WordCount
from ._base import BaseCLIResource


class CLIVaultResource(BaseCLIResource):
    """CLI resource for vault file operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def open(self, path: str, *, new_tab: bool = False) -> None:
        """Open a file in the Obsidian UI.

        Args:
            path: Path to the file relative to the vault root.
            new_tab: If ``True``, open in a new tab instead of the
                active one.
        """
        flags = ["newtab"] if new_tab else None
        await self._cli._execute("open", params={"path": path}, flags=flags)

    async def read(self, path: str) -> str:
        """Read the content of a vault file.

        Args:
            path: Path to the file relative to the vault root.

        Returns:
            File content as a string.
        """
        return await self._cli._execute("read", params={"path": path})

    async def write(
        self,
        path: str,
        content: str = "",
        *,
        name: str | None = None,
        template: str | None = None,
        overwrite: bool = True,
        open: bool = False,
        new_tab: bool = False,
    ) -> None:
        """Create or replace a file in the vault.

        Content with literal ``\\n`` or ``\\t`` sequences is written in several
        calls, so the file is built up incrementally rather than atomically.

        Args:
            path: Path for the file relative to the vault root. When
                ``name`` is given this is the folder to create it in.
            content: File content. Cannot be combined with ``template``.
            name: File name, without a directory prefix, appended to
                ``path``.
            template: Template to fill the new file with. The CLI reads
                the template instead of ``content``, never both.
            overwrite: If ``False``, refuse to touch a file that is
                already there and let the CLI report it as a failure.
            open: If ``True``, show the file in Obsidian afterwards.
            new_tab: Where to show it, for when ``open`` is asked for.
                On its own it does nothing, since the CLI reads it only
                once it has been told to open something.

        Raises:
            ValueError: If both ``content`` and ``template`` are given.
        """
        if content and template is not None:
            raise ValueError(
                "write() takes content or template, not both: "
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
        flags = ["overwrite"] if overwrite else []
        if open:
            flags.append("open")
        if new_tab:
            flags.append("newtab")
        await self._cli._execute("create", params=params, flags=flags or None)
        await self._write_parts(
            "append", parts[1:], params={"path": self._created_path(path, name)}
        )

    @staticmethod
    def _created_path(path: str, name: str | None) -> str:
        """Work out where the CLI puts a file it was asked to create.

        The `create` command joins `path` and `name` when both are
        given, and adds a `.md` extension when the result has none. The
        rest of a content write is appended to that file, not to `path`.

        Args:
            path: Path passed to `write`.
            name: File name passed to `write`, if any.

        Returns:
            Path of the created file, relative to the vault root.
        """
        target = f"{path.rstrip('/')}/{name}" if name is not None else path
        return target if target.rfind(".") > 0 else f"{target}.md"

    async def create_unique(
        self,
        suffix: str = "",
        content: str = "",
        *,
        open: bool = False,
        pane: Literal["tab", "split", "window"] | None = None,
    ) -> str:
        """Create a note named after the moment it was created.

        The Unique note creator core plugin owns this one, so it answers
        `Error: Command "unique" not found` while that plugin is off,
        and it decides both where the note goes and what it is called:
        the name is a timestamp in the format configured there, and the
        folder and template are that plugin's settings rather than
        arguments. There is no way to say where the note should land, so
        the path it did land in is what comes back.

        Content with literal ``\\n`` or ``\\t`` sequences is written in
        several calls, so the note is built up incrementally rather than
        atomically.

        Args:
            suffix: Follows the generated timestamp, after a space. The
                CLI calls it the name, but the name is the timestamp;
                empty leaves it on its own.
            content: Note content. Written instead of the plugin's
                template, which fills only a note left empty.
            open: If ``True``, show the note in Obsidian afterwards.
            pane: Where to show it, for when ``open`` is asked for. On
                its own it does nothing, since the CLI reads it only
                once it has been told to open something.

        Returns:
            Path of the created note, relative to the vault root.
        """
        parts = self._split_content(content)
        params: dict[str, str] = {"content": parts[0]}
        if suffix:
            params["name"] = suffix
        if pane is not None:
            params["paneType"] = pane
        flags = ["open"] if open else None
        output = await self._cli._execute("unique", params=params, flags=flags)
        path = output.strip()
        await self._write_parts("append", parts[1:], params={"path": path})
        return path

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

    async def prepend(self, path: str, content: str, *, inline: bool = False) -> None:
        """Prepend content to a vault file.

        Content with literal ``\\n`` or ``\\t`` sequences is written in several
        calls, so the prepend is not atomic.

        Args:
            path: Path to the file relative to the vault root.
            content: Content to prepend.
            inline: If ``True``, prepend without a newline separator, so
                the content runs straight into what was there.
        """
        parts = self._split_content(content)
        flags = ["inline"] if inline else None
        # The separator goes between the content and the file, so the
        # flag belongs to the part written against the file itself —
        # which is the last one, prepended first.
        await self._cli._execute(
            "prepend", params={"path": path, "content": parts[-1]}, flags=flags
        )
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

    async def info(self) -> VaultInfo:
        """Get vault information.

        Returns:
            The vault's name, where it lives and what it holds.

        Raises:
            CLIParseError: If the output has an unexpected shape.
        """
        output = await self._cli._execute("vault")
        return self._parse_fields_as("vault", output, VaultInfo)

    async def file_info(self, path: str) -> FileInfo:
        """Get information about a file.

        Args:
            path: Path to the file relative to the vault root.

        Returns:
            The file's name, size and timestamps.

        Raises:
            CLIParseError: If the output has an unexpected shape.
        """
        output = await self._cli._execute("file", params={"path": path})
        return self._parse_fields_as("file", output, FileInfo)

    async def resolve(self, name: str) -> FileInfo:
        """Find the file a note name points at.

        Every other method here takes a path, because a path is exact.
        This is the one that takes a name and resolves it the way a
        wikilink does: the note is looked up wherever it lives, and an
        ambiguous name lands on whichever match Obsidian would follow.
        The record it hands back carries the path, which is what the
        rest of this resource wants. Two calls rather than one, so a
        rename between them leaves the path pointing at nothing — or,
        worse, at whatever took its place.

        Args:
            name: Note name as a link would spell it, with or without
                the extension and with as much of the path as it takes
                to be unambiguous.

        Returns:
            The file's name, size and timestamps, and the path it was
            found at.

        Raises:
            CLINotFoundError: If no file answers to that name.
            CLIParseError: If the output has an unexpected shape.
        """
        output = await self._cli._execute("file", params={"file": name})
        return self._parse_fields_as("file", output, FileInfo)

    async def folder_info(self, path: str) -> FolderInfo:
        """Get information about a folder.

        Args:
            path: Path to the folder relative to the vault root.

        Returns:
            What the folder holds, at any depth below it.

        Raises:
            CLIParseError: If the output has an unexpected shape.
        """
        output = await self._cli._execute("folder", params={"path": path})
        return self._parse_fields_as("folder", output, FolderInfo)

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

    async def folder_count(self, folder: str = "") -> int:
        """Count folders in the vault.

        What `folders()` would return the length of, without the listing
        itself travelling through the CLI to be counted here.

        Args:
            folder: Parent folder path relative to the vault root. Empty
                string counts every folder in the vault.

        Returns:
            How many folders there are below that point, at any depth.

        Raises:
            CLIParseError: If the output is not a whole number.
        """
        params = {"folder": folder} if folder else None
        return await self._count("folders", params=params)

    async def wordcount(self, path: str) -> WordCount:
        """Get word and character count for a file.

        Args:
            path: Path to a Markdown file relative to the vault root.
                The CLI counts nothing else and reports any other
                extension as a failure.

        Returns:
            How much text the note holds.

        Raises:
            CommandError: If the file is not a markdown file.
            CLIParseError: If the output has an unexpected shape.
        """
        output = await self._cli._execute("wordcount", params={"path": path})
        return self._parse_fields_as("wordcount", output, WordCount, separator=": ")

    async def list(self, folder: str = "", *, ext: str | None = None) -> list[str]:
        """List files in the vault.

        Args:
            folder: Folder path relative to the vault root. Empty string
                    lists every file in the vault.
            ext: Filter by file extension (e.g. ``"md"``).

        Returns:
            List of file paths.
        """
        output = await self._cli._execute(
            "files", params=self._files_filter(folder, ext)
        )
        return self._parse_lines(output)

    @staticmethod
    def _files_filter(folder: str, ext: str | None) -> dict[str, str] | None:
        """Narrow the `files` command to a folder, an extension, or both.

        Listing files and counting them are the same command asked the
        same question, so what makes it a question is written once.

        Args:
            folder: Folder path relative to the vault root, empty for
                the whole vault.
            ext: File extension to keep, or `None` for every file.

        Returns:
            Parameters for the command, or `None` when it is being
            asked about the whole vault.
        """
        params: dict[str, str] = {}
        if folder:
            params["folder"] = folder
        if ext is not None:
            params["ext"] = ext
        return params or None

    async def file_count(self, folder: str = "", *, ext: str | None = None) -> int:
        """Count files in the vault.

        What `list()` would return the length of, without the listing
        itself travelling through the CLI to be counted here.

        Args:
            folder: Folder path relative to the vault root. Empty string
                counts every file in the vault.
            ext: Count only files with this extension (e.g. ``"md"``).

        Returns:
            How many files there are below that point, at any depth.

        Raises:
            CLIParseError: If the output is not a whole number.
        """
        return await self._count("files", params=self._files_filter(folder, ext))
