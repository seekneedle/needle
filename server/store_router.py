from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
import traceback

from services.file_add import FileAddRequest
from services.query import QueryRequest, stream_query, query
from utils.log import log
from utils.config import config
from services.create_store import create_store, CreateStoreRequest
from services.create_store_status import create_store_status
from services.retrieve import retrieve, RetrieveRequest
from server.auth import get_token, check_permission
from server.response import SuccessResponse, FailResponse
from fastapi.responses import StreamingResponse

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
        log.error(f'Exception for /vector_store/create, request: {request}, e: {e}, trace: {trace_info}')
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
        log.error(f'Exception for /vector_store/task_status, task_id:{task_id} , e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))

# 3. 向知识库增加文件
@store_router.post('/file/add')
async def file_add(request: FileAddRequest, background_tasks: BackgroundTasks, token: str = Depends(
    get_token)):
    """
        向知识库里添加文件：支持pdf、docx、doc、txt、md文件上传，切分。
    """
    try:
        if not check_permission(token, PERMISSION_MANAGE):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid permission.')

        file_add_response = file_add(request, background_tasks)
        return SuccessResponse(data=file_add_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/file_add, e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))


# 4. 知识召回
@store_router.post('/retrieve')
async def vector_store_retrieve(request: RetrieveRequest, token: str = Depends(
    get_token)):
    """
        召回知识库片段：根据检索内容召回知识库相关片段。
    """
    try:
        if not check_permission(token, request.id):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid permission.')

        retrieve_response = retrieve(request)

        return SuccessResponse(data=retrieve_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/retrieve, request: {request}, e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))


# 5. 流式RAG
@store_router.post('/stream_query')
async def vector_store_stream_query(request: QueryRequest, token: str = Depends(
    get_token)):
    """
        流式知识库查询：使用流式方法查询知识库并调用大模型总结回答。
    """
    try:
        if not check_permission(token, request.id):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid permission.')

        return StreamingResponse(stream_query(request), media_type='application/json')
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/stream_query, request: {request}, e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))


# 6. 常规RAG
@store_router.post('/query')
async def vector_store_query(request: QueryRequest, token: str = Depends(
    get_token)):
    """
        知识库查询：查询知识库并调用大模型总结回答。
    """
    try:
        if not check_permission(token, request.id):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid permission.')

        query_response = query(request)

        return SuccessResponse(data=query_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/query, request: {request}, e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))