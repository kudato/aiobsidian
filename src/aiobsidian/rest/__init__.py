"""Resource classes of the REST transport.

Reached in normal use through `ObsidianClient`; exported here so they can
be named in a type hint without importing a private module.
"""

from .active import ActiveFileResource
from .commands import CommandsResource
from .search import SearchResource
from .system import SystemResource
from .vault import VaultResource

__all__ = [
    "ActiveFileResource",
    "CommandsResource",
    "SearchResource",
    "SystemResource",
    "VaultResource",
]
