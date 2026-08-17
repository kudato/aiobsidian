from __future__ import annotations


def drop_field(output: str, field: str, separator: str = "\t") -> str:
    """Print a field block the way the CLI would without one field.

    The record commands print a field per line, and which of those lines
    Obsidian may leave out is what the models say. Removing one is how a
    test asks whether a field is really required.

    Args:
        output: Field block as the CLI prints it.
        field: Name of the field to leave out.
        separator: Separator between key and value.

    Returns:
        The same block without that field's line.
    """
    prefix = f"{field}{separator}"
    return "".join(
        line for line in output.splitlines(keepends=True) if not line.startswith(prefix)
    )
