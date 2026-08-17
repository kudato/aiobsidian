from __future__ import annotations

import json

from aiobsidian.models.bookmarks import Bookmark

# `verbose` prints the type and the title beside the value. A file
# bookmark carries its subpath in the value, a search bookmark falls back
# to its query for a title, a url bookmark left untitled has none, and a
# group points at nothing at all.
BOOKMARKS = [
    {"type": "file", "value": "notes/important.md", "title": "important"},
    {"type": "file", "value": "notes/important.md#Setup", "title": "important#Setup"},
    {"type": "folder", "value": "projects", "title": "projects"},
    {"type": "search", "value": "tag:#todo", "title": "tag:#todo"},
    {"type": "url", "value": "https://obsidian.md", "title": ""},
    {"type": "group", "value": "", "title": "Reading"},
]


async def test_list(cli):
    cli._execute.return_value = json.dumps(BOOKMARKS)
    result = await cli.bookmarks.list()
    assert result == [
        Bookmark(type="file", value="notes/important.md", title="important"),
        Bookmark(
            type="file", value="notes/important.md#Setup", title="important#Setup"
        ),
        Bookmark(type="folder", value="projects", title="projects"),
        Bookmark(type="search", value="tag:#todo", title="tag:#todo"),
        Bookmark(type="url", value="https://obsidian.md", title=""),
        Bookmark(type="group", value="", title="Reading"),
    ]
    cli._execute.assert_awaited_once_with(
        "bookmarks", flags=["verbose"], output_format="json"
    )


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
