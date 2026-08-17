from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class FileVersion(BaseModel):
    """A version of a note kept by file recovery.

    Attributes:
        version: Position in the listing, counting from 1 with the
            newest version first — the number `history.read()` and
            `history.restore()` take. It is a position rather than an
            identifier: saving the note again renumbers every version
            below it.
        modified: When the version was taken. The CLI prints it to the
            minute and names no timezone, so this carries none either
            and reads in whatever zone Obsidian is running in.
        size: Size of the version as the CLI prints it, rounded and
            carrying its unit, as in `"431 B"`.
    """

    version: int
    modified: datetime
    size: str
