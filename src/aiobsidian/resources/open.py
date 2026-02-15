from __future__ import annotations

from .._base_resource import BaseResource


class OpenResource(BaseResource):
    """Open files in the Obsidian UI."""

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

        Args:
            filename: Path to the file to open, relative to the vault root.
            new_leaf: If `True`, open the file in a new tab/pane.
        """
        params: dict[str, str] = {}
        if new_leaf:
            params["newLeaf"] = "true"
        await self._client.request(
            "POST",
            f"{self._BASE_URL}/{filename}",
            params=params,
        )
