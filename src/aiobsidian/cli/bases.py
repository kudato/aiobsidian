from __future__ import annotations

from typing import Any

from ._base import BaseCLIResource


class CLIBasesResource(BaseCLIResource):
    """CLI resource for Obsidian Bases (database) operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def views(self, path: str) -> list[str]:
        """List views of a database file.

        Args:
            path: Path to the database file.

        Returns:
            List of view names.
        """
        output = await self._cli._execute("base:views", params={"file": path})
        return self._parse_lines(output)

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
        if view is not None:
            params["view"] = view
        output = await self._cli._execute(
            "base:query", params=params, output_format="json"
        )
        result: list[dict[str, Any]] = self._parse_json("base:query", output)
        return result

    async def list(self) -> list[str]:
        """List all database files in the vault.

        Returns:
            List of paths to `.base` files.
        """
        output = await self._cli._execute("bases")
        return self._parse_lines(output)
