from __future__ import annotations


async def test_get(cli):
    cli._execute.return_value = "home\nstart\n"
    result = await cli.aliases.get("notes/my-note.md")
    assert result == ["home", "start"]
    cli._execute.assert_awaited_once_with(
        "aliases", params={"file": "notes/my-note.md"}
    )


async def test_get_empty(cli):
    cli._execute.return_value = "No aliases found.\n"
    result = await cli.aliases.get("notes/no-aliases.md")
    assert result == []
