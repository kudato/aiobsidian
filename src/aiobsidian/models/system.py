from pydantic import BaseModel, Field


class Versions(BaseModel):
    obsidian: str
    self_: str = Field(alias="self")


class ServerStatus(BaseModel):
    ok: str
    service: str
    authenticated: bool
    versions: Versions
