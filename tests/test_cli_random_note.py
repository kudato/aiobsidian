from __future__ import annotations


async def test_open(cli):
    cli._execute.return_value = ""
    await cli.random.open()
    cli._execute.assert_awaited_once_with("random")


async def test_read(cli):
    cli._execute.return_value = "# Random Note\n\nSome content here."
    result = await cli.random.read()
    assert result == "# Random Note\n\nSome content here."
    cli._execute.assert_awaited_once_with("random:read")
