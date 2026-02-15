from typing import Any

from .._base_resource import BaseResource
from .._types import ContentType
from ..models.search import SearchResult


class SearchResource(BaseResource):
    """Search vault content using different query methods."""

    _BASE_URL = "/search"

    async def simple(
        self,
        query: str,
        *,
        context_length: int = 100,
    ) -> list[SearchResult]:
        """Perform a simple text search across the vault.

        Args:
            query: The search query string.
            context_length: Number of context characters to include
                around each match.

        Returns:
            A list of `SearchResult` objects with matching files
            and context snippets.
        """
        response = await self._client.request(
            "POST",
            f"{self._BASE_URL}/simple/",
            params={"query": query, "contextLength": context_length},
        )
        return [SearchResult.model_validate(r) for r in response.json()]

    async def dataview(self, dql: str) -> list[SearchResult]:
        """Search using a Dataview Query Language (DQL) expression.

        Requires the Dataview plugin to be installed in Obsidian.

        Args:
            dql: A DQL query string (e.g. `"TABLE file.name FROM #tag"`).

        Returns:
            A list of `SearchResult` objects.
        """
        response = await self._client.request(
            "POST",
            f"{self._BASE_URL}/",
            content=dql,
            headers={"Content-Type": ContentType.DATAVIEW_DQL},
        )
        return [SearchResult.model_validate(r) for r in response.json()]

    async def jsonlogic(self, query: dict[str, Any]) -> list[SearchResult]:
        """Search using a JsonLogic query object.

        Args:
            query: A JsonLogic query dictionary
                (e.g. `{"glob": ["*.md"]}`).

        Returns:
            A list of `SearchResult` objects.
        """
        response = await self._client.request(
            "POST",
            f"{self._BASE_URL}/",
            json=query,
            headers={"Content-Type": ContentType.JSONLOGIC},
        )
        return [SearchResult.model_validate(r) for r in response.json()]
