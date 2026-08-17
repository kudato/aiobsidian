from __future__ import annotations

import pytest

from aiobsidian._exceptions import CLIParseError
from aiobsidian.models.publish import PublishChange, PublishSite

# Obsidian prints the custom domain only for a site that has one.
SITE_INFO = (
    "slug\tmysite\n"
    "url\thttps://publish.obsidian.md/mysite\n"
    "custom\thttps://notes.example.com\n"
)

PUBLISHED_FILES = "about.md\nindex.md\n"

# The scan walks the published files first and the vault tree after, so
# a new file is always reported last.
PUBLISH_STATUS = "changed\tindex.md\ndeleted\tnotes/gone.md\nnew\tnotes/draft.md\n"


async def test_open(cli):
    cli._execute.return_value = "https://publish.obsidian.md/mysite/notes/index\n"
    result = await cli.publish.open("notes/index.md")
    assert result == "https://publish.obsidian.md/mysite/notes/index"
    cli._execute.assert_awaited_once_with(
        "publish:open", params={"path": "notes/index.md"}
    )


async def test_open_active_file(cli):
    cli._execute.return_value = "https://publish.obsidian.md/mysite/index\n"
    await cli.publish.open()
    cli._execute.assert_awaited_once_with("publish:open", params=None)


async def test_site(cli):
    cli._execute.return_value = SITE_INFO
    result = await cli.publish.site()
    assert result == PublishSite(
        slug="mysite",
        url="https://publish.obsidian.md/mysite",
        custom_domain="https://notes.example.com",
    )
    cli._execute.assert_awaited_once_with("publish:site")


async def test_site_without_a_custom_domain(cli):
    cli._execute.return_value = (
        "slug\tmysite\nurl\thttps://publish.obsidian.md/mysite\n"
    )
    result = await cli.publish.site()
    assert result.custom_domain is None


async def test_site_without_the_url_field(cli):
    cli._execute.return_value = "slug\tmysite\n"
    with pytest.raises(CLIParseError) as exc_info:
        await cli.publish.site()
    assert exc_info.value.command == "publish:site"


async def test_list(cli):
    cli._execute.return_value = PUBLISHED_FILES
    result = await cli.publish.list()
    assert result == ["about.md", "index.md"]
    cli._execute.assert_awaited_once_with("publish:list")


async def test_status(cli):
    cli._execute.return_value = PUBLISH_STATUS
    result = await cli.publish.status()
    assert result == [
        PublishChange(type="changed", path="index.md"),
        PublishChange(type="deleted", path="notes/gone.md"),
        PublishChange(type="new", path="notes/draft.md"),
    ]
    cli._execute.assert_awaited_once_with("publish:status")


async def test_status_with_an_unexpected_row(cli):
    cli._execute.return_value = "new\tnotes/draft.md\textra\n"
    with pytest.raises(CLIParseError) as exc_info:
        await cli.publish.status()
    assert exc_info.value.command == "publish:status"


async def test_status_up_to_date(cli):
    cli._execute.return_value = "No changes.\n"
    result = await cli.publish.status()
    assert result == []


async def test_add(cli):
    cli._execute.return_value = "Published: notes/new.md\n"
    result = await cli.publish.add("notes/new.md")
    assert result == "Published: notes/new.md"
    cli._execute.assert_awaited_once_with(
        "publish:add", params={"path": "notes/new.md"}
    )


async def test_add_active_file(cli):
    cli._execute.return_value = "Published: index.md\n"
    await cli.publish.add()
    cli._execute.assert_awaited_once_with("publish:add", params=None)


async def test_add_changed(cli):
    cli._execute.return_value = "Published 2 files:\nindex.md\nnotes/draft.md\n"
    result = await cli.publish.add(changed=True)
    assert result == "Published 2 files:\nindex.md\nnotes/draft.md"
    cli._execute.assert_awaited_once_with("publish:add", flags=["changed"])


async def test_remove(cli):
    cli._execute.return_value = "Unpublished: notes/old.md\n"
    await cli.publish.remove("notes/old.md")
    cli._execute.assert_awaited_once_with(
        "publish:remove", params={"path": "notes/old.md"}
    )


async def test_remove_active_file(cli):
    cli._execute.return_value = "Unpublished: index.md\n"
    await cli.publish.remove()
    cli._execute.assert_awaited_once_with("publish:remove", params=None)
