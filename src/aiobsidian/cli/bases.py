from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLIBasesResource(BaseCLIResource):
    """CLI resource for Obsidian Bases (database) operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def views(self, path: str) -> list[dict[str, Any]]:
        """List views of a database file.

        Args:
            path: Path to the database file.

        Returns:
            List of view objects.
        """
        output = await self._cli._execute("base:views", params={"file": path})
        result: list[dict[str, Any]] = json.loads(output)
        return result

    async def create(self, path: str, **fields: str) -> None:
        """Create a record in a database.

        Args:
            path: Path to the database file.
            **fields: Field name-value pairs for the new record.
        """
        params: dict[str, str] = {"file": path}
        params.update(fields)
        await self._cli._execute("base:create", params=params)

    async def query(
        self, path: str, *, view: str | None = None
    ) -> list[dict[str, Any]]:
        """Query records from a database.

        Args:
            path: Path to the database file.
            view: Optional view name to filter by.

        Returns:
            List of record objects.
        """
        params: dict[str, str] = {"file": path}
        if view:
            params["view"] = view
        output = await self._cli._execute("base:query", params=params)
        result: list[dict[str, Any]] = json.loads(output)
        return result

    async def list(self) -> list[dict[str, Any]]:
        """List all database files in the vault.

        Returns:
            List of database file objects.
        """
        output = await self._cli._execute("bases")
        result: list[dict[str, Any]] = json.loads(output)
        return result
