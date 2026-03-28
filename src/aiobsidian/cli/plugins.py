from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLIPluginsResource(BaseCLIResource):
    """CLI resource for plugin management.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def info(self, plugin_id: str) -> dict[str, Any]:
        """Get details about a plugin.

        Args:
            plugin_id: Plugin identifier.

        Returns:
            Plugin details.
        """
        output = await self._cli._execute("plugin", params={"id": plugin_id})
        result: dict[str, Any] = json.loads(output)
        return result

    async def restrict(self, *, on: bool) -> None:
        """Toggle restricted mode for plugins.

        Args:
            on: If ``True``, enable restricted mode;
                if ``False``, disable it.
        """
        flags = ["--on"] if on else ["--off"]
        await self._cli._execute("plugins:restrict", flags=flags)

    async def enabled(self) -> list[dict[str, Any]]:
        """List enabled plugins.

        Returns:
            List of enabled plugin objects.
        """
        output = await self._cli._execute("plugins:enabled")
        result: list[dict[str, Any]] = json.loads(output)
        return result

    async def enable(self, plugin_id: str) -> None:
        """Enable a plugin.

        Args:
            plugin_id: Plugin identifier.
        """
        await self._cli._execute("plugin:enable", params={"id": plugin_id})

    async def disable(self, plugin_id: str) -> None:
        """Disable a plugin.

        Args:
            plugin_id: Plugin identifier.
        """
        await self._cli._execute("plugin:disable", params={"id": plugin_id})

    async def install(self, plugin_id: str) -> None:
        """Install a community plugin.

        Args:
            plugin_id: Plugin identifier from the community registry.
        """
        await self._cli._execute("plugin:install", params={"id": plugin_id})

    async def uninstall(self, plugin_id: str) -> None:
        """Uninstall a plugin.

        Args:
            plugin_id: Plugin identifier.
        """
        await self._cli._execute("plugin:uninstall", params={"id": plugin_id})

    async def reload(self, plugin_id: str) -> None:
        """Reload a plugin (useful during development).

        Args:
            plugin_id: Plugin identifier.
        """
        await self._cli._execute("plugin:reload", params={"id": plugin_id})

    async def list(self, *, versions: bool = False) -> list[dict[str, Any]]:
        """List all installed plugins.

        Args:
            versions: If ``True``, include version information.

        Returns:
            List of plugin objects.
        """
        flags = ["--versions"] if versions else None
        output = await self._cli._execute("plugins", flags=flags)
        result: list[dict[str, Any]] = json.loads(output)
        return result
