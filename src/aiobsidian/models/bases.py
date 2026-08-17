from __future__ import annotations

from pydantic import BaseModel


class BaseView(BaseModel):
    """A view defined in a base file.

    Attributes:
        name: View name, the one `bases.query(view=)` takes.
        type: How the view presents the items it collects, such as
            `"table"` or `"cards"`.
    """

    name: str
    type: str
