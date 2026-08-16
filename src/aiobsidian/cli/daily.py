from __future__ import annotations

from ._base import BaseCLIResource


class CLIDailyResource(BaseCLIResource):
    """CLI resource for daily note operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def read(self, *, date: str | None = None) -> str:
        """Read the content of a daily note.

        Args:
            date: Date in ``YYYY-MM-DD`` format. Defaults to today.

        Returns:
            Daily note content as a string.
        """
        params = {"date": date} if date is not None else None
        return await self._cli._execute("daily:read", params=params)

    async def path(self) -> str:
        """Get the file path of today's daily note.

        Returns:
            Path to the daily note relative to the vault root.
        """
        output = await self._cli._execute("daily:path")
        return output.strip()

    async def create(self) -> None:
        """Create today's daily note."""
        await self._cli._execute("daily")

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
