from pydantic import BaseModel
from typing import List, Optional
from utils.files_utils import Document
from utils.bailian import list_file


class FileListResponse(BaseModel):
    documents: Optional[List[Document]] = None


def file_list(index_id: str):
    all_files = list_file(index_id)
    documents = []
    for file in all_files:
        documents.append(Document(doc_id=file.id, doc_name=file.name, status=file.status, message=file.message))
    return FileListResponse(documents=documents)
