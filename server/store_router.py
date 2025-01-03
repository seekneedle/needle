from fastapi import APIRouter, Depends, BackgroundTasks, Request
import traceback

from server.auth import check_permission
from services.file_add import FileAddRequest, file_add
from services.query import QueryRequest, stream_query, query
from utils.log import log
from services.create_store import create_store, CreateStoreRequest
from services.create_store_status import task_status
from services.retrieve import retrieve, RetrieveRequest
from services.file_list import file_list
from services.files_delete import DeleteFilesRequest, delete_files
from server.response import SuccessResponse, FailResponse
from fastapi.responses import StreamingResponse

store_router = APIRouter(prefix='/vector_store', dependencies=[Depends(check_permission)])


# 1. 创建知识库
@store_router.post('/create')
async def vector_store_create(request: CreateStoreRequest, background_tasks: BackgroundTasks):
    """
        创建向量知识库：支持pdf、docx、doc、txt、md文件上传，切分。
    """
    try:
        create_store_response = create_store(request, background_tasks)
        return SuccessResponse(data=create_store_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/create, request: {request}, e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))


# 2. 查询任务状态
@store_router.get('/task_status/{task_id}')
async def vector_store_get_task_status(task_id: str):
    """
        查询任务状态：根据任务ID获取任务的当前状态。
    """
    try:
        create_store_status_response = task_status(task_id)

        return SuccessResponse(data=create_store_status_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/task_status, task_id:{task_id} , e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))


# 3. 查询知识库列表
@store_router.get('/list/{name}')
async def vector_store_get_store_list(name: str):
    """
        根据知识库名称查询所有知识库，如果不填名称，则查询所有知识库。
    """
    pass


# 4. 删除知识库
@store_router.post('/delete/{id}')
async def vector_store_delete_store(id: str):
    """
        根据id删除知识库
    """
    pass


# 5. 向知识库增加文件
@store_router.post('/file/add')
async def vector_store_file_add(request: FileAddRequest, background_tasks: BackgroundTasks):
    """
        向知识库里添加文件：支持pdf、docx、doc、txt、md文件上传，切分。
    """
    try:
        file_add_response = file_add(request, background_tasks)
        return SuccessResponse(data=file_add_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/file_add, e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))


# 6. 查询知识库文件列表
@store_router.get('/file/list/{id}')
async def vector_store_get_file_list(id: str):
    """
        根据id查询知识库文件列表
    """
    try:
        file_list_response = file_list(id)

        return SuccessResponse(data=file_list_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /file/list, index_id:{id} , e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))


# 7. 删除知识库文件
@store_router.post('/file/delete')
async def vector_store_delete_files(request: DeleteFilesRequest):
    """
        根据文件id列表删除知识库文件
    """
    """
            根据id查询知识库文件列表
        """
    try:
        files_delete_response = delete_files(request)

        return SuccessResponse(data=files_delete_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /file/delete, index_id:{request.id} , e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))


# 8. 知识召回
@store_router.post('/retrieve')
async def vector_store_retrieve(request: RetrieveRequest):
    """
        召回知识库片段：根据检索内容召回知识库相关片段。
    """
    try:
        retrieve_response = retrieve(request)

        return SuccessResponse(data=retrieve_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/retrieve, request: {request}, e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))


# 9.1 流式RAG
@store_router.post('/stream_query')
async def vector_store_stream_query(request: Request, query_request: QueryRequest):
    """
        流式知识库查询：使用流式方法查询知识库并调用大模型总结回答。
    """
    try:
        async def event_stream():
            async for event in stream_query(query_request):
                if await request.is_disconnected():
                    break
                yield event
        return StreamingResponse(event_stream(), media_type='text/event-stream')
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/stream_query, request: {request}, e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))


# 9.2 常规RAG
@store_router.post('/query')
async def vector_store_query(request: QueryRequest):
    """
        知识库查询：查询知识库并调用大模型总结回答。
    """
    try:
        query_response = query(request)

        return SuccessResponse(data=query_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/query, request: {request}, e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))
