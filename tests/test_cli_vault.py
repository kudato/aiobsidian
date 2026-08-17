from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import call

import pytest

from aiobsidian._exceptions import CLIParseError
from aiobsidian.models.vault import FileInfo, FolderInfo, VaultInfo, WordCount

from .helpers import drop_field

# The counts are of the whole tree, at any depth.
VAULT_INFO = (
    "name\tTestVault\npath\t/vaults/TestVault\nfiles\t47\nfolders\t14\nsize\t2825\n"
)

FOLDER_INFO = "path\tnotes\nfiles\t3\nfolders\t0\nsize\t305\n"

# `created` and `modified` come straight from the file system record,
# where Obsidian keeps them as milliseconds since the epoch.
FILE_INFO = (
    "path\tnote.md\nname\tnote\nextension\tmd\nsize\t137\n"
    "created\t1786836399339\nmodified\t1786836399341\n"
)

# `wordcount` separates with a colon and a space, where every other
# record command separates with a tab.
WORD_COUNT = "words: 500\ncharacters: 2800\n"


async def test_open(cli):
    cli._execute.return_value = ""
    await cli.vault.open("note.md")
    cli._execute.assert_awaited_once_with("open", params={"path": "note.md"})


async def test_read(cli):
    cli._execute.return_value = "# Hello"
    result = await cli.vault.read("note.md")
    assert result == "# Hello"
    cli._execute.assert_awaited_once_with("read", params={"path": "note.md"})


async def test_write(cli):
    cli._execute.return_value = "Created: note.md\n"
    await cli.vault.write("note.md", "content")
    cli._execute.assert_awaited_once_with(
        "create",
        params={"path": "note.md", "content": "content"},
        flags=["overwrite"],
    )


async def test_write_empty(cli):
    cli._execute.return_value = "Created: note.md\n"
    await cli.vault.write("note.md")
    cli._execute.assert_awaited_once_with(
        "create", params={"path": "note.md", "content": ""}, flags=["overwrite"]
    )


async def test_write_without_overwrite(cli):
    cli._execute.return_value = "Created: note.md\n"
    await cli.vault.write("note.md", "content", overwrite=False)
    cli._execute.assert_awaited_once_with(
        "create",
        params={"path": "note.md", "content": "content"},
        flags=None,
    )


async def test_write_with_name(cli):
    cli._execute.return_value = "Created: notes/My Note.md\n"
    await cli.vault.write("notes", "content", name="My Note")
    cli._execute.assert_awaited_once_with(
        "create",
        params={"path": "notes", "content": "content", "name": "My Note"},
        flags=["overwrite"],
    )


async def test_write_with_template(cli):
    cli._execute.return_value = "Created: note.md\n"
    await cli.vault.write("note.md", template="daily")
    cli._execute.assert_awaited_once_with(
        "create",
        params={"path": "note.md", "template": "daily"},
        flags=["overwrite"],
    )


async def test_write_rejects_content_and_template(cli):
    with pytest.raises(ValueError, match="content or template"):
        await cli.vault.write("note.md", "content", template="daily")
    cli._execute.assert_not_awaited()


