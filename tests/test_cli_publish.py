from __future__ import annotations

import json

SITE_INFO = {"name": "My Site", "url": "https://publish.obsidian.md/mysite"}

PUBLISHED_FILES = [
    {"path": "index.md", "published": True},
    {"path": "about.md", "published": True},
]

PUBLISH_STATUS = {"path": "index.md", "published": True, "changed": False}


async def test_open(cli):
    cli._execute.return_value = ""
    await cli.publish.open("notes/index.md")
    cli._execute.assert_awaited_once_with(
        "publish:open", params={"path": "notes/index.md"}
    )


async def test_open_no_path(cli):
    cli._execute.return_value = ""
    await cli.publish.open()
    cli._execute.assert_awaited_once_with("publish:open", params=None)


async def test_site(cli):
    cli._execute.return_value = json.dumps(SITE_INFO)
    result = await cli.publish.site()
    assert result == SITE_INFO
    cli._execute.assert_awaited_once_with("publish:site")


async def test_list(cli):
    cli._execute.return_value = json.dumps(PUBLISHED_FILES)
    result = await cli.publish.list()
    assert result == PUBLISHED_FILES
    cli._execute.assert_awaited_once_with("publish:list")


async def test_status(cli):
    cli._execute.return_value = json.dumps(PUBLISH_STATUS)
    result = await cli.publish.status("index.md")
    assert result == PUBLISH_STATUS
    cli._execute.assert_awaited_once_with("publish:status", params={"path": "index.md"})


async def test_status_no_path(cli):
    cli._execute.return_value = json.dumps({"published": 5, "changed": 2})
    result = await cli.publish.status()
    assert result == {"published": 5, "changed": 2}
    cli._execute.assert_awaited_once_with("publish:status", params=None)


async def test_add(cli):
    cli._execute.return_value = ""
    await cli.publish.add("notes/new.md")
    cli._execute.assert_awaited_once_with(
        "publish:add", params={"path": "notes/new.md"}
    )


async def test_add_all(cli):
    cli._execute.return_value = ""
    await cli.publish.add()
    cli._execute.assert_awaited_once_with("publish:add", params=None)


async def test_remove(cli):
    cli._execute.return_value = ""
    await cli.publish.remove("notes/old.md")
    cli._execute.assert_awaited_once_with(
        "publish:remove", params={"path": "notes/old.md"}
    )
