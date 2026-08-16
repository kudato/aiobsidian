from __future__ import annotations

from ._base import BaseCLIResource


class CLIWorkspacesResource(BaseCLIResource):
    """CLI resource for workspace management.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def current(self) -> str:
        """Get the current workspace layout tree.

        Returns:
            The layout as a rendered tree, one pane group per section.
        """
        output = await self._cli._execute("workspace")
        return output.strip()

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

    async def list(self) -> list[str]:
        """List all saved workspaces.

        Returns:
            List of workspace names, empty if none are saved.
        """
        output = await self._cli._execute("workspaces")
        return self._parse_lines(output)
