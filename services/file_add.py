import uuid
from pydantic import BaseModel
from fastapi import BackgroundTasks
from utils.bailian import *
from typing import List, Optional
from utils.files_utils import File


class FileAddRequest(BaseModel):
    id: str
    files: Optional[List[File]] = None


class FileAddResponse(BaseModel):
    task_id: str

    
def file_add(request: FileAddRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(_file_add, request, task_id=task_id)
    return FileAddResponse(task_id=task_id)


def _file_add(request: FileAddRequest, task_id: str):
    add_files(task_id, request.id, request.files)
