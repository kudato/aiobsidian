from __future__ import annotations

from ._base import BaseCLIResource


class CLITabsResource(BaseCLIResource):
    """CLI resource for workspace tabs management.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def open(self, *, file: str | None = None, view: str | None = None) -> None:
        """Open a file or view in a new tab.

        Args:
            file: Path to the file to open.
            view: View type to open.
        """
        params: dict[str, str] = {}
        if file is not None:
            params["file"] = file
        if view is not None:
            params["view"] = view
        await self._cli._execute("tab:open", params=params or None)

    async def recents(self) -> list[str]:
        """List recently opened files.

        Returns:
            List of file paths, most recent first.
        """
        output = await self._cli._execute("recents")
        return self._parse_lines(output)

    async def list(self) -> list[str]:
        """List open tabs.

        Returns:
            List of tabs as printed by the CLI, each prefixed with its view
            type (e.g. ``"[markdown] welcome"``).
        """
        output = await self._cli._execute("tabs")
        return self._parse_lines(output)
