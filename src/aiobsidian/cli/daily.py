from __future__ import annotations

from ._base import BaseCLIResource


class CLIDailyResource(BaseCLIResource):
    """CLI resource for daily note operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def read(self) -> str:
        """Read the content of today's daily note.

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

    async def create(self) -> None:
        """Create today's daily note."""
        await self._cli._execute("daily")

    async def append(self, content: str) -> None:
        """Append content to today's daily note.

        Args:
            content: Content to append.
        """
        await self._cli._execute("daily:append", params={"content": content})

    async def prepend(self, content: str) -> None:
        """Prepend content to today's daily note.

        Args:
            content: Content to prepend.
        """
        await self._cli._execute("daily:prepend", params={"content": content})
