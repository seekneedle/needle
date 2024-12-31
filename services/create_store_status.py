from pydantic import BaseModel
from data.task import TaskStatus, CreateStoreTaskEntity
from data.store import StoreEntity, DocumentEntity
from typing import List, Optional


class Document(BaseModel):
    doc_name: str
    doc_id: str
    status: str


class CreateStoreStatusResponse(BaseModel):
    task_id: str
    status: str
    message: Optional[str] = None
    id: Optional[str] = None
    documents: Optional[List[Document]] = None


def create_store_status(task_id):
    task_entry = CreateStoreTaskEntity.query_first(task_id=task_id)
    status = task_entry.status
    store = StoreEntity.query_first(category_id=task_entry.category_id)
    if status == TaskStatus.COMPLETED:
        index_id = store.index_id
        documents = DocumentEntity.query_all(category_id=task_entry.category_id)
        docs = []
        for doc in documents:
            docs.append(Document(doc_name=doc.doc_name, doc_id=doc.doc_id))
        return CreateStoreStatusResponse(task_id=task_id, status=status, id=store.store_id, documents=docs)
    args = {
        'task_id': task_id,
        'status': status
    }
    if store.index_id:
        args['id'] = store.index_id
    if store.message:
        args['message'] = store.message
    return CreateStoreStatusResponse(**args)


if __name__ == '__main__':
    tasks = CreateStoreTaskEntity.query_all()
    for task in tasks:
        print(f'id: {task.task_id}, status: {task.status}, create_time: {task.create_time}, modify_time: {task.modify_time}')
