from __future__ import annotations

import datetime
from typing import Literal, overload

from .._base_resource import ContentResource
from .._types import ContentType, PatchOperation, Period, TargetType
from ..models.vault import DocumentMap, NoteJson


class PeriodicNotesResource(ContentResource):
    """Operations on periodic notes (daily, weekly, monthly, quarterly, yearly)."""

    _BASE_URL = "/periodic"

    def _build_url(self, period: Period, date: datetime.date | None = None) -> str:
        if date is None:
            return f"{self._BASE_URL}/{period}/"
        return f"{self._BASE_URL}/{period}/{date.year}/{date.month}/{date.day}/"

    @overload
    async def get(
        self,
        period: Period,
        *,
        date: datetime.date | None = ...,
        content_type: Literal[ContentType.MARKDOWN] = ...,
    ) -> str: ...

    @overload
    async def get(
        self,
        period: Period,
        *,
        date: datetime.date | None = ...,
        content_type: Literal[ContentType.NOTE_JSON],
    ) -> NoteJson: ...

    @overload
    async def get(
        self,
        period: Period,
        *,
        date: datetime.date | None = ...,
        content_type: Literal[ContentType.DOCUMENT_MAP],
    ) -> DocumentMap: ...

    async def get(
        self,
        period: Period,
        *,
        date: datetime.date | None = None,
        content_type: ContentType = ContentType.MARKDOWN,
    ) -> str | NoteJson | DocumentMap:
        """Get the content of a periodic note.

        Args:
            period: The time period (e.g. `Period.DAILY`).
            date: Specific date to retrieve. Defaults to the current period.
            content_type: Desired response format.

        Returns:
            Note content as `str`, `NoteJson`, or `DocumentMap`
            depending on the requested content type.
        """
        return await self._get_content(self._build_url(period, date), content_type)

    async def update(
        self, period: Period, content: str, *, date: datetime.date | None = None
    ) -> None:
        """Replace the entire content of a periodic note.

        If the note does not exist, it will be created.

        Args:
            period: The time period.
            content: New Markdown content for the note.
            date: Specific date to target. Defaults to the current period.
        """
        await self._client.request(
            "PUT",
            self._build_url(period, date),
            content=content,
            headers={"Content-Type": ContentType.MARKDOWN},
        )

    async def append(
        self, period: Period, content: str, *, date: datetime.date | None = None
    ) -> None:
        """Append content to the end of a periodic note.

        Args:
            period: The time period.
            content: Markdown content to append.
            date: Specific date to target. Defaults to the current period.
        """
        await self._append_content(self._build_url(period, date), content)

    async def patch(
        self,
        period: Period,
        content: str,
        *,
        date: datetime.date | None = None,
        operation: PatchOperation,
        target_type: TargetType,
        target: str,
        target_delimiter: str = "::",
    ) -> None:
        """Patch a specific section of a periodic note.

        Args:
            period: The time period.
            content: Content to insert or replace.
            date: Specific date to target. Defaults to the current period.
            operation: How to apply the content (`append`, `prepend`,
                or `replace`).
            target_type: What to target (`heading`, `block`, or
                `frontmatter`).
            target: The target identifier.
            target_delimiter: Delimiter for nested targets.
        """
        await self._patch_content(
            self._build_url(period, date),
            content,
            operation=operation,
            target_type=target_type,
            target=target,
            target_delimiter=target_delimiter,
        )

    async def delete(
        self, period: Period, *, date: datetime.date | None = None
    ) -> None:
        """Delete a periodic note.

        Args:
            period: The time period of the note to delete.
            date: Specific date to target. Defaults to the current period.
        """
        await self._client.request("DELETE", self._build_url(period, date))
