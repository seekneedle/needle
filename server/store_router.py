from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
import traceback
from utils.log import log
from services.create_store import create_store, CreateStoreEntity
from server.auth import authenticate, check_permission
from server.response import SuccessResponse, FailResponse
from data.task import TaskEntry

store_router = APIRouter(prefix='/vector_store')


# 1. 创建知识库
@store_router.post('/create')
async def vector_store_create(request: CreateStoreEntity, background_tasks: BackgroundTasks, token: str = Depends(
    authenticate)):
    """
        创建向量知识库：支持pdf、docx、doc、txt、md文件上传，切分。
    """
    try:
        if not check_permission(token, 'store'):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid permission.')

        task_id = create_store(request, background_tasks)
        return SuccessResponse(data={
            'task_id': task_id
        })
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/create, e: {e}, trace: {trace_info}')
        return FailResponse(data={'error': e})

# 2. 查询任务状态
@store_router.get('/task_status/{task_id}')
async def get_task_status(task_id: str):#, token: str = Depends(authenticate)):
    """
        查询任务状态：根据任务ID获取任务的当前状态。
    """
    try:
        #if not check_permission(token, 'task'):
        #    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid permission.')
        
        task_entry = TaskEntry(task_id=task_id)
        task_entry.load()
        if not task_entry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Task not found.')

        return SuccessResponse(data={
            'task_id': task_entry.task_id,
            'status': task_entry.status
        })
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/task_status/{task_id}, e: {e}, trace: {trace_info}')
        return FailResponse(data={'error': e})
