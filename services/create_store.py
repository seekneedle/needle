import uuid
from pydantic import BaseModel
from fastapi import BackgroundTasks
from utils.config import config
from utils.security import decrypt
from utils.log import log
from utils.bailian import create_client
from alibabacloud_bailian20231229 import models as bailian_20231229_models
from alibabacloud_tea_util import models as util_models
import traceback
from data.task import TaskEntry, TaskStatus


class File(BaseModel):
    name: str
    file_base64: str


class CreateStoreEntity(BaseModel):
    name: str
    chunking_size: int
    overlap: int
    seperator: str
    files: list[File]


def _create_store(request: CreateStoreEntity, task_id: str):
    task = TaskEntry(task_id=task_id)
    task.set_status(TaskStatus.RUNNING)
    workspace_id = decrypt(config['workspace_id'])
    runtime = util_models.RuntimeOptions()
    headers = {}
    client = create_client()
    # 1. 新增类目
    category_name = request.name
    category_type = 'UNSTRUCTURED'
    parent_category_id = decrypt(config['parent_category_id'])
    add_category_request = bailian_20231229_models.AddCategoryRequest(
        parent_category_id=parent_category_id,
        category_name=category_name,
        category_type=category_type
    )
    try:
        result = client.add_category_with_options(workspace_id, add_category_request, headers, runtime)
        category_id = result.body.data.category_id
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for _create_store/add_category, e: {e}, trace: {trace_info}')
        task.set_status(TaskStatus.FAIL)
        return
    # 2. 上传文件
    for file in request.files:
        # 2.1. 申请文档上传租约
        file_name = file.name

        apply_file_upload_lease_request = bailian_20231229_models.ApplyFileUploadLeaseRequest(
            file_name=file_name,
            md_5='ccc',
            size_in_bytes='30'
        )
        try:
            client.apply_file_upload_lease_with_options(category_id, workspace_id, apply_file_upload_lease_request, headers,
                                                        runtime)
        except Exception as e:
            trace_info = traceback.format_exc()
            log.error(f'Exception for _create_store/add_lease, e: {e}, trace: {trace_info}')
            task.set_status(TaskStatus.FAIL)
            return


def create_store(request: CreateStoreEntity, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(_create_store, request, task_id=task_id)
    return task_id


if __name__ == '__main__':
    _create_store(CreateStoreEntity(name='test', chunking_size=0, overlap=0, seperator='', files=[]), 'aaa')
