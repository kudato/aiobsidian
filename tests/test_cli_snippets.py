from __future__ import annotations


async def test_list(cli):
    cli._execute.return_value = "custom-styles\nhide-sidebar\n"
    result = await cli.snippets.list()
    assert result == ["custom-styles", "hide-sidebar"]
    cli._execute.assert_awaited_once_with("snippets")


async def test_list_none_installed(cli):
    cli._execute.return_value = ""
    result = await cli.snippets.list()
    assert result == []


async def test_enabled(cli):
    cli._execute.return_value = "custom-styles\n"
    result = await cli.snippets.enabled()
    assert result == ["custom-styles"]
    cli._execute.assert_awaited_once_with("snippets:enabled")


async def test_enable(cli):
    cli._execute.return_value = ""
    await cli.snippets.enable("custom-styles")
    cli._execute.assert_awaited_once_with(
        "snippet:enable", params={"name": "custom-styles"}
    )


async def test_disable(cli):
    cli._execute.return_value = ""
    await cli.snippets.disable("custom-styles")
    cli._execute.assert_awaited_once_with(
        "snippet:disable", params={"name": "custom-styles"}
    )
