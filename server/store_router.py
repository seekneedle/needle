import uuid
from fastapi import APIRouter, Depends, BackgroundTasks, Request, Query, File, Form, UploadFile
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
import time

store_router = APIRouter(prefix='/vector_store', dependencies=[Depends(check_permission)])


def generate_trace_id():
    return str(uuid.uuid4().hex)[:8]  # Using first 8 characters of UUID hex for simplicity


# 1. 创建知识库
@store_router.post('/create')
async def vector_store_create(name: str = Form(...),
                              chunk_size: Optional[int] = Form(None),
                              overlap_size: Optional[int] = Form(None),
                              separator: Optional[str] = Form(None),
                              files: List[UploadFile] = File(...),
                              background_tasks: BackgroundTasks = None):
    """
        创建向量知识库：支持pdf、docx、doc、txt、md文件上传，切分。
    """
    trace_id = generate_trace_id()
    start_time = time.time()
    log.info(
        f"[TraceID:{trace_id}] API /vector_store/create started. Input params: name={name}, chunk_size={chunk_size}, "
        f"overlap_size={overlap_size}, separator={separator}, files_count={len(files)}")

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
        log.info(
            f"[TraceID:{trace_id}] API /vector_store/create completed. Execution time: {time.time() - start_time:.2f}s. "
            f"Response: {create_store_response}")
        return SuccessResponse(data=create_store_response)
    except Exception as e:
        log.error(
            f'[TraceID:{trace_id}] Exception for /vector_store/create, request: {request}, e: {e}')
        return FailResponse(error=str(e))


# 2. 查询任务状态
@store_router.get('/task_status/{task_id}')
async def vector_store_get_task_status(task_id: str):
    """
        查询任务状态：根据任务ID获取任务的当前状态。
    """
    trace_id = generate_trace_id()
    start_time = time.time()
    log.info(f"[TraceID:{trace_id}] API /vector_store/task_status started. Input params: task_id={task_id}")

    try:
        create_store_status_response = task_status(task_id)
        log.info(
            f"[TraceID:{trace_id}] API /vector_store/task_status completed. Execution time: {time.time() - start_time:.2f}s. "
            f"Response: {create_store_status_response}")
        return SuccessResponse(data=create_store_status_response)
    except Exception as e:
        log.error(
            f'[TraceID:{trace_id}] Exception for /vector_store/task_status, task_id:{task_id} , e: {e}')
        return FailResponse(error=str(e))


# 3. 查询知识库列表
@store_router.get('/list')
async def vector_store_get_store_list(name: Optional[str] = Query(None)):
    """
        根据知识库名称查询所有知识库，如果不填名称，则查询所有知识库。
    """
    trace_id = generate_trace_id()
    start_time = time.time()
    log.info(f"[TraceID:{trace_id}] API /vector_store/list started. Input params: name={name}")

    try:
        store_list_response = get_store_list(name)
        log.info(
            f"[TraceID:{trace_id}] API /vector_store/list completed. Execution time: {time.time() - start_time:.2f}s. "
            f"Response: {store_list_response}")
        return SuccessResponse(data=store_list_response)
    except Exception as e:
        log.error(f'[TraceID:{trace_id}] Exception for /vector_store/list, name:{name}, e: {e}')
        return FailResponse(error=str(e))


# 4. 删除知识库
@store_router.post('/delete')
async def vector_store_delete_store(request: DeleteStoreRequest):
    """
        根据id删除知识库
    """
    trace_id = generate_trace_id()
    start_time = time.time()
    log.info(f"[TraceID:{trace_id}] API /vector_store/delete started. Input params: {request}")

    try:
        store_delete_response = delete_store(request.ids)
        log.info(
            f"[TraceID:{trace_id}] API /vector_store/delete completed. Execution time: {time.time() - start_time:.2f}s. "
            f"Response: {store_delete_response}")
        return SuccessResponse(data=store_delete_response)
    except Exception as e:
        log.error(f'[TraceID:{trace_id}] Exception for /delete, index_id:{request.id}, e:{e}')
        return FailResponse(error=str(e))


