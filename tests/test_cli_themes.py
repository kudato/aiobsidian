from __future__ import annotations


async def test_list(cli):
    cli._execute.return_value = "Minimal\nThings\n"
    result = await cli.themes.list()
    assert result == ["Minimal", "Things"]
    cli._execute.assert_awaited_once_with("themes", flags=None)


async def test_list_with_versions(cli):
    cli._execute.return_value = "Minimal\t7.7.0\n"
    result = await cli.themes.list(versions=True)
    assert result == ["Minimal\t7.7.0"]
    cli._execute.assert_awaited_once_with("themes", flags=["versions"])


async def test_list_only_default_installed(cli):
    cli._execute.return_value = ""
    result = await cli.themes.list()
    assert result == []


async def test_current(cli):
    cli._execute.return_value = "(default)\n"
    result = await cli.themes.current()
    assert result == "(default)"
    cli._execute.assert_awaited_once_with("theme")


async def test_set(cli):
    cli._execute.return_value = ""
    await cli.themes.set("Minimal")
    cli._execute.assert_awaited_once_with("theme:set", params={"name": "Minimal"})


async def test_install(cli):
    cli._execute.return_value = ""
    await cli.themes.install("Minimal")
    cli._execute.assert_awaited_once_with(
        "theme:install", params={"name": "Minimal"}, flags=None
    )


async def test_install_with_enable(cli):
    cli._execute.return_value = ""
    await cli.themes.install("Minimal", enable=True)
    cli._execute.assert_awaited_once_with(
        "theme:install", params={"name": "Minimal"}, flags=["enable"]
    )


async def test_uninstall(cli):
    cli._execute.return_value = ""
    await cli.themes.uninstall("Minimal")
    cli._execute.assert_awaited_once_with("theme:uninstall", params={"name": "Minimal"})
