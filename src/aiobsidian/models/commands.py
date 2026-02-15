from pydantic import BaseModel


class Command(BaseModel):
    """An Obsidian command.

    Attributes:
        id: Unique command identifier (e.g. `"editor:toggle-bold"`).
        name: Human-readable command name (e.g. `"Toggle bold"`).
    """

    id: str
    name: str