# 5. 向知识库增加文件
@store_router.post('/file/add')
async def vector_store_file_add(request: Request,
                                id: str = Form(...),
                                files: List[UploadFile] = File(...),
                                background_tasks: BackgroundTasks = None):
    """
        向知识库里添加文件：支持pdf、docx、doc、txt、md文件上传，切分。
    """
    trace_id = generate_trace_id()
    start_time = time.time()
    client_ip = request.headers.get('x-forwarded-for')
    if not client_ip:
        client_ip = request.client.host if request.client else "unknown"

    log.info(
        f"[TraceID:{trace_id}] API /vector_store/file/add started. Input params: id={id}, files_count={len(files)}, "
        f"client_ip={client_ip}")

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
        log.info(
            f"[TraceID:{trace_id}] API /vector_store/file/add completed. Execution time: {time.time() - start_time:.2f}s. "
            f"Response: {file_add_response}")
        return SuccessResponse(data=file_add_response)
    except Exception as e:
        log.error(f'[TraceID:{trace_id}] Exception for /vector_store/file_add, e: {e}')
        return FailResponse(error=str(e))


# 6. 查询知识库文件列表
@store_router.get('/file/list/{id}')
async def vector_store_get_file_list(id: str, file_name: Optional[str] = Query(None)):
    """
        根据id查询知识库文件列表
    """
    trace_id = generate_trace_id()
    start_time = time.time()
    log.info(f"[TraceID:{trace_id}] API /vector_store/file/list started. Input params: id={id}, file_name={file_name}")

    try:
        file_list_response = file_list(id, file_name)
        log.info(
            f"[TraceID:{trace_id}] API /vector_store/file/list completed. Execution time: {time.time() - start_time:.2f}s. "
            f"Response count: {file_list_response}")
        return SuccessResponse(data=file_list_response)
    except Exception as e:
        log.error(f'[TraceID:{trace_id}] Exception for /file/list, index_id:{id} , e: {e}')
        return FailResponse(error=str(e))


# 7. 删除知识库文件
@store_router.post('/file/delete')
async def vector_store_delete_files(fastapi_request: Request,
                                    request: DeleteFilesRequest):
    """
        根据文件id列表删除知识库文件
    """
    trace_id = generate_trace_id()
    start_time = time.time()
    client_ip = fastapi_request.headers.get('x-forwarded-for')
    if not client_ip:
        client_ip = fastapi_request.client.host if fastapi_request.client else "unknown"

    log.info(
        f"[TraceID:{trace_id}] API /vector_store/file/delete started. Input params: {request}, client_ip={client_ip}")

    try:
        files_delete_response = delete_files(request)
        log.info(
            f"[TraceID:{trace_id}] API /vector_store/file/delete completed. Execution time: {time.time() - start_time:.2f}s. "
            f"Response: {files_delete_response}")
        return SuccessResponse(data=files_delete_response)
    except Exception as e:
        log.error(
            f'[TraceID:{trace_id}] Exception for /file/delete, index_id:{request.id} , e: {e}')
        return FailResponse(error=str(e))


# 8 根据file id查询文件内容
@store_router.get('/file/get/{file_id}')
async def vector_store_file_get(file_id):
    """
            根据file id查询知识库文件内容
        """
    trace_id = generate_trace_id()
    start_time = time.time()
    log.info(f"[TraceID:{trace_id}] API /vector_store/file/get started. Input params: file_id={file_id}")

    try:
        file_content_response = get_file(file_id)
        log.info(
            f"[TraceID:{trace_id}] API /vector_store/file/get completed. Execution time: {time.time() - start_time:.2f}s. "
            f"Response: {file_content_response}")
        return SuccessResponse(data=file_content_response)
    except Exception as e:
        log.error(f'[TraceID:{trace_id}] Exception for /file/get, file_id:{file_id} , e: {e}')
        return FailResponse(error=str(e))


# 9. 知识召回
@store_router.post('/retrieve')
async def vector_store_retrieve(request: RetrieveRequest):
    """
        召回知识库片段：根据检索内容召回知识库相关片段。
    """
    trace_id = generate_trace_id()
    start_time = time.time()
    log.info(f"[TraceID:{trace_id}] API /vector_store/retrieve started. Input params: {request}")

    try:
        retrieve_response = await retrieve(request)
        log.info(
            f"[TraceID:{trace_id}] API /vector_store/retrieve completed. Execution time: {time.time() - start_time:.2f}s. "
            f"Response count: {retrieve_response}")
        return SuccessResponse(data=retrieve_response)
    except Exception as e:
        log.error(
            f'[TraceID:{trace_id}] Exception for /vector_store/retrieve, request: {request}, e: {e}')
        return FailResponse(error=str(e))


