from __future__ import annotations

from ._base import BaseCLIResource


class CLIPublishResource(BaseCLIResource):
    """CLI resource for Obsidian Publish operations.

    Obsidian registers the `publish:*` commands only for a vault with a
    configured Publish site. Without one the CLI answers
    `Error: Command "publish:status" not found. It may require a plugin to
    be enabled.`, which surfaces as a `CommandError`.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def open(self, path: str | None = None) -> str:
        """Open a file on the published site in a browser.

        Args:
            path: Path to the file to open. Defaults to the file active
                in the Obsidian UI.

        Returns:
            The URL that was opened.
        """
        params = {"path": path} if path is not None else None
        output = await self._cli._execute("publish:open", params=params)
        return output.strip()

    async def site(self) -> dict[str, str]:
        """Get Publish site information.

        Returns:
            Site details keyed by field name: ``slug``, ``url`` and, when
            one is set, ``custom`` for the custom domain.
        """
        output = await self._cli._execute("publish:site")
        return self._parse_fields("publish:site", output)

    async def status(self) -> list[dict[str, str]]:
        """List the changes waiting to be published.

        Returns:
            One entry per changed file, with its ``type`` — ``new``,
            ``changed`` or ``deleted`` — and its ``path``. Empty when the
            site is up to date.
        """
        output = await self._cli._execute("publish:status")
        return [
            {"type": row[0], "path": row[1]}
            for row in self._parse_rows(output)
            if len(row) == 2
        ]

    async def add(self, path: str | None = None, *, changed: bool = False) -> str:
        """Publish a file, or every new and changed file.

        Args:
            path: Path to the file to publish. Defaults to the file active
                in the Obsidian UI.
            changed: If ``True``, publish every new and changed file and
                ignore ``path``.

        Returns:
            The CLI's report of what was published.
        """
        if changed:
            output = await self._cli._execute("publish:add", flags=["changed"])
        else:
            params = {"path": path} if path is not None else None
            output = await self._cli._execute("publish:add", params=params)
        return output.strip()

    async def remove(self, path: str | None = None) -> None:
        """Unpublish a file.

        Args:
            path: Path to the file to unpublish. Defaults to the file
                active in the Obsidian UI.
        """
        params = {"path": path} if path is not None else None
        await self._cli._execute("publish:remove", params=params)

    async def list(self) -> list[str]:
        """List published files.

        Returns:
            Paths of the published files, sorted by the CLI.
        """
        output = await self._cli._execute("publish:list")
        return self._parse_lines(output)
