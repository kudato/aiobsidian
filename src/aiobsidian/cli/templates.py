from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLITemplatesResource(BaseCLIResource):
    """CLI resource for template operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def read(
        self,
        name: str,
        *,
        title: str | None = None,
        resolve: bool = False,
    ) -> str:
        """Read a template's content.

        Args:
            name: Template name.
            title: Title to substitute when resolving template variables.
            resolve: If ``True``, resolve template variables in the output.

        Returns:
            Template content as a string.
        """
        params: dict[str, str] = {"name": name}
        if title:
            params["title"] = title
        flags = ["--resolve"] if resolve else None
        return await self._cli._execute("template:read", params=params, flags=flags)

    async def insert(self, name: str) -> None:
        """Insert a template into the active file.

        Args:
            name: Template name to insert.
        """
        await self._cli._execute("template:insert", params={"name": name})

    async def list(self) -> list[dict[str, Any]]:
        """List available templates.

        Returns:
            List of template objects.
        """
        output = await self._cli._execute("templates")
        result: list[dict[str, Any]] = json.loads(output)
        return result
