from __future__ import annotations

from unittest.mock import call

import pytest

from aiobsidian._exceptions import CLIParseError


async def test_open(cli):
    cli._execute.return_value = ""
    await cli.vault.open("note.md")
    cli._execute.assert_awaited_once_with("open", params={"path": "note.md"})


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
        flags=["overwrite"],
    )


async def test_create_with_name(cli):
    cli._execute.return_value = ""
    await cli.vault.create("note.md", "content", name="My Note")
    cli._execute.assert_awaited_once_with(
        "create",
        params={"path": "note.md", "content": "content", "name": "My Note"},
        flags=None,
    )


async def test_create_with_template(cli):
    cli._execute.return_value = ""
    await cli.vault.create("note.md", "content", template="daily")
    cli._execute.assert_awaited_once_with(
        "create",
        params={"path": "note.md", "content": "content", "template": "daily"},
        flags=None,
    )


async def test_create_silent(cli):
    cli._execute.return_value = ""
    await cli.vault.create("note.md", "content", silent=True)
    cli._execute.assert_awaited_once_with(
        "create",
        params={"path": "note.md", "content": "content"},
        flags=["silent"],
    )


async def test_create_all_params(cli):
    cli._execute.return_value = ""
    await cli.vault.create(
        "note.md",
        "content",
        name="My Note",
        template="daily",
        overwrite=True,
        silent=True,
    )
    cli._execute.assert_awaited_once_with(
        "create",
        params={
            "path": "note.md",
            "content": "content",
            "name": "My Note",
            "template": "daily",
        },
        flags=["overwrite", "silent"],
    )


async def test_append(cli):
    cli._execute.return_value = ""
    await cli.vault.append("note.md", "extra")
    cli._execute.assert_awaited_once_with(
        "append", params={"path": "note.md", "content": "extra"}, flags=None
    )


async def test_append_inline(cli):
    cli._execute.return_value = ""
    await cli.vault.append("note.md", "extra", inline=True)
    cli._execute.assert_awaited_once_with(
        "append", params={"path": "note.md", "content": "extra"}, flags=["inline"]
    )


async def test_prepend(cli):
    cli._execute.return_value = ""
    await cli.vault.prepend("note.md", "first")
    cli._execute.assert_awaited_once_with(
        "prepend", params={"path": "note.md", "content": "first"}
    )


async def test_create_with_backslash_escapes(cli):
    cli._execute.return_value = ""
    await cli.vault.create("note.md", r"C:\notes\temp")
    assert cli._execute.await_args_list == [
        call("create", params={"path": "note.md", "content": "C:\\"}, flags=None),
        call(
            "append",
            params={"path": "note.md", "content": "notes\\"},
            flags=["inline"],
        ),
        call(
            "append",
            params={"path": "note.md", "content": "temp"},
            flags=["inline"],
        ),
    ]


async def test_append_with_backslash_escapes(cli):
    cli._execute.return_value = ""
    await cli.vault.append("note.md", r"a\tb")
    assert cli._execute.await_args_list == [
        call("append", params={"path": "note.md", "content": "a\\"}, flags=None),
        call("append", params={"path": "note.md", "content": "tb"}, flags=["inline"]),
    ]


async def test_append_inline_with_backslash_escapes(cli):
    cli._execute.return_value = ""
    await cli.vault.append("note.md", r"a\tb", inline=True)
    assert cli._execute.await_args_list == [
        call("append", params={"path": "note.md", "content": "a\\"}, flags=["inline"]),
        call("append", params={"path": "note.md", "content": "tb"}, flags=["inline"]),
    ]


async def test_prepend_with_backslash_escapes(cli):
    cli._execute.return_value = ""
    await cli.vault.prepend("note.md", r"C:\notes\temp")
    assert cli._execute.await_args_list == [
        call("prepend", params={"path": "note.md", "content": "temp"}),
        call(
            "prepend",
            params={"path": "note.md", "content": "notes\\"},
            flags=["inline"],
        ),
        call(
            "prepend",
            params={"path": "note.md", "content": "C:\\"},
            flags=["inline"],
        ),
    ]


async def test_move(cli):
    cli._execute.return_value = ""
    await cli.vault.move("old.md", "new.md")
    cli._execute.assert_awaited_once_with(
        "move", params={"path": "old.md", "to": "new.md"}
    )


async def test_rename(cli):
    cli._execute.return_value = "Renamed to renamed.md\n"
    await cli.vault.rename("note.md", "renamed.md")
    cli._execute.assert_awaited_once_with(
        "rename", params={"path": "note.md", "name": "renamed.md"}
    )


