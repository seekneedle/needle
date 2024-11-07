import uuid
from pydantic import BaseModel
from fastapi import BackgroundTasks
from data.database import db, TableModel, values
from sqlalchemy import Column, String, DateTime, func
from utils.config import config
from utils.security import decrypt
from utils.log import log
from utils.bailian import create_client
from alibabacloud_bailian20231229 import models as bailian_20231229_models
from alibabacloud_tea_util import models as util_models
import traceback


class File(BaseModel):
    name: str
    file_base64: str


class CreateStoreEntity(BaseModel):
    name: str
    chunking_size: int
    overlap: int
    seperator: str
    files: list[File]


class CreateStoreTask(TableModel):
    task_id = Column(String)
    status = Column(String)
    create_time = Column(DateTime, server_default=func.now())
    modify_time = Column(DateTime, server_default=func.now())


def _create_store(request: CreateStoreEntity, task_id: str):
    # 1. 新增类目
    workspace_id = decrypt(config['workspace_id'])
    category_name = request.name
    category_type = 'UNSTRUCTURED'
    parent_category_id = decrypt(config['parent_category_id'])
    client = create_client()
    add_category_request = bailian_20231229_models.AddCategoryRequest(
        parent_category_id=parent_category_id,
        category_name=category_name,
        category_type=category_type
    )
    runtime = util_models.RuntimeOptions()
    headers = {}
    try:
        result = client.add_category_with_options(workspace_id, add_category_request, headers, runtime)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f"Exception for _create_store/add_category, e: {e}, trace: {trace_info}")
        with db:
            db.update_records(CreateStoreTask, task_id=task_id, values=values(status='fail', modify_time=func.now()))
    print("done")


def create_store(request: CreateStoreEntity, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    with db:
        db.add_record(CreateStoreTask, task_id=task_id, status='running')
    background_tasks.add_task(_create_store, request, task_id=task_id)
    return task_id


if __name__ == '__main__':
    _create_store(CreateStoreEntity(name="test", chunking_size=0, overlap=0,seperator='',files=[]), 'aaa')