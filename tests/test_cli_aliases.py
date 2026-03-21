from __future__ import annotations

import json

ALIASES = ["My Note", "Note Alias", "Another Name"]


async def test_get(cli):
    cli._execute.return_value = json.dumps(ALIASES)
    result = await cli.aliases.get("notes/my-note.md")
    assert result == ALIASES
    cli._execute.assert_awaited_once_with(
        "aliases", params={"file": "notes/my-note.md"}
    )


async def test_get_empty(cli):
    cli._execute.return_value = json.dumps([])
    result = await cli.aliases.get("notes/no-aliases.md")
    assert result == []
