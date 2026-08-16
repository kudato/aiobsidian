from __future__ import annotations

from ._base import BaseResource


class OpenResource(BaseResource):
    """Open files in the Obsidian UI."""

    __slots__ = ()

    _BASE_URL = "/open"

    async def open(
        self,
        filename: str,
        *,
        new_leaf: bool = False,
    ) -> None:
        """Open a file in Obsidian.

        ```python
        await client.open.open("Notes/hello.md")
        ```

        Warning:
            This is not a read-only operation. If the file does not
            exist, Obsidian creates an empty note at `filename` and
            opens that — the call succeeds instead of raising.

        Args:
            filename: Path to the file to open, relative to the vault
                root. A leading slash is ignored.
            new_leaf: If `True`, open the file in a new tab/pane.
        """
        params: dict[str, str] = {}
        if new_leaf:
            params["newLeaf"] = "true"
        await self._client.request(
            "POST",
            f"{self._BASE_URL}/{self._encode_path(filename)}",
            params=params,
        )
