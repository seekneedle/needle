from pydantic import BaseModel
from typing import List, Optional
from utils.files_utils import Document
from data.store import StoreEntity
from utils.bailian import list_file


class FileListResponse(BaseModel):
    documents: Optional[List[Document]] = None


def file_list(index_id: str):
    store = StoreEntity.query_first(index_id=index_id)
    category_id = store.category_id
    all_files = list_file(category_id)
    documents = []
    for file in all_files:
        documents.append(Document(doc_id=file.file_id, doc_name=file.file_name, status=file.status))
    return FileListResponse(documents=documents)
