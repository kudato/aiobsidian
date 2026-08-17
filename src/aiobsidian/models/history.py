from __future__ import annotations

import unicodedata
from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


class FileVersion(BaseModel):
    """A version of a note kept by file recovery.

    Attributes:
        version: Position in the listing, counting from 1 with the
            newest version first — the number `history.read()` and
            `history.restore()` take. It is a position rather than an
            identifier: file recovery snapshots a changed note every few
            minutes and `history.restore()` adds one straight away, and
            each new snapshot pushes every number below it down by one.
        modified: When the version was taken. The CLI prints it to the
            minute and names no timezone, so this carries none either
            and reads in whatever zone Obsidian is running in.
        size: Size of the version as the CLI prints it, rounded and
            carrying its unit, as in `"431 B"`.
    """

    version: int
    modified: datetime
    size: str

    @field_validator("modified", mode="before")
    @classmethod
    def _latin_digits(cls, value: Any) -> Any:
        """Spell the timestamp in the digits `datetime` can read.

        Obsidian formats it through moment, under the locale of the
        language the app runs in, and several of those locales rewrite
        every digit — an Arabic UI prints `٢٠٢٦-٠٨-١٦ ٠٢:٣٨`.

        Args:
            value: Timestamp column as the CLI printed it.

        Returns:
            The same timestamp with every decimal digit written in
            ASCII, or the value untouched if it is not a string.
        """
        if not isinstance(value, str):
            return value
        return "".join(
            str(unicodedata.decimal(character))
            if character.isdecimal() and not character.isascii()
            else character
            for character in value
        )
