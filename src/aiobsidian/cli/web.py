from __future__ import annotations

from ._base import BaseCLIResource


class CLIWebResource(BaseCLIResource):
    """CLI resource for the web viewer.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def open(self, url: str) -> None:
        """Open a URL in the Obsidian web viewer.

        Args:
            url: The URL to open.
        """
        await self._cli._execute("web", params={"url": url})