async def test_write_all_params(cli):
    cli._execute.return_value = "Created: notes/My Note.md\n"
    await cli.vault.write("notes", template="daily", name="My Note", overwrite=False)
    cli._execute.assert_awaited_once_with(
        "create",
        params={
            "path": "notes",
            "template": "daily",
            "name": "My Note",
        },
        flags=None,
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


async def test_write_with_backslash_escapes(cli):
    cli._execute.return_value = "Created: note.md\n"
    await cli.vault.write("note.md", r"C:\notes\temp")
    assert cli._execute.await_args_list == [
        call(
            "create",
            params={"path": "note.md", "content": "C:\\"},
            flags=["overwrite"],
        ),
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
    cli._execute.return_value = VAULT_INFO
    result = await cli.vault.info()
    assert result == VaultInfo(
        name="TestVault",
        path="/vaults/TestVault",
        files=47,
        folders=14,
        size=2825,
    )
    cli._execute.assert_awaited_once_with("vault")


async def test_info_counts_are_numbers(cli):
    cli._execute.return_value = VAULT_INFO
    result = await cli.vault.info()
    assert isinstance(result.files, int)
    assert isinstance(result.folders, int)
    assert isinstance(result.size, int)


async def test_info_unexpected_output(cli):
    cli._execute.return_value = "not a field list\n"
    with pytest.raises(CLIParseError) as exc_info:
        await cli.vault.info()
    assert exc_info.value.command == "vault"


@pytest.mark.parametrize("field", ["name", "path", "files", "folders", "size"])
async def test_info_without_a_required_field(cli, field):
    cli._execute.return_value = drop_field(VAULT_INFO, field)
    with pytest.raises(CLIParseError):
        await cli.vault.info()


async def test_file_info(cli):
    cli._execute.return_value = FILE_INFO
    result = await cli.vault.file_info("note.md")
    assert result == FileInfo(
        path="note.md",
        name="note",
        extension="md",
        size=137,
        created=datetime(2026, 8, 15, 23, 26, 39, 339000, tzinfo=UTC),
        modified=datetime(2026, 8, 15, 23, 26, 39, 341000, tzinfo=UTC),
    )
    cli._execute.assert_awaited_once_with("file", params={"path": "note.md"})


async def test_file_info_reads_the_timestamps_as_milliseconds(cli):
    cli._execute.return_value = FILE_INFO
    result = await cli.vault.file_info("note.md")
    assert result.created.timestamp() * 1000 == 1786836399339
    assert result.modified.timestamp() * 1000 == 1786836399341
    assert isinstance(result.size, int)


@pytest.mark.parametrize(
    ("field", "printed"), [("created", "1786836399339"), ("modified", "1786836399341")]
)
async def test_file_info_reads_a_small_timestamp_as_milliseconds_too(
    cli, field, printed
):
    # The CLI prints milliseconds whatever the number is, so the unit is
    # not for pydantic to guess: it reads a small number as seconds,
    # which would date a file from days after the epoch to 2001.
    cli._execute.return_value = FILE_INFO.replace(printed, "1000000000")
    result = await cli.vault.file_info("note.md")
    assert getattr(result, field) == datetime(1970, 1, 12, 13, 46, 40, tzinfo=UTC)


async def test_file_info_reads_a_timestamp_from_before_the_epoch(cli):
    # A file older than 1970 records a negative number of milliseconds.
    cli._execute.return_value = FILE_INFO.replace("1786836399339", "-315619200000")
    result = await cli.vault.file_info("note.md")
    assert result.created == datetime(1960, 1, 1, tzinfo=UTC)


async def test_file_info_without_an_extension(cli):
    # A file whose name carries no extension prints the field empty
    # rather than leaving it out.
    cli._execute.return_value = (
        "path\tnotes/note\nname\tnote\nextension\t\nsize\t18\n"
        "created\t1786848833424\nmodified\t1786848833424\n"
    )
    result = await cli.vault.file_info("notes/note")
    assert result.extension == ""
    assert result.name == "note"


@pytest.mark.parametrize("field", ["created", "modified"])
@pytest.mark.parametrize("printed", ["just now", "1.5", "1786836399.0", "9" * 20])
async def test_file_info_without_a_timestamp_in_milliseconds(cli, field, printed):
    cli._execute.return_value = drop_field(FILE_INFO, field) + f"{field}\t{printed}\n"
    with pytest.raises(CLIParseError) as exc_info:
        await cli.vault.file_info("note.md")
    assert exc_info.value.command == "file"


async def test_file_info_reads_back_the_json_it_writes(cli):
    # Only a plain number is read as milliseconds, so the timestamps the
    # model prints are timestamps it can be built from again.
    cli._execute.return_value = FILE_INFO
    result = await cli.vault.file_info("note.md")
    assert FileInfo.model_validate_json(result.model_dump_json()) == result


@pytest.mark.parametrize(
    "field", ["path", "name", "extension", "size", "created", "modified"]
)
async def test_file_info_without_a_required_field(cli, field):
    cli._execute.return_value = drop_field(FILE_INFO, field)
    with pytest.raises(CLIParseError):
        await cli.vault.file_info("note.md")


async def test_folder_info(cli):
    cli._execute.return_value = FOLDER_INFO
    result = await cli.vault.folder_info("notes")
    assert result == FolderInfo(path="notes", files=3, folders=0, size=305)
    assert isinstance(result.files, int)
    assert isinstance(result.folders, int)
    assert isinstance(result.size, int)
    cli._execute.assert_awaited_once_with("folder", params={"path": "notes"})


async def test_folder_info_unexpected_output(cli):
    cli._execute.return_value = FOLDER_INFO.replace("files\t3", "files\tthree")
    with pytest.raises(CLIParseError) as exc_info:
        await cli.vault.folder_info("notes")
    assert exc_info.value.command == "folder"


@pytest.mark.parametrize("field", ["path", "files", "folders", "size"])
async def test_folder_info_without_a_required_field(cli, field):
    cli._execute.return_value = drop_field(FOLDER_INFO, field)
    with pytest.raises(CLIParseError):
        await cli.vault.folder_info("notes")


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
    cli._execute.return_value = WORD_COUNT
    result = await cli.vault.wordcount("note.md")
    assert result == WordCount(words=500, characters=2800)
    assert isinstance(result.words, int)
    assert isinstance(result.characters, int)
    cli._execute.assert_awaited_once_with("wordcount", params={"path": "note.md"})


async def test_wordcount_non_numeric(cli):
    cli._execute.return_value = "words: many\ncharacters: 2800\n"
    with pytest.raises(CLIParseError) as exc_info:
        await cli.vault.wordcount("note.md")
    assert exc_info.value.command == "wordcount"


@pytest.mark.parametrize("field", ["words", "characters"])
async def test_wordcount_without_a_required_field(cli, field):
    cli._execute.return_value = drop_field(WORD_COUNT, field, separator=": ")
    with pytest.raises(CLIParseError):
        await cli.vault.wordcount("note.md")


# Only `sync:status` mixes a sentence into its fields. For the rest an
# extra line is output this library does not understand.
async def test_info_with_a_stray_line(cli):
    cli._execute.return_value = VAULT_INFO + "and one more thing\n"
    with pytest.raises(CLIParseError):
        await cli.vault.info()


async def test_folder_info_with_a_stray_line(cli):
    cli._execute.return_value = FOLDER_INFO + "and one more thing\n"
    with pytest.raises(CLIParseError):
        await cli.vault.folder_info("notes")


async def test_file_info_with_a_stray_line(cli):
    cli._execute.return_value = FILE_INFO + "and one more thing\n"
    with pytest.raises(CLIParseError):
        await cli.vault.file_info("note.md")


async def test_wordcount_with_a_stray_line(cli):
    cli._execute.return_value = WORD_COUNT + "and one more thing\n"
    with pytest.raises(CLIParseError):
        await cli.vault.wordcount("note.md")
