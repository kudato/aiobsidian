from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Versions(BaseModel):
    """Version information for Obsidian and the REST API plugin.

    Attributes:
        obsidian: Obsidian application version string.
        self_: REST API plugin version string (aliased from `"self"`).
    """

    model_config = ConfigDict(populate_by_name=True)

    obsidian: str
    self_: str = Field(alias="self")


class ServerStatus(BaseModel):
    """Status response from the Obsidian REST API root endpoint.

    Attributes:
        status: Status message (typically `"OK"`).
        service: Service identifier string.
        authenticated: Whether the request was authenticated.
        versions: Version information for Obsidian and the plugin.
    """

    model_config = ConfigDict(extra="ignore")

    status: str
    service: str
    authenticated: bool
    versions: Versions
