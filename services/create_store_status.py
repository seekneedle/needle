from pydantic import BaseModel
from typing import List, Optional
from utils.bailian import *
import traceback


class Document(BaseModel):
    doc_name: str
    doc_id: str
    status: str
    message: Optional[str] = None


class StoreStatusResponse(BaseModel):
    task_id: str
    status: str
    message: Optional[str] = None
    id: Optional[str] = None
    documents: Optional[List[Document]] = None


def task_status(task_id):
    task = StoreTaskEntity.query_first(task_id=task_id)
    store = StoreEntity.query_first(id=task.store_id)
    documents = []

    if store and task.job_id:
        try:
            result = get_index_result(store.index_id, task.job_id)
            for doc in result.body.data.documents:
                file_entity = FileEntity.query_first(store_id=store.id, doc_id=doc.doc_id)
                file_task = FileTaskEntity.query_first(task_id=task_id, file_id=file_entity.id)
                file_task.set(status=doc.status, message=doc.message)
            for file_task in FileTaskEntity.query_all(task_id=task_id):
                doc = FileEntity.query_first(id=file_task.file_id)
                documents.append(Document(doc_name=doc.doc_name, doc_id=doc.doc_id, status=file_task.status,
                                          message=file_task.message))
            task.set(status=result.body.data.status, message=result.body.message)
        except Exception as e:
            trace_info = traceback.format_exc()
            task.set(status=TaskStatus.FAILED,
                     message=f'Exception for task_status, task_id: {task_id}, e: {e}, trace: {trace_info}')

    return StoreStatusResponse(task_id=task_id, status=task.status, message=task.message, id=store.index_id,
                               documents=documents)


if __name__ == '__main__':
    tasks = StoreTaskEntity.query_all()
    for _task in tasks:
        print(
            f'id: {_task.task_id}, status: {_task.status}, create_time: {_task.create_time}, modify_time: {_task.modify_time}')
