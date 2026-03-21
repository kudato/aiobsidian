from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLIHotkeysResource(BaseCLIResource):
    """CLI resource for hotkey operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def get(self, command_id: str) -> dict[str, Any]:
        """Get the hotkey binding for a command.

        Args:
            command_id: Command identifier.

        Returns:
            Hotkey binding details.
        """
        output = await self._cli._execute("hotkey", params={"id": command_id})
        result: dict[str, Any] = json.loads(output)
        return result

    async def list(self) -> list[dict[str, Any]]:
        """List all hotkey bindings.

        Returns:
            List of hotkey binding objects.
        """
        output = await self._cli._execute("hotkeys")
        result: list[dict[str, Any]] = json.loads(output)
        return result
