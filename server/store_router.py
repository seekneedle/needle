from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
import traceback
from utils.log import log
from services.create_store import create_store, CreateStoreEntity
from .auth import authenticate, check_permission
from .response import SuccessResponse, FailResponse

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
