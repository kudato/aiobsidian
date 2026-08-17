from __future__ import annotations

import json

BOOKMARKS_LIST = [
    {"value": "notes/important.md"},
    {"value": "projects/"},
]


async def test_list(cli):
    cli._execute.return_value = json.dumps(BOOKMARKS_LIST)
    result = await cli.bookmarks.list()
    assert result == ["notes/important.md", "projects/"]
    cli._execute.assert_awaited_once_with("bookmarks", output_format="json")


async def test_list_empty(cli):
    cli._execute.return_value = "No bookmarks found.\n"
    result = await cli.bookmarks.list()
    assert result == []


async def test_add_file(cli):
    cli._execute.return_value = ""
    await cli.bookmarks.add(file="notes/important.md")
    cli._execute.assert_awaited_once_with(
        "bookmark", params={"file": "notes/important.md"}
    )


async def test_add_folder(cli):
    cli._execute.return_value = ""
    await cli.bookmarks.add(folder="projects/")
    cli._execute.assert_awaited_once_with("bookmark", params={"folder": "projects/"})


async def test_add_url(cli):
    cli._execute.return_value = ""
    await cli.bookmarks.add(url="https://example.com", title="Example")
    cli._execute.assert_awaited_once_with(
        "bookmark", params={"url": "https://example.com", "title": "Example"}
    )


async def test_add_search(cli):
    cli._execute.return_value = ""
    await cli.bookmarks.add(search="TODO")
    cli._execute.assert_awaited_once_with("bookmark", params={"search": "TODO"})


async def test_add_empty_title(cli):
    cli._execute.return_value = ""
    await cli.bookmarks.add(file="note.md", title="")
    cli._execute.assert_awaited_once_with(
        "bookmark", params={"file": "note.md", "title": ""}
    )


async def test_add_with_subpath(cli):
    cli._execute.return_value = ""
    await cli.bookmarks.add(file="note.md", subpath="#heading")
    cli._execute.assert_awaited_once_with(
        "bookmark", params={"file": "note.md", "subpath": "#heading"}
    )
