from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLIOutlineResource(BaseCLIResource):
    """CLI resource for document outline operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def get(self, path: str) -> list[dict[str, Any]]:
        """Get the heading outline of a file.

        Args:
            path: Path to the file relative to the vault root.

        Returns:
            List of heading objects forming the document outline.
        """
        output = await self._cli._execute("outline", params={"file": path})
        result: list[dict[str, Any]] = json.loads(output)
        return result
