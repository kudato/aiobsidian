from __future__ import annotations

from ._base import BaseCLIResource


class CLIRandomResource(BaseCLIResource):
    """CLI resource for random note operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def read(self) -> str:
        """Read the content of a random note.

        Returns:
            Content of a randomly selected note.
        """
        return await self._cli._execute("random:read")
