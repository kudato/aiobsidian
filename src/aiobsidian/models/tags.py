from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Tag(BaseModel):
    """A tag in the vault, with how often it is used.

    Attributes:
        name: Tag name without the leading `#`, which is the spelling
            `tags.get()` takes.
        count: How many times the tag occurs — across the vault, or
            within one note when `tags.list()` was given a path.
    """

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(alias="tag")
    count: int

    @field_validator("name", mode="before")
    @classmethod
    def _drop_sigil(cls, value: Any) -> Any:
        """Drop the `#` the CLI prints in front of every tag.

        Args:
            value: Tag name as the CLI spells it.

        Returns:
            The name without its leading `#`, or the value untouched if
            it is not a string, leaving the type error to the field.
        """
        return value.removeprefix("#") if isinstance(value, str) else value
