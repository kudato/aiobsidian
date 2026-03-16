from __future__ import annotations

import json

from ._base import BaseCLIResource


class CLIAliasesResource(BaseCLIResource):
    """CLI resource for note alias operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def get(self, path: str) -> list[str]:
        """Get the aliases for a file.

        Args:
            path: Path to the file relative to the vault root.

        Returns:
            List of alias strings for the file.
        """
        output = await self._cli._execute("aliases", params={"file": path})
        result: list[str] = json.loads(output)
        return result
