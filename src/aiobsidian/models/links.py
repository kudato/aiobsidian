from __future__ import annotations

from pydantic import BaseModel


class Backlink(BaseModel):
    """A note that links to another one.

    Attributes:
        file: Path to the linking note.
        count: How many of its links point at the note asked about.
    """

    file: str
    count: int
