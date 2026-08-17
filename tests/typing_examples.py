"""Static-typing contracts, checked by mypy rather than pytest.

Nothing here runs: `mypy` verifies that the overloads of the REST `read()`
methods resolve as documented. The module is deliberately not named
`test_*` so pytest leaves it alone.
"""

from __future__ import annotations

from typing import assert_type

from aiobsidian import ContentType, DocumentMap, NoteJson, ObsidianClient


async def literal_content_types(client: ObsidianClient) -> None:
    """A literal `ContentType` narrows the return type."""
    assert_type(await client.vault.read("note.md"), str)
    assert_type(
        await client.vault.read("note.md", content_type=ContentType.NOTE_JSON),
        NoteJson,
    )
    assert_type(
        await client.vault.read("note.md", content_type=ContentType.DOCUMENT_MAP),
        DocumentMap,
    )
    assert_type(await client.active.read(), str)
    assert_type(
        await client.active.read(content_type=ContentType.NOTE_JSON),
        NoteJson,
    )
    assert_type(
        await client.active.read(content_type=ContentType.DOCUMENT_MAP),
        DocumentMap,
    )


async def runtime_content_type(client: ObsidianClient, chosen: ContentType) -> None:
    """A `ContentType` picked at runtime type-checks, widening the return."""
    assert_type(
        await client.vault.read("note.md", content_type=chosen),
        str | NoteJson | DocumentMap,
    )
    assert_type(
        await client.active.read(content_type=chosen),
        str | NoteJson | DocumentMap,
    )
