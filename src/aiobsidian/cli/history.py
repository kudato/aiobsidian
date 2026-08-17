from __future__ import annotations

from typing import Literal

from ..models import FileVersion
from ._base import BaseCLIResource


class CLIHistoryResource(BaseCLIResource):
    """CLI resource for local file history operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def versions(self, path: str) -> list[FileVersion]:
        """List versions of a specific file in local history.

        Args:
            path: Path to the file relative to the vault root.

        Returns:
            The versions kept for that file, newest first. Their numbers
            are positions in this listing, so they hold only until the
            note is saved again.

        Raises:
            CLIParseError: If a version row has an unexpected shape.
        """
        output = await self._cli._execute("history", params={"path": path})
        return self._parse_rows_as(
            "history",
            output,
            FileVersion,
            columns=("version", "modified", "size"),
        )

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
        from_version: int | None = None,
        to_version: int | None = None,
        filter: Literal["local", "sync"] | None = None,
    ) -> str:
        """Get a diff between file versions.

        This command numbers versions of its own: it lists the local and
        the synced ones together, newest first, so its numbers line up
        with `versions()` only under ``filter="local"``. With neither
        version given it prints that combined listing instead of a diff.

        Args:
            path: Path to the file relative to the vault root.
            from_version: Version to diff from, counting from 1.
            to_version: Version to diff to, counting from 1.
            filter: Restrict the versions to the ``"local"`` ones kept by
                file recovery, or the ``"sync"`` ones held by Obsidian
                Sync.

        Returns:
            Diff output as a string.
        """
        params: dict[str, str] = {"path": path}
        if from_version is not None:
            params["from"] = str(from_version)
        if to_version is not None:
            params["to"] = str(to_version)
        if filter is not None:
            params["filter"] = filter
        return await self._cli._execute("diff", params=params)

    async def read(self, path: str, *, version: int | None = None) -> str:
        """Read a version from local history.

        Args:
            path: Path to the file relative to the vault root.
            version: Version to read, as `versions()` numbers them.
                Defaults to 1, the newest.

        Returns:
            File content at that version, without the header line the CLI
            prints before it.
        """
        params: dict[str, str] = {"path": path}
        if version is not None:
            params["version"] = str(version)
        output = await self._cli._execute("history:read", params=params)
        return self._strip_content_header(output)

    async def restore(self, path: str, *, version: int) -> None:
        """Restore a file from local history.

        Args:
            path: Path to the file relative to the vault root.
            version: Version to restore, as `versions()` numbers them.
        """
        await self._cli._execute(
            "history:restore", params={"path": path, "version": str(version)}
        )

    async def list(self) -> list[str]:
        """List files that have local history.

        Returns:
            List of file paths with local history.
        """
        output = await self._cli._execute("history:list")
        return self._parse_lines(output)
