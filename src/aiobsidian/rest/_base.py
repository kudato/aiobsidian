from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Literal, overload
from urllib.parse import quote

from pydantic import BaseModel, ValidationError

from .._constants import PATCH_VERSION
from .._exceptions import APIParseError
from .._types import ContentType, JsonValue, PatchOperation, TargetType
from ..models.vault import DocumentMap, NoteJson

if TYPE_CHECKING:
    import httpx

    from .._client import ObsidianClient


class BaseResource:
    """Base class for all API resource classes."""

    __slots__ = ("_client",)

    def __init__(self, client: ObsidianClient) -> None:
        self._client = client

    @staticmethod
    def _encode_path(path: str) -> str:
        """Percent-encode a vault-relative path for use in a request URL.

        Leading and trailing slashes are stripped, so `"/notes/a.md"`
        and `"notes/a.md"` address the same file. Characters that URL
        syntax would otherwise claim (`#`, `?`, `%`) are escaped, while
        the `/` separators are left intact.

        Args:
            path: Path relative to the vault root.

        Returns:
            The encoded path, without leading or trailing slashes.
        """
        return quote(path.strip("/"), safe="/")

    @staticmethod
    def _parse_error(response: httpx.Response) -> APIParseError:
        """Describe a response body that is not what it should be.

        Built rather than raised, so a caller can raise it where the
        shape went wrong and chain it from the exception that said so.

        Args:
            response: The response whose body could not be read.

        Returns:
            The error to raise, naming the request and carrying the
            body.
        """
        return APIParseError(
            response.request.method, str(response.request.url), response.text
        )

    @classmethod
    def _parse_json(cls, response: httpx.Response) -> Any:
        """Parse a response body that is documented to be JSON.

        Args:
            response: The response to read.

        Returns:
            The decoded JSON value.

        Raises:
            APIParseError: If the body is not valid JSON.
        """
        try:
            return response.json()
        except ValueError as exc:
            raise cls._parse_error(response) from exc

    @classmethod
    def _parse_as[ModelT: BaseModel](
        cls, response: httpx.Response, model: type[ModelT]
    ) -> ModelT:
        """Parse a response body that describes one thing.

        Args:
            response: The response to read.
            model: Model to validate the body against.

        Returns:
            The model built from the body.

        Raises:
            APIParseError: If the body is not valid JSON, or is valid
                JSON that does not fit the model.
        """
        try:
            return model.model_validate(cls._parse_json(response))
        except ValidationError as exc:
            raise cls._parse_error(response) from exc

    @classmethod
    def _parse_rows_as[ModelT: BaseModel](
        cls, response: httpx.Response, model: type[ModelT]
    ) -> list[ModelT]:
        """Parse a response body that lists things.

        Args:
            response: The response to read.
            model: Model to validate every entry against.

        Returns:
            One model per entry, in the order sent.

        Raises:
            APIParseError: If the body is not valid JSON, is not a
                list, or an entry does not fit the model.
        """
        rows = cls._parse_json(response)
        if not isinstance(rows, list):
            raise cls._parse_error(response)
        try:
            return [model.model_validate(row) for row in rows]
        except ValidationError as exc:
            raise cls._parse_error(response) from exc


class ContentResource(BaseResource):
    """Base class for resources that operate on file content.

    Provides shared helpers for content retrieval, appending, and
    patching that are used by the vault and active file resources.
    """

    __slots__ = ()

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
        headers = {"Accept": content_type.value}
        if content_type == ContentType.DOCUMENT_MAP:
            # 2.0 answers with a nested heading tree whose paths cannot be
            # fed back to a 1.x patch target; ask for the flat 1.x map.
            headers["Markdown-Patch-Version"] = PATCH_VERSION

        response = await self._client.request("GET", url, headers=headers)
        if content_type == ContentType.NOTE_JSON:
            return self._parse_as(response, NoteJson)
        if content_type == ContentType.DOCUMENT_MAP:
            return self._parse_as(response, DocumentMap)
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
        content: JsonValue,
        *,
        operation: PatchOperation,
        target_type: TargetType,
        target: str,
        target_delimiter: str = "::",
    ) -> None:
        headers: dict[str, str] = {
            "Markdown-Patch-Version": PATCH_VERSION,
            "Content-Type": ContentType.MARKDOWN,
            "Operation": operation.value,
            "Target-Type": target_type.value,
            "Target": quote(target, safe=""),
            "Target-Delimiter": target_delimiter,
        }

        body: str
        if isinstance(content, str):
            body = content
        else:
            if target_type != TargetType.FRONTMATTER:
                raise TypeError(
                    f"a {target_type.value} target takes Markdown text, "
                    f"got {type(content).__name__}"
                )
            headers["Content-Type"] = "application/json"
            body = json.dumps(content)

        await self._client.request(
            "PATCH",
            url,
            content=body,
            headers=headers,
        )
