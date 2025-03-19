from pydantic import BaseModel
from typing import List, Optional
from utils.files_utils import Document
from utils.bailian import list_file, list_file_batch
from utils.log import log


class FileListResponse(BaseModel):
    documents: Optional[List[Document]] = None

class FileListBatchRequest(BaseModel):
    index_id: str
    file_names: list[str]

def file_list(index_id: str, file_name: str):
    all_files = list_file(index_id, file_name)
    documents = []
    for file in all_files:
        documents.append(Document(doc_id=file.id, doc_name=file.name, status=file.status, message=file.message))
    return FileListResponse(documents=documents)

def file_list_abnormal(index_id: str, file_name: str):
    all_files = list_file(index_id, file_name)
    documents = [Document(doc_id=f.id, doc_name=f.name, status=f.status, message=f.message) for f in all_files if f.status != 'FINISH']
    return FileListResponse(documents=documents)

def file_list_batch(index_id: str, file_names: list[str]):
    all_files = list_file_batch(index_id, file_names)
    documents = [Document(doc_id=f.id, doc_name=f.name, status=f.status, message=f.message) for f in all_files]
    # found_names = set(f.name for f in all_files)
    # non_exist_names = set(file_names) - found_names
    # for file_name in non_exist_names:
    #     documents.append(Document(doc_id='', doc_name=file_name, status='NOT_EXISTS', message='不存在'))
    return FileListResponse(documents=documents)
