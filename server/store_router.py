from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
import traceback
from utils.log import log
from utils.config import config
from services.create_store import create_store, CreateStoreRequest
from services.create_store_status import create_store_status
from server.auth import get_token, check_permission
from server.response import SuccessResponse, FailResponse

store_router = APIRouter(prefix='/vector_store')

PERMISSION_MANAGE = config['permission_manage']


# 1. 创建知识库
@store_router.post('/create')
async def vector_store_create(request: CreateStoreRequest, background_tasks: BackgroundTasks, token: str = Depends(
    get_token)):
    """
        创建向量知识库：支持pdf、docx、doc、txt、md文件上传，切分。
    """
    try:
        if not check_permission(token, PERMISSION_MANAGE):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid permission.')

        create_store_response = create_store(request, background_tasks)
        return SuccessResponse(data=create_store_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/create, e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))


# 2. 查询任务状态
@store_router.get('/task_status/{task_id}')
async def get_task_status(task_id: str, token: str = Depends(
    get_token)):
    """
        查询任务状态：根据任务ID获取任务的当前状态。
    """
    try:
        if not check_permission(token, PERMISSION_MANAGE):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid permission.')

        create_store_status_response = create_store_status(task_id)

        return SuccessResponse(data=create_store_status_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/task_status, e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))
