from __future__ import annotations

from ._base import BaseCLIResource


class CLIDevResource(BaseCLIResource):
    """CLI resource for developer/debugging tools.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def devtools(self) -> None:
        """Toggle Electron DevTools."""
        await self._cli._execute("devtools")

    async def eval(self, code: str) -> str:
        """Execute JavaScript in the Obsidian API context.

        Args:
            code: JavaScript code to evaluate.

        Returns:
            Evaluation result as a string.
        """
        output = await self._cli._execute("eval", params={"code": code})
        return output.strip()

    async def console(self, *, limit: int | None = None) -> list[str]:
        """Show console messages.

        Args:
            limit: Maximum number of messages to return.

        Returns:
            List of captured messages, each prefixed with its timestamp.
        """
        params: dict[str, str] = {}
        if limit is not None:
            params["limit"] = str(limit)
        output = await self._cli._execute("dev:console", params=params or None)
        return self._parse_lines(output)

    async def errors(self) -> list[str]:
        """Show JavaScript errors.

        Returns:
            List of captured errors, empty if none were captured.
        """
        output = await self._cli._execute("dev:errors")
        return self._parse_lines(output)

    async def screenshot(self, path: str) -> None:
        """Capture a screenshot of the Obsidian window.

        The CLI answers before the capture has been written, so the file
        may not exist yet when this returns. Poll for it rather than
        opening it straight away.

        Args:
            path: Where to write the PNG. A relative path is resolved
                against the vault root.
        """
        await self._cli._execute("dev:screenshot", params={"path": path})

    async def dom(
        self,
        selector: str,
        *,
        match_all: bool = False,
        text: bool = False,
        attr: str | None = None,
        css: str | None = None,
    ) -> str:
        """Inspect DOM elements.

        Args:
            selector: CSS selector for the element(s).
            match_all: If ``True``, match all elements instead of just the first.
            text: If ``True``, return text content only.
            attr: Return this attribute value from matched elements.
            css: Return this CSS property value from matched elements.

        Returns:
            DOM inspection result. The element's outer HTML unless one of
            ``text``, ``attr`` or ``css`` narrows it.

        Raises:
            TypeError: If more than one of ``text``, ``attr`` and ``css``
                is requested. The CLI answers only the first one it finds
                and drops the rest.
        """
        requested = [
            name
            for name, wanted in (("text", text), ("attr", attr), ("css", css))
            if wanted is not None and wanted is not False
        ]
        if len(requested) > 1:
            raise TypeError(
                f"dom() answers one of text, attr and css, not {len(requested)}: "
                f"got {', '.join(requested)}"
            )

        params: dict[str, str] = {"selector": selector}
        if attr is not None:
            params["attr"] = attr
        if css is not None:
            params["css"] = css
        flags: list[str] = []
        if match_all:
            flags.append("all")
        if text:
            flags.append("text")
        output = await self._cli._execute("dev:dom", params=params, flags=flags or None)
        return output.strip()

    async def css(self, selector: str, *, prop: str | None = None) -> str:
        """Inspect CSS styles.

        Args:
            selector: CSS selector for the element.
            prop: Specific CSS property to retrieve.

        Returns:
            CSS inspection result.
        """
        params: dict[str, str] = {"selector": selector}
        if prop is not None:
            params["prop"] = prop
        output = await self._cli._execute("dev:css", params=params)
        return output.strip()

    async def set_mobile(self, value: bool) -> None:
        """Turn mobile emulation on or off.

        Args:
            value: ``True`` enables emulation, ``False`` disables it.
        """
        flags = ["on"] if value else ["off"]
        await self._cli._execute("dev:mobile", flags=flags)

    async def set_capture(self, value: bool) -> None:
        """Start or stop capturing the console.

        What is captured is what `console()` and `errors()` read.

        Args:
            value: ``True`` starts capturing, ``False`` stops it.
        """
        flags = ["on"] if value else ["off"]
        await self._cli._execute("dev:debug", flags=flags)

    async def cdp(self, method: str, params: str) -> str:
        """Execute a Chrome DevTools Protocol command.

        Args:
            method: CDP method name.
            params: JSON-encoded parameters.

        Returns:
            CDP command result.
        """
        output = await self._cli._execute(
            "dev:cdp", params={"method": method, "params": params}
        )
        return output.strip()
