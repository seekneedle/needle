import uuid

from pydantic import BaseModel
from fastapi import BackgroundTasks

from data.database import connect_db
from utils.bailian import *
from data.task import StoreTaskEntity
from typing import List, Optional
from utils.files_utils import File


class CreateStoreRequest(BaseModel):
    name: str
    chunk_size: Optional[int] = None
    overlap_size: Optional[int] = None
    separator: Optional[str] = None
    files: Optional[List[File]] = None


class CreateStoreResponse(BaseModel):
    task_id: str


def _create_store(request: CreateStoreRequest, task_id: str):
    store = add_store(task_id, request.name, request.chunk_size, request.overlap_size, request.separator)
    if store:
        add_files(task_id, store.index_id, request.files)


def create_store(request: CreateStoreRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(_create_store, request, task_id=task_id)
    return CreateStoreResponse(task_id=task_id)


if __name__ == '__main__':
    connect_db()

    for _task in StoreTaskEntity.query_all():
        _task.delete()

    _create_store(CreateStoreRequest(name='test', files=[File(
        name='server.txt',
        file_content=b'Test Doc')]),
                  'aaa')
    for _task in StoreTaskEntity.query_all():
        print(f'task_id: {_task.task_id}, status: {_task.status}, '
              f'create_time: {_task.create_time}, modify_time: {_task.modify_time}')