# 10.1 流式RAG
@store_router.post('/stream_query')
async def vector_store_stream_query(request: Request, query_request: QueryRequest):
    """
        流式知识库查询：使用流式方法查询知识库并调用大模型总结回答。
    """
    trace_id = generate_trace_id()
    start_time = time.time()
    log.info(f"[TraceID:{trace_id}] API /vector_store/stream_query started. Input params: {query_request}")

    try:
        async def event_stream():
            async for event in stream_query(query_request):
                if await request.is_disconnected():
                    break
                yield event

        log.info(
            f"[TraceID:{trace_id}] API /vector_store/stream_query streaming started. Execution time: {time.time() - start_time:.2f}s")
        return StreamingResponse(event_stream(), media_type='text/event-stream')
    except Exception as e:
        log.error(
            f'[TraceID:{trace_id}] Exception for /vector_store/stream_query, request: {request}, e: {e}')
        return FailResponse(error=str(e))


# 10.2 常规RAG
@store_router.post('/query')
async def vector_store_query(request: QueryRequest):
    """
        知识库查询：查询知识库并调用大模型总结回答。
    """
    trace_id = generate_trace_id()
    start_time = time.time()
    log.info(f"[TraceID:{trace_id}] API /vector_store/query started. Input params: {request}")

    try:
        query_response = await query(request)
        log.info(
            f"[TraceID:{trace_id}] API /vector_store/query completed. Execution time: {time.time() - start_time:.2f}s. "
            f"Response: {query_response}")
        return SuccessResponse(data=query_response)
    except Exception as e:
        log.error(
            f'[TraceID:{trace_id}] Exception for /vector_store/query, request: {request}, e: {e}')
        return FailResponse(error=str(e))


# 6. 列出参数 id 对应的知识库里状态异常的 docs
@store_router.get('/file/list_abnormal/{id}')
async def vector_store_get_file_list_abnormal(id: str, file_name: Optional[str] = Query(None)):
    """
        根据 id 查询知识库里状态异常的文件列表
    """
    trace_id = generate_trace_id()
    start_time = time.time()
    log.info(
        f"[TraceID:{trace_id}] API /vector_store/file/list_abnormal started. Input params: id={id}, file_name={file_name}")

    try:
        abnormal_response = file_list_abnormal(id, file_name)
        log.info(
            f"[TraceID:{trace_id}] API /vector_store/file/list_abnormal completed. Execution time: {time.time() - start_time:.2f}s. "
            f"Response: {abnormal_response}")
        return SuccessResponse(data=abnormal_response)
    except Exception as e:
        log.error(f'[TraceID:{trace_id}] Exception for /file/list_abnormal, index_id:{id} , e:{e}')
        return FailResponse(error=str(e))


# 6. 列出知识库里多个 document 对应的 file_id 以及其他若干参数
@store_router.post('/file/list_batch')
async def vector_store_file_list_batch(request: FileListBatchRequest):
    """
        列出知识库里多个 document 对应的 file_id 以及其他若干参数
    """
    trace_id = generate_trace_id()
    start_time = time.time()
    index_id = request.index_id
    file_names = request.file_names
    log.info(f"[TraceID:{trace_id}] API /vector_store/file/list_batch started. Input params: index_id={index_id}, "
             f"file_names_count={len(file_names)}")

    try:
        response = file_list_batch(index_id, file_names)
        log.info(
            f"[TraceID:{trace_id}] API /vector_store/file/list_batch completed. Execution time: {time.time() - start_time:.2f}s. "
            f"Response: {response}")
        return SuccessResponse(data=response)
    except Exception as e:
        log.error(
            f'[TraceID:{trace_id}] Exception for /file/list_batch, index_id:{index_id}, file_names:{file_names}, e:{e}')
        return FailResponse(error=str(e))