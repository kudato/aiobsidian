from __future__ import annotations

from ._base import BaseCLIResource


class CLIThemesResource(BaseCLIResource):
    """CLI resource for theme management.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def current(self) -> str:
        """Get the active theme.

        Returns:
            Theme name, or ``"(default)"`` when no community theme is active.
        """
        output = await self._cli._execute("theme")
        return output.strip()

    async def set(self, name: str) -> None:
        """Change the active theme.

        Args:
            name: Theme name to activate.
        """
        await self._cli._execute("theme:set", params={"name": name})

    async def install(self, name: str, *, enable: bool = False) -> None:
        """Install a theme from the community registry.

        Args:
            name: Theme name to install.
            enable: If ``True``, activate the theme after installation.
        """
        flags = ["enable"] if enable else None
        await self._cli._execute("theme:install", params={"name": name}, flags=flags)

    async def uninstall(self, name: str) -> None:
        """Uninstall a theme.

        Args:
            name: Theme name to uninstall.
        """
        await self._cli._execute("theme:uninstall", params={"name": name})

    async def list(self, *, versions: bool = False) -> list[str]:
        """List all installed themes.

        Args:
            versions: If ``True``, include version information.

        Returns:
            List of theme names, empty if only the default theme is installed.
        """
        flags = ["versions"] if versions else None
        output = await self._cli._execute("themes", flags=flags)
        return self._parse_lines(output)
