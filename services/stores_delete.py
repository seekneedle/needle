from pydantic import BaseModel
from typing import List, Optional
from utils.bailian import delete_store_and_files


class DeleteStoreRequest(BaseModel):
    ids: Optional[List[str]] = None


class DeleteStoreResponse(BaseModel):
    ids: Optional[List[str]] = None


def delete_store(ids):
    ids = delete_store_and_files(ids)
    return DeleteStoreResponse(ids=ids)
