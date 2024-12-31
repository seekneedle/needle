import time
import uuid
from pydantic import BaseModel
from fastapi import BackgroundTasks
from utils.config import config
from utils.security import decrypt
from utils.log import log
from utils.bailian import create_client
from alibabacloud_bailian20231229 import models as bailian_20231229_models
from alibabacloud_tea_util import models as util_models
from utils.bailian import get_category_from_index
import traceback
from data.task import CreateFileTaskEntity, TaskStatus
from data.store import DocumentEntity
from typing import List, Optional
from utils.files_utils import File, upload_file
from contextlib import contextmanager


class FileAddRequest(BaseModel):
    index_id: str
    files: Optional[List[File]] = None


class FileAddResponse(BaseModel):
    task_id: str

    
def file_add(request: FileAddRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(_file_add, request, task_id=task_id)
    return FileAddResponse(task_id=task_id)

@contextmanager
def task_manager(task_id):
    task = CreateFileTaskEntity.create(task_id=task_id, status=TaskStatus.RUNNING)
    try:
        yield task  # Yield the task object for use in the function
    except Exception as e:
        task.set(status=TaskStatus.FAILED)
        raise e  # Re-raise the exception after setting the status
    else:
        # Automatically set the status based on the execution results
        if task.status == TaskStatus.RUNNING:  # If still running, mark as failed
            task.set(status=TaskStatus.FAILED)

def _file_add(request: FileAddRequest, task_id: str):
    with task_manager(task_id) as task:
        workspace_id = decrypt(config['workspace_id'])
        index_id = request.index_id
        task.set(store_id=index_id)
        runtime = util_models.RuntimeOptions()
        headers = {}
        client = create_client()
        category_id = get_category_from_index(request.index_id)
        document_ids = []

        # 1. 上传文件
        if request.files:
            for file in request.files:
                isSuccess, file_id = upload_file(client, category_id, workspace_id, task_id, file)
                if isSuccess:  # 上传不成功则不做处理
                    document_ids.append(file_id)
                else:
                    log.error(f'File upload failed for task_id: {task_id}, file: {file}')
                    return  # Exit without setting status, handled by task_manager

        else:
            log.error(f'No files provided for task_id: {task_id}')
            return  # Exit without setting status, handled by task_manager

        # 2. 提交文档添加任务     
        submit_index_add_documents_job_request = bailian_20231229_models.SubmitIndexAddDocumentsJobRequest(
            index_id=index_id,
            source_type='DATA_CENTER_FILE',
            document_ids=document_ids
        )
        try:
            result = client.submit_index_add_documents_job_with_options(workspace_id, submit_index_add_documents_job_request, headers, runtime)
            if result.status_code != 200 or not result.body.success:
                log.error(f'Submission failed for task_id: {task_id}, result: {result.body}')
                return  # Exit without setting status, handled by task_manager
            job_id = result.body.data.id
        except Exception as e:
            trace_info = traceback.format_exc()
            log.error(f'Exception for _file_add/submit_index, task_id: {task_id}, e: {e}, trace info: {trace_info}')
            return  # Exit without setting status, handled by task_manager

        # 3. 轮询任务状态
        for i in range(10):
            get_index_job_status_request = bailian_20231229_models.GetIndexJobStatusRequest(
                job_id=job_id,
                index_id=index_id
            )
            try:
                result = client.get_index_job_status_with_options(workspace_id, get_index_job_status_request, headers, runtime)
                if result.status_code != 200 or not result.body.success:
                    log.error(f'Job status check failed for task_id: {task_id}, result: {result.body}')
                    return  # Exit without setting status, handled by task_manager
                status = result.body.data.status
            except Exception as e:
                trace_info = traceback.format_exc()
                log.error(f'Exception for _file_add/submit_index, task_id: {task_id}, e: {e}, trace info: {trace_info}')
                return  # Exit without setting status, handled by task_manager

            if status == TaskStatus.FAILED:
                log.error(f'Exception for _file_add/submit_index, task_id: {task_id}, docs: {result.body.data.documents}')
                return  # Exit without setting status, handled by task_manager
            if status == TaskStatus.COMPLETED:
                task.set(status=TaskStatus.COMPLETED)
            time.sleep(6)