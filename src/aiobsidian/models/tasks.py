from __future__ import annotations

from pydantic import BaseModel

_TODO_STATUS = " "


class Task(BaseModel):
    """A task in a note.

    Attributes:
        status: The character between the brackets: a space for an open
            task, `"x"` for a completed one, anything else for one of
            the custom statuses a theme or plugin defines.
        text: The task's line as the note writes it, list marker and
            checkbox included. Empty when the CLI could not read the
            line back.
        file: Path to the note holding the task.
        line: Line number within that note, counting from 1 — the
            number `tasks.toggle()`, `tasks.complete()` and
            `tasks.reopen()` take.
    """

    status: str
    text: str
    file: str
    line: int

    @property
    def done(self) -> bool:
        """Whether Obsidian counts the task as done.

        Returns:
            `False` only while the checkbox is blank, which is how
            `tasks.list(done=True)` and `tasks.list(todo=True)` tell the
            two apart.
        """
        return self.status != _TODO_STATUS
