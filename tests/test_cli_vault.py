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


async def test_info(cli):
    vault_info = {"name": "TestVault", "path": "/vaults/TestVault"}
    cli._execute.return_value = json.dumps(vault_info)
    result = await cli.vault.info()
    assert result == vault_info
    cli._execute.assert_awaited_once_with("vault")


async def test_file_info(cli):
    file_meta = {"path": "note.md", "size": 1024, "ctime": 1710000000}
    cli._execute.return_value = json.dumps(file_meta)
    result = await cli.vault.file_info("note.md")
    assert result == file_meta
    cli._execute.assert_awaited_once_with("file", params={"path": "note.md"})


async def test_folder_info(cli):
    folder_meta = {"path": "notes", "children": 5}
    cli._execute.return_value = json.dumps(folder_meta)
    result = await cli.vault.folder_info("notes")
    assert result == folder_meta
    cli._execute.assert_awaited_once_with("folder", params={"path": "notes"})


async def test_folders(cli):
    cli._execute.return_value = json.dumps(["notes", "archive", "templates"])
    result = await cli.vault.folders()
    assert result == ["notes", "archive", "templates"]
    cli._execute.assert_awaited_once_with("folders", params=None)


async def test_folders_with_path(cli):
    cli._execute.return_value = json.dumps(["notes/sub1", "notes/sub2"])
    result = await cli.vault.folders("notes")
    assert result == ["notes/sub1", "notes/sub2"]
    cli._execute.assert_awaited_once_with("folders", params={"path": "notes"})


async def test_wordcount(cli):
    counts = {"words": 500, "characters": 2800}
    cli._execute.return_value = json.dumps(counts)
    result = await cli.vault.wordcount("note.md")
    assert result == counts
    cli._execute.assert_awaited_once_with("wordcount", params={"file": "note.md"})
