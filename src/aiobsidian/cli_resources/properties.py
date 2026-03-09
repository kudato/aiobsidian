from __future__ import annotations

import json
from typing import Any

from .._base_cli_resource import BaseCLIResource


class CLIPropertiesResource(BaseCLIResource):
    """CLI resource for note property operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def list(self, path: str) -> dict[str, Any]:
        """List all properties of a note.

        Args:
            path: Path to the note relative to the vault root.

        Returns:
            Dictionary of property names to their values.
        """
        output = await self._cli._execute("properties", params={"path": path})
        return json.loads(output)

    async def read(self, path: str, property_name: str) -> Any:
        """Read a single property from a note.

        Args:
            path: Path to the note relative to the vault root.
            property_name: Name of the property to read.

        Returns:
            The property value.
        """
        output = await self._cli._execute(
            "property:read",
            params={"path": path, "property": property_name},
        )
        return json.loads(output)

    async def set(self, path: str, property_name: str, value: str) -> None:
        """Set a property on a note.

        Args:
            path: Path to the note relative to the vault root.
            property_name: Name of the property to set.
            value: Value to set.
        """
        await self._cli._execute(
            "property:set",
            params={
                "path": path,
                "property": property_name,
                "value": value,
            },
        )

    async def remove(self, path: str, property_name: str) -> None:
        """Remove a property from a note.

        Args:
            path: Path to the note relative to the vault root.
            property_name: Name of the property to remove.
        """
        await self._cli._execute(
            "property:remove",
            params={"path": path, "property": property_name},
        )
