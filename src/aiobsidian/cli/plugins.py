from __future__ import annotations

from typing import Any

from ._base import BaseCLIResource


class CLIPluginsResource(BaseCLIResource):
    """CLI resource for plugin management.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def info(self, plugin_id: str) -> dict[str, str]:
        """Get details about a plugin.

        Args:
            plugin_id: Plugin identifier.

        Returns:
            Plugin details keyed by field name (e.g. ``type``, ``name``,
            ``enabled``).
        """
        output = await self._cli._execute("plugin", params={"id": plugin_id})
        return self._parse_fields("plugin", output)

    async def set_restricted(self, value: bool) -> None:
        """Turn restricted mode on or off.

        Obsidian reloads its window right after answering, unless the
        setting was already in the state asked for; give it a moment
        before the next command.

        Args:
            value: ``True`` enables restricted mode, which turns every
                community plugin off; ``False`` disables restricted mode
                and lets them run again.
        """
        flags = ["on"] if value else ["off"]
        await self._cli._execute("plugins:restrict", flags=flags)

    async def enabled(self) -> list[str]:
        """List enabled plugins.

        Returns:
            Identifiers of the plugins that are turned on, core and
            community alike.
        """
        output = await self._cli._execute("plugins:enabled", output_format="json")
        return self._parse_json_column("plugins:enabled", output, "id")

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
        flags = ["versions"] if versions else None
        output = await self._cli._execute("plugins", flags=flags, output_format="json")
        result: list[dict[str, Any]] = self._parse_json("plugins", output)
        return result
