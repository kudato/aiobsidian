from pydantic import BaseModel


class Command(BaseModel):
    id: str
    name: str
