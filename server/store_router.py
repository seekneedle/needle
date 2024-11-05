from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
import traceback
from utils import log
from services.create_store import create_store, CreateStoreEntity
from .auth import authenticate, check_permission
from .response import BaseResponse


store_router = APIRouter(prefix="/vector_store")


# 1. 创建知识库
@store_router.post('/create')
async def vector_store_create(request: CreateStoreEntity, tasks: BackgroundTasks, token: str = Depends(authenticate)):
    """
        创建向量知识库：支持pdf、docx、doc、txt、md文件上传，切分。
    """
    if not check_permission(token, "create"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid permission.")
    try:
        result = create_store(request, tasks)
        return BaseResponse(data=result)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.info(f"Exception for /vector_store/create, e: {e}, trace: {trace_info}")
        return BaseResponse(code=400, status='fail', data={'error': e})
