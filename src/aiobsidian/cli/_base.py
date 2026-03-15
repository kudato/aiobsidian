from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .._cli import ObsidianCLI


class BaseCLIResource:
    """Base class for all CLI resource classes."""

    __slots__ = ("_cli",)

    def __init__(self, cli: ObsidianCLI) -> None:
        self._cli = cli
