from __future__ import annotations

from typing import TYPE_CHECKING, Literal, overload

from ._types import ContentType, PatchOperation, TargetType
from .models.vault import DocumentMap, NoteJson

if TYPE_CHECKING:
    from ._client import ObsidianClient


class BaseResource:
    """Base class for all API resource classes."""

    __slots__ = ("_client",)

    def __init__(self, client: ObsidianClient) -> None:
        self._client = client


class ContentResource(BaseResource):
    """Base class for resources that operate on file content.

    Provides shared helpers for content retrieval, appending,
    and patching that are used by vault, active file, and
    periodic notes resources.
    """

    @overload
    async def _get_content(
        self, url: str, content_type: Literal[ContentType.MARKDOWN]
    ) -> str: ...

    @overload
    async def _get_content(
        self, url: str, content_type: Literal[ContentType.NOTE_JSON]
    ) -> NoteJson: ...

    @overload
    async def _get_content(
        self, url: str, content_type: Literal[ContentType.DOCUMENT_MAP]
    ) -> DocumentMap: ...

    @overload
    async def _get_content(
        self, url: str, content_type: ContentType
    ) -> str | NoteJson | DocumentMap: ...

    async def _get_content(
        self,
        url: str,
        content_type: ContentType,
    ) -> str | NoteJson | DocumentMap:
        response = await self._client.request(
            "GET",
            url,
            headers={"Accept": content_type.value},
        )
        if content_type == ContentType.NOTE_JSON:
            return NoteJson.model_validate(response.json())
        if content_type == ContentType.DOCUMENT_MAP:
            return DocumentMap.model_validate(response.json())
        return response.text

    async def _append_content(self, url: str, content: str) -> None:
        await self._client.request(
            "POST",
            url,
            content=content,
            headers={"Content-Type": ContentType.MARKDOWN},
        )

    async def _patch_content(
        self,
        url: str,
        content: str,
        *,
        operation: PatchOperation,
        target_type: TargetType,
        target: str,
        target_delimiter: str = "::",
    ) -> None:
        headers: dict[str, str] = {
            "Content-Type": ContentType.MARKDOWN,
            "Operation": operation.value,
            "Target-Type": target_type.value,
            "Target": target,
            "Target-Delimiter": target_delimiter,
        }
        if target_type == TargetType.FRONTMATTER:
            headers["Content-Type"] = "application/json"

        await self._client.request(
            "PATCH",
            url,
            content=content,
            headers=headers,
        )
