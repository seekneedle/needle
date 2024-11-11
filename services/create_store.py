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
from utils.files_utils import save_file_to_index_path, calculate_md5, read_file
import os
import requests


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
        if result.status_code != 200 or not result.body.success:
            raise RuntimeError(result.body)
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
        file_path = save_file_to_index_path(task_id, file_name, file.file_base64)
        md_5 = calculate_md5(file_path)
        size_in_bytes = str(os.path.getsize(file_path))
        apply_file_upload_lease_request = bailian_20231229_models.ApplyFileUploadLeaseRequest(
            file_name=file_name,
            md_5=md_5,
            size_in_bytes=size_in_bytes
        )
        try:
            result = client.apply_file_upload_lease_with_options(category_id, workspace_id,
                                                              apply_file_upload_lease_request,
                                                        headers,
                                                        runtime)
            if result.status_code != 200 or not result.body.success:
                raise RuntimeError(result.body)
            lease_id = result.body.data.file_upload_lease_id
            url = result.body.data.param.url
            upload_file_headers = result.body.data.param.headers
        except Exception as e:
            trace_info = traceback.format_exc()
            log.error(f'Exception for _create_store/add_lease, e: {e}, trace: {trace_info}')
            task.set_status(TaskStatus.FAIL)
            return
        # 2.2. 上传文件
        file_content = read_file(file_path)
        response = requests.put(url, data=file_content, headers=upload_file_headers)
        if not response or response.status_code != 200 or not response.ok:
            log.error(f'Exception for _create_store/put_file')
            task.set_status(TaskStatus.FAIL)
            return
        # 2.3. 添加文档
        add_file_request = bailian_20231229_models.AddFileRequest(
            lease_id=lease_id,
            parser='DASHSCOPE_DOCMIND',
            category_id=category_id
        )
        try:
            result = client.add_file_with_options(workspace_id, add_file_request, headers, runtime)
            if result.status_code != 200 or not result.body.success:
                raise RuntimeError(result.body)
        except Exception as e:
            trace_info = traceback.format_exc()
            log.error(f'Exception for _create_store/add_file, e: {e}, trace: {trace_info}')
            task.set_status(TaskStatus.FAIL)
            return
    # 3. 创建知识库索引


def create_store(request: CreateStoreEntity, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(_create_store, request, task_id=task_id)
    return task_id


if __name__ == '__main__':
    _create_store(CreateStoreEntity(name='test', chunking_size=0, overlap=0, seperator='', files=[File(
        name='server.txt',
        file_base64='MjAyNC0xMS0xMSAwOTo1MzoxMCw0OTkgLSBJTkZPIC0gdGVzdAoyMDI0LTExLTExIDE1OjE2OjMxLDAxMCAtIElORk8gLSB0ZXN0Cg==')]),
                  'aaa')
