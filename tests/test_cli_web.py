from __future__ import annotations


async def test_open(cli):
    cli._execute.return_value = ""
    await cli.web.open("https://example.com")
    cli._execute.assert_awaited_once_with("web", params={"url": "https://example.com"})
