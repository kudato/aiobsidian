from __future__ import annotations


async def test_open(cli):
    cli._execute.return_value = ""
    await cli.random.open()
    cli._execute.assert_awaited_once_with("random")


async def test_read_drops_the_path_header(cli):
    cli._execute.return_value = "notes/pick.md\n\n# Random Note\n\nSome content.\n"
    result = await cli.random.read()
    assert result == "# Random Note\n\nSome content.\n"
    cli._execute.assert_awaited_once_with("random:read")
