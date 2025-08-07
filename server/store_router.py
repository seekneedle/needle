from fastapi import APIRouter, Depends, BackgroundTasks, Request, Query, File, Form, UploadFile
import traceback
from typing import Optional, List
from server.auth import check_permission
from services.file_add import FileAddRequest, file_add
from services.query import QueryRequest, stream_query, query
from utils.log import log
from utils.files_utils import FileContent
from services.create_store import create_store, CreateStoreRequest
from services.create_store_status import task_status
from services.retrieve import retrieve, RetrieveRequest
from services.file_list import file_list, file_list_abnormal, FileListBatchRequest, file_list_batch
from services.files_delete import DeleteFilesRequest, delete_files
from services.store_list import get_store_list
from services.file_get import get_file
from services.stores_delete import delete_store, DeleteStoreRequest
from server.response import SuccessResponse, FailResponse
from fastapi.responses import StreamingResponse
from urllib.parse import unquote

store_router = APIRouter(prefix='/vector_store', dependencies=[Depends(check_permission)])


# 1. 创建知识库
@store_router.post('/create')
async def vector_store_create(name: str = Form(...),
                              chunk_size: Optional[int] = Form(None),
                              overlap_size: Optional[int] = Form(None),
                              separator: Optional[str] = Form(None),
                              files: List[UploadFile] = File(...),
                              background_tasks: BackgroundTasks=None):
    """
        创建向量知识库：支持pdf、docx、doc、txt、md文件上传，切分。
    """
    file_list = []
    for file in files:
        content = await file.read()
        file_content = FileContent(name=file.filename, file_content=content)
        file_list.append(file_content)
    request = CreateStoreRequest(
        name=name,
        chunk_size=chunk_size,
        overlap_size=overlap_size,
        separator=separator,
        files=file_list
    )
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
@store_router.get('/list')
async def vector_store_get_store_list(name: Optional[str] = Query(None)):
    """
        根据知识库名称查询所有知识库，如果不填名称，则查询所有知识库。
    """
    try:
        store_list_response = get_store_list(name)
        return SuccessResponse(data=store_list_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/list, name:{name}, e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))


# 4. 删除知识库
@store_router.post('/delete')
async def vector_store_delete_store(request: DeleteStoreRequest):
    """
        根据id删除知识库
    """
    try:
        store_delete_response = delete_store(request.ids)

        return SuccessResponse(data=store_delete_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /delete, index_id:{request.id}, e:{e}, trace:{trace_info}')
        return FailResponse(error=str(e))


# 5. 向知识库增加文件
@store_router.post('/file/add')
async def vector_store_file_add(request: Request,
                                id: str = Form(...),
                                files: List[UploadFile] = File(...),
                                background_tasks: BackgroundTasks=None):
    """
        向知识库里添加文件：支持pdf、docx、doc、txt、md文件上传，切分。
    """
    client_ip = request.headers.get('x-forwarded-for')
    if not client_ip:
        client_ip = request.client.host if request.client else "unknown"
    
    # 记录请求基本信息
    log.info(
        f"File add request from IP: {client_ip}, "
        f"store_id: {id}, "
        f"file_count: {len(files)}, "
        f"filenames: {[file.filename for file in files]}"
    )
    
    file_list = []
    for file in files:
        content = await file.read()
        decoded_filename = unquote(file.filename, encoding='utf-8')
        file_content = FileContent(name=decoded_filename, file_content=content)
        file_list.append(file_content)
    request = FileAddRequest(
        id=id,
        files=file_list
    )
    try:
        file_add_response = file_add(request, background_tasks)
        return SuccessResponse(data=file_add_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/file_add, e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))


# 6. 查询知识库文件列表
@store_router.get('/file/list/{id}')
async def vector_store_get_file_list(id: str, file_name: Optional[str] = Query(None)):
    """
        根据id查询知识库文件列表
    """
    try:
        file_list_response = file_list(id, file_name)

        return SuccessResponse(data=file_list_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /file/list, index_id:{id} , e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))


# 7. 删除知识库文件
@store_router.post('/file/delete')
async def vector_store_delete_files(fastapi_request: Request,
    request: DeleteFilesRequest):
    """
        根据文件id列表删除知识库文件
    """
    try:
        client_ip = fastapi_request.headers.get('x-forwarded-for')
        if not client_ip:
            client_ip = fastapi_request.client.host if fastapi_request.client else "unknown"
        
        # 记录请求日志
        log.info(
            f"Delete files request from IP: {client_ip}, "
            f"store_id: {request.id}, "
            f"file_ids: {request.file_ids}"
        )
        
        files_delete_response = delete_files(request)

        return SuccessResponse(data=files_delete_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /file/delete, index_id:{request.id} , e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))


# 8 根据file id查询文件内容
@store_router.get('/file/get/{file_id}')
async def vector_store_file_get(file_id):
    """
            根据file id查询知识库文件内容
        """
    try:
        file_content_response = get_file(file_id)

        return SuccessResponse(data=file_content_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /file/get, file_id:{file_id} , e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))


# 9. 知识召回
@store_router.post('/retrieve')
async def vector_store_retrieve(request: RetrieveRequest):
    """
        召回知识库片段：根据检索内容召回知识库相关片段。
    """
    try:
        retrieve_response = await retrieve(request)

        return SuccessResponse(data=retrieve_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/retrieve, request: {request}, e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))


# 10.1 流式RAG
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


# 10.2 常规RAG
@store_router.post('/query')
async def vector_store_query(request: QueryRequest):
    """
        知识库查询：查询知识库并调用大模型总结回答。
    """
    try:
        query_response = await query(request)

        return SuccessResponse(data=query_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/query, request: {request}, e: {e}, trace: {trace_info}')
        return FailResponse(error=str(e))


# 6. 列出参数 id 对应的知识库里状态异常的 docs
@store_router.get('/file/list_abnormal/{id}')
async def vector_store_get_file_list_abnormal(id: str, file_name: Optional[str] = Query(None)):
    """
        根据 id 查询知识库里状态异常的文件列表
    """
    try:
        abnormal_response = file_list_abnormal(id, file_name)

        return SuccessResponse(data=abnormal_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /file/list_abnormal, index_id:{id} , e:{e}, trace:{trace_info}')
        return FailResponse(error=str(e))

# 6. 列出知识库里多个 document 对应的 file_id 以及其他若干参数
# 参数：index_id: 知识库 id
# 参数：file_names: 多个 document name 的列表
@store_router.post('/file/list_batch')
async def vector_store_file_list_batch(request: FileListBatchRequest):
    """
        列出知识库里多个 document 对应的 file_id 以及其他若干参数
    """
    index_id = request.index_id
    file_names = request.file_names
    try:
        response = file_list_batch(index_id, file_names)
        return SuccessResponse(data=response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /file/list_batch, index_id:{index_id}, file_names:{file_names}, e:{e}, trace:{trace_info}')
        return FailResponse(error=str(e))
