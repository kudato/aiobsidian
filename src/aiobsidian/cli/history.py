from __future__ import annotations

from .._exceptions import CLIParseError
from ._base import BaseCLIResource


class CLIHistoryResource(BaseCLIResource):
    """CLI resource for local file history operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def versions(self, path: str) -> list[dict[str, str]]:
        """List versions of a specific file in local history.

        Args:
            path: Path to the file relative to the vault root.

        Returns:
            List of versions, each with the ``version`` number, the
            ``modified`` timestamp and the ``size`` of that version.

        Raises:
            CLIParseError: If a version row has an unexpected shape.
        """
        output = await self._cli._execute("history", params={"path": path})
        versions: list[dict[str, str]] = []
        for row in self._parse_rows(output):
            if len(row) != 3:
                raise CLIParseError("history", output)
            versions.append({"version": row[0], "modified": row[1], "size": row[2]})
        return versions

    async def open(self, path: str) -> None:
        """Open the File Recovery UI for a file.

        Args:
            path: Path to the file relative to the vault root.
        """
        await self._cli._execute("history:open", params={"path": path})

    async def diff(
        self,
        path: str,
        *,
        from_version: str | None = None,
        to_version: str | None = None,
        filter: str | None = None,
    ) -> str:
        """Get a diff between file versions.

        Args:
            path: Path to the file relative to the vault root.
            from_version: Starting version identifier.
            to_version: Ending version identifier.
            filter: Filter expression for the diff output.

        Returns:
            Diff output as a string.
        """
        params: dict[str, str] = {"path": path}
        if from_version is not None:
            params["from"] = from_version
        if to_version is not None:
            params["to"] = to_version
        if filter is not None:
            params["filter"] = filter
        return await self._cli._execute("diff", params=params)

    async def read(self, path: str, *, version: str | None = None) -> str:
        """Read a version from local history.

        Args:
            path: Path to the file relative to the vault root.
            version: Version identifier. Defaults to the latest version.

        Returns:
            File content at that version, without the header line the CLI
            prints before it.
        """
        params: dict[str, str] = {"path": path}
        if version is not None:
            params["version"] = version
        output = await self._cli._execute("history:read", params=params)
        return self._strip_content_header(output)

    async def restore(self, path: str, *, version: str) -> None:
        """Restore a file from local history.

        Args:
            path: Path to the file relative to the vault root.
            version: Version identifier to restore.
        """
        await self._cli._execute(
            "history:restore", params={"path": path, "version": version}
        )

    async def list(self) -> list[str]:
        """List files that have local history.

        Returns:
            List of file paths with local history.
        """
        output = await self._cli._execute("history:list")
        return self._parse_lines(output)
