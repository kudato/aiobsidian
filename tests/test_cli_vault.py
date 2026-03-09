from __future__ import annotations

import json


async def test_read(cli):
    cli._execute.return_value = "# Hello"
    result = await cli.vault.read("note.md")
    assert result == "# Hello"
    cli._execute.assert_awaited_once_with("read", params={"path": "note.md"})


async def test_create(cli):
    cli._execute.return_value = ""
    await cli.vault.create("note.md", "content")
    cli._execute.assert_awaited_once_with(
        "create", params={"path": "note.md", "content": "content"}, flags=None
    )


async def test_create_overwrite(cli):
    cli._execute.return_value = ""
    await cli.vault.create("note.md", "content", overwrite=True)
    cli._execute.assert_awaited_once_with(
        "create",
        params={"path": "note.md", "content": "content"},
        flags=["--overwrite"],
    )


async def test_append(cli):
    cli._execute.return_value = ""
    await cli.vault.append("note.md", "extra")
    cli._execute.assert_awaited_once_with(
        "append", params={"path": "note.md", "content": "extra"}
    )


async def test_prepend(cli):
    cli._execute.return_value = ""
    await cli.vault.prepend("note.md", "first")
    cli._execute.assert_awaited_once_with(
        "prepend", params={"path": "note.md", "content": "first"}
    )


async def test_move(cli):
    cli._execute.return_value = ""
    await cli.vault.move("old.md", "new.md")
    cli._execute.assert_awaited_once_with(
        "move", params={"path": "old.md", "new-path": "new.md"}
    )


async def test_rename(cli):
    cli._execute.return_value = ""
    await cli.vault.rename("note.md", "renamed.md")
    cli._execute.assert_awaited_once_with(
        "rename", params={"path": "note.md", "new-name": "renamed.md"}
    )


async def test_delete(cli):
    cli._execute.return_value = ""
    await cli.vault.delete("note.md")
    cli._execute.assert_awaited_once_with("delete", params={"path": "note.md"})


async def test_list(cli):
    cli._execute.return_value = json.dumps(["a.md", "b.md"])
    result = await cli.vault.list()
    assert result == ["a.md", "b.md"]
    cli._execute.assert_awaited_once_with("files", params=None)


async def test_list_with_path(cli):
    cli._execute.return_value = json.dumps(["folder/a.md"])
    result = await cli.vault.list("folder")
    assert result == ["folder/a.md"]
    cli._execute.assert_awaited_once_with("files", params={"path": "folder"})