async def test_delete(cli):
    cli._execute.return_value = ""
    await cli.vault.delete("note.md")
    cli._execute.assert_awaited_once_with(
        "delete", params={"path": "note.md"}, flags=None
    )


async def test_delete_permanent(cli):
    cli._execute.return_value = ""
    await cli.vault.delete("note.md", permanent=True)
    cli._execute.assert_awaited_once_with(
        "delete", params={"path": "note.md"}, flags=["permanent"]
    )


async def test_list(cli):
    cli._execute.return_value = "a.md\nb.md\n"
    result = await cli.vault.list()
    assert result == ["a.md", "b.md"]
    cli._execute.assert_awaited_once_with("files", params=None)


async def test_list_with_folder_positional(cli):
    cli._execute.return_value = "folder/a.md\n"
    result = await cli.vault.list("folder")
    assert result == ["folder/a.md"]
    cli._execute.assert_awaited_once_with("files", params={"folder": "folder"})


async def test_list_with_ext(cli):
    cli._execute.return_value = "a.md\nb.md\n"
    result = await cli.vault.list(ext="md")
    assert result == ["a.md", "b.md"]
    cli._execute.assert_awaited_once_with("files", params={"ext": "md"})


async def test_list_with_folder_keyword(cli):
    cli._execute.return_value = "notes/a.md\n"
    result = await cli.vault.list(folder="notes")
    assert result == ["notes/a.md"]
    cli._execute.assert_awaited_once_with("files", params={"folder": "notes"})


async def test_list_with_folder_and_ext(cli):
    cli._execute.return_value = "notes/a.md\n"
    result = await cli.vault.list("notes", ext="md")
    assert result == ["notes/a.md"]
    cli._execute.assert_awaited_once_with(
        "files", params={"folder": "notes", "ext": "md"}
    )


async def test_list_empty_vault(cli):
    cli._execute.return_value = ""
    result = await cli.vault.list()
    assert result == []


async def test_info(cli):
    cli._execute.return_value = (
        "name\tTestVault\npath\t/vaults/TestVault\nfiles\t47\nfolders\t14\nsize\t2825\n"
    )
    result = await cli.vault.info()
    assert result == {
        "name": "TestVault",
        "path": "/vaults/TestVault",
        "files": "47",
        "folders": "14",
        "size": "2825",
    }
    cli._execute.assert_awaited_once_with("vault")


async def test_info_unexpected_output(cli):
    cli._execute.return_value = "not a field list\n"
    with pytest.raises(CLIParseError):
        await cli.vault.info()


async def test_file_info(cli):
    cli._execute.return_value = (
        "path\tnote.md\nname\tnote\nextension\tmd\nsize\t137\n"
        "created\t1786836399339\nmodified\t1786836399341\n"
    )
    result = await cli.vault.file_info("note.md")
    assert result == {
        "path": "note.md",
        "name": "note",
        "extension": "md",
        "size": "137",
        "created": "1786836399339",
        "modified": "1786836399341",
    }
    cli._execute.assert_awaited_once_with("file", params={"path": "note.md"})


async def test_folder_info(cli):
    cli._execute.return_value = "path\tnotes\nfiles\t3\nfolders\t0\nsize\t305\n"
    result = await cli.vault.folder_info("notes")
    assert result == {"path": "notes", "files": "3", "folders": "0", "size": "305"}
    cli._execute.assert_awaited_once_with("folder", params={"path": "notes"})


async def test_folders(cli):
    cli._execute.return_value = "notes\narchive\ntemplates\n"
    result = await cli.vault.folders()
    assert result == ["notes", "archive", "templates"]
    cli._execute.assert_awaited_once_with("folders", params=None)


async def test_folders_with_parent(cli):
    cli._execute.return_value = "notes/sub1\nnotes/sub2\n"
    result = await cli.vault.folders("notes")
    assert result == ["notes/sub1", "notes/sub2"]
    cli._execute.assert_awaited_once_with("folders", params={"folder": "notes"})


async def test_wordcount(cli):
    cli._execute.return_value = "words: 500\ncharacters: 2800\n"
    result = await cli.vault.wordcount("note.md")
    assert result == {"words": 500, "characters": 2800}
    cli._execute.assert_awaited_once_with("wordcount", params={"file": "note.md"})


async def test_wordcount_non_numeric(cli):
    cli._execute.return_value = "words: many\n"
    with pytest.raises(CLIParseError):
        await cli.vault.wordcount("note.md")
