
from pydantic import BaseModel


class CreateStoreEntity(BaseModel):
    name: str
    chunking_size: int
    overlap: int
    seperator: str


def create_store(body, tasks):
    pass
