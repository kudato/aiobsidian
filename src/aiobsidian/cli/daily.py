from __future__ import annotations

from ._base import BaseCLIResource


class CLIDailyResource(BaseCLIResource):
    """CLI resource for daily note operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def read(self) -> str:
        """Read the content of today's daily note.

        The CLI has no command that reaches a past daily note. Get its
        path from the Daily notes settings and read it with
        `vault.read()`.

        Returns:
            Daily note content as a string.
        """
        return await self._cli._execute("daily:read")

    async def path(self) -> str:
        """Get the file path of today's daily note.

        Returns:
            Path to the daily note relative to the vault root.
        """
        output = await self._cli._execute("daily:path")
        return output.strip()

    async def open(self) -> str:
        """Open today's daily note in the Obsidian UI, creating it first.

        Returns:
            Path to the daily note relative to the vault root.
        """
        output = await self._cli._execute("daily")
        return output.strip().removeprefix("Opened: ")

    async def append(self, content: str) -> None:
        """Append content to today's daily note.

        Content with literal ``\\n`` or ``\\t`` sequences is written in several
        calls, so the append is not atomic.

        Args:
            content: Content to append.
        """
        parts = self._split_content(content)
        await self._cli._execute("daily:append", params={"content": parts[0]})
        await self._write_parts("daily:append", parts[1:])

    async def prepend(self, content: str) -> None:
        """Prepend content to today's daily note.

        Content with literal ``\\n`` or ``\\t`` sequences is written in several
        calls, so the prepend is not atomic.

        Args:
            content: Content to prepend.
        """
        parts = self._split_content(content)
        await self._cli._execute("daily:prepend", params={"content": parts[-1]})
        await self._write_parts("daily:prepend", parts[-2::-1])
