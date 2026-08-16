from __future__ import annotations

from typing import Any

from ._base import BaseCLIResource


class CLITasksResource(BaseCLIResource):
    """CLI resource for task operations.

    The CLI addresses a task by the file it lives in and its line number;
    it has no task identifier and no command that creates one. Write a new
    task with `vault.append(path, "- [ ] ...")`.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def list(
        self,
        *,
        path: str | None = None,
        daily: bool = False,
        done: bool = False,
        todo: bool = False,
    ) -> list[dict[str, Any]]:
        """List tasks across the vault.

        Args:
            path: Restrict to tasks in files under this path.
            daily: If ``True``, only list tasks from the daily note.
            done: If ``True``, list only tasks whose status box is not
                blank: completed ones and any custom status character.
            todo: If ``True``, list only tasks with a blank status box.

        Returns:
            List of task objects, each with ``status``, ``text``, ``file``
            and ``line``.
        """
        params = {"path": path} if path is not None else None
        flags: list[str] = []
        if daily:
            flags.append("daily")
        if done:
            flags.append("done")
        if todo:
            flags.append("todo")
        output = await self._cli._execute(
            "tasks", params=params, flags=flags or None, output_format="json"
        )
        result: list[dict[str, Any]] = self._parse_json("tasks", output)
        return result

    async def toggle(self, path: str, line: int) -> None:
        """Toggle a task's completion status.

        Args:
            path: Path to the file containing the task.
            line: Line number of the task in the file, counting from 1.
        """
        await self._cli._execute(
            "task", params={"path": path, "line": str(line)}, flags=["toggle"]
        )

    async def complete(self, path: str, line: int) -> None:
        """Mark a task as done.

        Args:
            path: Path to the file containing the task.
            line: Line number of the task in the file, counting from 1.
        """
        await self._cli._execute(
            "task", params={"path": path, "line": str(line)}, flags=["done"]
        )

    async def reopen(self, path: str, line: int) -> None:
        """Mark a task as not done.

        Args:
            path: Path to the file containing the task.
            line: Line number of the task in the file, counting from 1.
        """
        await self._cli._execute(
            "task", params={"path": path, "line": str(line)}, flags=["todo"]
        )
