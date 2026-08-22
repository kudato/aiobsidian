from __future__ import annotations

from typing import Any

from .._types import ContentType
from ..models.search import SearchResult
from ._base import BaseResource


class SearchResource(BaseResource):
    """Search vault content with a text query or a JsonLogic expression."""

    __slots__ = ()

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

        Raises:
            APIParseError: If the body is not a list of results.
        """
        response = await self._client.request(
            "POST",
            f"{self._BASE_URL}/simple/",
            params={"query": query, "contextLength": context_length},
        )
        return self._parse_rows_as(response, SearchResult)

    async def jsonlogic(self, query: dict[str, Any]) -> list[SearchResult]:
        """Search using a JsonLogic query object.

        Only files the query evaluates truthy for are returned, each
        carrying what the expression evaluated to in `result`.

        Args:
            query: A JsonLogic query dictionary
                (e.g. `{"glob": ["*.md"]}`).

        Returns:
            A list of `SearchResult` objects. `result` holds any JSON
            type: `True` for a predicate, the value itself for a field
            lookup.

        Raises:
            APIParseError: If the body is not a list of results.
        """
        response = await self._client.request(
            "POST",
            f"{self._BASE_URL}/",
            json=query,
            headers={"Content-Type": ContentType.JSONLOGIC},
        )
        return self._parse_rows_as(response, SearchResult)
