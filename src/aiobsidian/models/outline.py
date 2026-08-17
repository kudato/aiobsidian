from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Heading(BaseModel):
    """A heading in a note's outline.

    Attributes:
        level: Depth of the heading, 1 for `#` through 6 for `######`.
        text: The heading itself, without the `#` marks that set it.
        line: Line number within the note, counting from 1.
    """

    model_config = ConfigDict(populate_by_name=True)

    level: int
    text: str = Field(alias="heading")
    line: int
