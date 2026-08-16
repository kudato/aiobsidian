"""Async Python client for Obsidian CLI and Local REST API plugin."""

from ._cli import ObsidianCLI
from ._client import ObsidianClient
from ._exceptions import (
    APIError,
    APINotFoundError,
    AuthenticationError,
    BinaryNotFoundError,
    CLIError,
    CLINotFoundError,
    CLIParseError,
    CLITimeoutError,
    CommandError,
    NotFoundError,
    ObsidianError,
)
from ._types import (
    ContentType,
    JsonValue,
    PatchOperation,
    PropertyType,
    PropertyValue,
    TargetType,
)
from .models import (
    Command,
    DocumentMap,
    FileStat,
    MatchSpan,
    NoteJson,
    SearchMatch,
    SearchResult,
    ServerStatus,
    VaultDirectory,
    Versions,
)

__all__ = [
    "APIError",
    "APINotFoundError",
    "AuthenticationError",
    "BinaryNotFoundError",
    "CLIError",
    "CLINotFoundError",
    "CLIParseError",
    "CLITimeoutError",
    "Command",
    "CommandError",
    "ContentType",
    "DocumentMap",
    "FileStat",
    "JsonValue",
    "MatchSpan",
    "NotFoundError",
    "NoteJson",
    "ObsidianCLI",
    "ObsidianClient",
    "ObsidianError",
    "PatchOperation",
    "PropertyType",
    "PropertyValue",
    "SearchMatch",
    "SearchResult",
    "ServerStatus",
    "TargetType",
    "Versions",
    "VaultDirectory",
]
