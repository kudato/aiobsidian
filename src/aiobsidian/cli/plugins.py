from __future__ import annotations

from ..models import Plugin, PluginInfo
from ._base import BaseCLIResource


class CLIPluginsResource(BaseCLIResource):
    """CLI resource for plugin management.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def info(self, plugin_id: str) -> PluginInfo:
        """Get details about a plugin.

        Args:
            plugin_id: Plugin identifier.

        Returns:
            What the plugin is and whether it is turned on. A community
            plugin also carries its version, author and description.

        Raises:
            CLIParseError: If the output has an unexpected shape.
        """
        output = await self._cli._execute("plugin", params={"id": plugin_id})
        return self._parse_fields_as("plugin", output, PluginInfo)

    async def is_restricted(self) -> bool:
        """Check whether restricted mode is on.

        Returns:
            ``True`` if restricted mode is on and every community plugin
            with it off, ``False`` otherwise.

        Raises:
            CLIParseError: If the output has an unexpected shape.
        """
        output = await self._cli._execute("plugins:restrict")
        return self._parse_yes_or_no("plugins:restrict", output, yes="on", no="off")

    async def set_restricted(self, value: bool) -> bool:
        """Turn restricted mode on or off.

        Obsidian reloads its window right after answering, and only when
        the setting actually changed — which is what this returns, so a
        caller that has to sit out the reload knows whether there is one
        coming.

        Args:
            value: ``True`` enables restricted mode, which turns every
                community plugin off; ``False`` disables restricted mode
                and lets them run again.

        Returns:
            ``True`` if this call changed anything, ``False`` if
            restricted mode was already the way it was asked to be.

        Raises:
            CLIParseError: If the output has an unexpected shape.
        """
        flags = ["on"] if value else ["off"]
        state = "enabled" if value else "disabled"
        output = await self._cli._execute("plugins:restrict", flags=flags)
        return self._parse_yes_or_no(
            "plugins:restrict",
            output,
            yes=f"Restricted mode {state}. Reloading...",
            no=f"Restricted mode is already {state}.",
        )

    async def enabled(self) -> list[str]:
        """List enabled plugins.

        Returns:
            Identifiers of the plugins that are turned on, core and
            community alike.
        """
        output = await self._cli._execute("plugins:enabled", output_format="json")
        return self._parse_json_column("plugins:enabled", output, key="id")

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

    async def list(self) -> list[Plugin]:
        """List all installed plugins.

        Returns:
            Every installed plugin, core and community alike, sorted by
            identifier. Only a community plugin carries a version.
        """
        output = await self._cli._execute(
            "plugins", flags=["versions"], output_format="json"
        )
        return self._parse_json_rows("plugins", output, Plugin)
