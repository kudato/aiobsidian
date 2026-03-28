from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLITabsResource(BaseCLIResource):
    """CLI resource for workspace tabs management.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

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

    async def recents(self) -> list[dict[str, Any]]:
        """List recently opened files.

        Returns:
            List of recently opened file objects.
        """
        output = await self._cli._execute("recents")
        result: list[dict[str, Any]] = json.loads(output)
        return result

    async def list(self) -> list[dict[str, Any]]:
        """List open tabs.

        Returns:
            List of open tab objects.
        """
        output = await self._cli._execute("tabs")
        result: list[dict[str, Any]] = json.loads(output)
        return result
