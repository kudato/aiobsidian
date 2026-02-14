from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._client import ObsidianClient


class BaseResource:
    __slots__ = ("_client",)

    def __init__(self, client: ObsidianClient) -> None:
        self._client = client
