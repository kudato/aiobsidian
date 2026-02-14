from typing import Any

from .._base_resource import BaseResource
from .._types import ContentType
from ..models.search import SearchResult


class SearchResource(BaseResource):
    async def simple(
        self,
        query: str,
        *,
        context_length: int = 100,
    ) -> list[SearchResult]:
        response = await self._client.request(
            "POST",
            "/search/simple/",
            params={"query": query, "contextLength": context_length},
        )
        return [SearchResult.model_validate(r) for r in response.json()]

    async def dataview(self, dql: str) -> list[SearchResult]:
        response = await self._client.request(
            "POST",
            "/search/",
            content=dql,
            headers={"Content-Type": ContentType.DATAVIEW_DQL},
        )
        return [SearchResult.model_validate(r) for r in response.json()]

    async def jsonlogic(self, query: dict[str, Any]) -> list[SearchResult]:
        response = await self._client.request(
            "POST",
            "/search/",
            json=query,
            headers={"Content-Type": ContentType.JSONLOGIC},
        )
        return [SearchResult.model_validate(r) for r in response.json()]
