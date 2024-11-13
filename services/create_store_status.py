from pydantic import BaseModel
from data.task import TaskEntry, TaskStatus
from data.store import CreateStoreEntity, CreateStoreDocumentEntity
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
    task_entry = TaskEntry(task_id=task_id)
    task_entry.load()
    status = task_entry.status
    store = CreateStoreEntity(task_id=task_id)
    store.load()
    if status == TaskStatus.COMPLETED:
        index_id = store.index_id
        documents = CreateStoreDocumentEntity(task_id=task_id)
        docs = []
        for doc in documents.iter():
            docs.append(Document(doc_name=doc.doc_name, doc_id=doc.doc_id, status=doc.status))
        return CreateStoreStatusResponse(task_id=task_id, status=status, id=index_id, documents=docs)
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
    tasks = TaskEntry(task_id='1a9b800a-64e0-46ab-bfde-06aa080d1c8d')
    for task in tasks.iter():
        print(f'id: {task.task_id}, status: {task.status}, create_time: {task.create_time}, modify_time: {task.modify_time}')
