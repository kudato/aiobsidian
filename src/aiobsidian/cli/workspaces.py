from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLIWorkspacesResource(BaseCLIResource):
    """CLI resource for workspace management.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def current(self) -> dict[str, Any]:
        """Get the current workspace layout tree.

        Returns:
            Current workspace tree structure.
        """
        output = await self._cli._execute("workspace")
        result: dict[str, Any] = json.loads(output)
        return result

    async def save(self, name: str) -> None:
        """Save the current workspace layout.

        Args:
            name: Name for the saved workspace.
        """
        await self._cli._execute("workspace:save", params={"name": name})

    async def load(self, name: str) -> None:
        """Load a saved workspace.

        Args:
            name: Name of the workspace to load.
        """
        await self._cli._execute("workspace:load", params={"name": name})

    async def delete(self, name: str) -> None:
        """Delete a saved workspace.

        Args:
            name: Name of the workspace to delete.
        """
        await self._cli._execute("workspace:delete", params={"name": name})

    async def list(self) -> list[dict[str, Any]]:
        """List all saved workspaces.

        Returns:
            List of workspace objects.
        """
        output = await self._cli._execute("workspaces")
        result: list[dict[str, Any]] = json.loads(output)
        return result
