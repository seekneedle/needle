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
import time

store_router = APIRouter(prefix='/vector_store', dependencies=[Depends(check_permission)])


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
    start_time = time.time()
    request_id = f"create_{int(start_time * 1000)}"
    log.info(f"API /vector_store/create started - request_id: {request_id}, name: {name}, "
             f"chunk_size: {chunk_size}, overlap_size: {overlap_size}, separator: {separator}, "
             f"file_count: {len(files)}")

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
        log.info(f"API /vector_store/create completed - request_id: {request_id}, "
                 f"response: {create_store_response}, execution_time: {time.time() - start_time:.2f}s")
        return SuccessResponse(data=create_store_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(
            f'Exception for /vector_store/create, request_id: {request_id}, request: {request}, e: {e}, trace: {trace_info}')
        log.info(f"API /vector_store/create failed - request_id: {request_id}, "
                 f"error: {str(e)}, execution_time: {time.time() - start_time:.2f}s")
        return FailResponse(error=str(e))


# 2. 查询任务状态
@store_router.get('/task_status/{task_id}')
async def vector_store_get_task_status(task_id: str):
    """
        查询任务状态：根据任务ID获取任务的当前状态。
    """
    start_time = time.time()
    request_id = f"task_status_{task_id}_{int(start_time * 1000)}"
    log.info(f"API /vector_store/task_status started - request_id: {request_id}, task_id: {task_id}")

    try:
        create_store_status_response = task_status(task_id)
        log.info(f"API /vector_store/task_status completed - request_id: {request_id}, "
                 f"response: {create_store_status_response}, execution_time: {time.time() - start_time:.2f}s")
        return SuccessResponse(data=create_store_status_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(
            f'Exception for /vector_store/task_status, request_id: {request_id}, task_id:{task_id} , e: {e}, trace: {trace_info}')
        log.info(f"API /vector_store/task_status failed - request_id: {request_id}, "
                 f"error: {str(e)}, execution_time: {time.time() - start_time:.2f}s")
        return FailResponse(error=str(e))


# 3. 查询知识库列表
@store_router.get('/list')
async def vector_store_get_store_list(name: Optional[str] = Query(None)):
    """
        根据知识库名称查询所有知识库，如果不填名称，则查询所有知识库。
    """
    start_time = time.time()
    request_id = f"store_list_{int(start_time * 1000)}"
    log.info(f"API /vector_store/list started - request_id: {request_id}, name: {name}")

    try:
        store_list_response = get_store_list(name)
        log.info(f"API /vector_store/list completed - request_id: {request_id}, "
                 f"response_count: {len(store_list_response)}, execution_time: {time.time() - start_time:.2f}s")
        return SuccessResponse(data=store_list_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(
            f'Exception for /vector_store/list, request_id: {request_id}, name:{name}, e: {e}, trace: {trace_info}')
        log.info(f"API /vector_store/list failed - request_id: {request_id}, "
                 f"error: {str(e)}, execution_time: {time.time() - start_time:.2f}s")
        return FailResponse(error=str(e))


# 4. 删除知识库
@store_router.post('/delete')
async def vector_store_delete_store(request: DeleteStoreRequest):
    """
        根据id删除知识库
    """
    start_time = time.time()
    request_id = f"delete_store_{'_'.join(request.ids)}_{int(start_time * 1000)}"
    log.info(f"API /vector_store/delete started - request_id: {request_id}, ids: {request.ids}")

    try:
        store_delete_response = delete_store(request.ids)
        log.info(f"API /vector_store/delete completed - request_id: {request_id}, "
                 f"response: {store_delete_response}, execution_time: {time.time() - start_time:.2f}s")
        return SuccessResponse(data=store_delete_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /delete, request_id: {request_id}, index_id:{request.id}, e:{e}, trace:{trace_info}')
        log.info(f"API /vector_store/delete failed - request_id: {request_id}, "
                 f"error: {str(e)}, execution_time: {time.time() - start_time:.2f}s")
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
    start_time = time.time()
    request_id = f"file_add_{id}_{int(start_time * 1000)}"
    client_ip = request.headers.get('x-forwarded-for')
    if not client_ip:
        client_ip = request.client.host if request.client else "unknown"

    filenames = [file.filename for file in files]
    log.info(f"API /vector_store/file/add started - request_id: {request_id}, "
             f"store_id: {id}, file_count: {len(files)}, filenames: {filenames}, "
             f"client_ip: {client_ip}")

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
        log.info(f"API /vector_store/file/add completed - request_id: {request_id}, "
                 f"response: {file_add_response}, execution_time: {time.time() - start_time:.2f}s")
        return SuccessResponse(data=file_add_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /vector_store/file_add, request_id: {request_id}, e: {e}, trace: {trace_info}')
        log.info(f"API /vector_store/file/add failed - request_id: {request_id}, "
                 f"error: {str(e)}, execution_time: {time.time() - start_time:.2f}s")
        return FailResponse(error=str(e))


# 6. 查询知识库文件列表
@store_router.get('/file/list/{id}')
async def vector_store_get_file_list(id: str, file_name: Optional[str] = Query(None)):
    """
        根据id查询知识库文件列表
    """
    start_time = time.time()
    request_id = f"file_list_{id}_{int(start_time * 1000)}"
    log.info(f"API /vector_store/file/list started - request_id: {request_id}, "
             f"store_id: {id}, file_name: {file_name}")

    try:
        file_list_response = file_list(id, file_name)
        log.info(f"API /vector_store/file/list completed - request_id: {request_id}, "
                 f"response_count: {len(file_list_response)}, execution_time: {time.time() - start_time:.2f}s")
        return SuccessResponse(data=file_list_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /file/list, request_id: {request_id}, index_id:{id} , e: {e}, trace: {trace_info}')
        log.info(f"API /vector_store/file/list failed - request_id: {request_id}, "
                 f"error: {str(e)}, execution_time: {time.time() - start_time:.2f}s")
        return FailResponse(error=str(e))


# 7. 删除知识库文件
@store_router.post('/file/delete')
async def vector_store_delete_files(fastapi_request: Request,
                                    request: DeleteFilesRequest):
    """
        根据文件id列表删除知识库文件
    """
    start_time = time.time()
    request_id = f"file_delete_{request.id}_{int(start_time * 1000)}"
    client_ip = fastapi_request.headers.get('x-forwarded-for')
    if not client_ip:
        client_ip = fastapi_request.client.host if fastapi_request.client else "unknown"

    log.info(f"API /vector_store/file/delete started - request_id: {request_id}, "
             f"store_id: {request.id}, file_ids: {request.file_ids}, client_ip: {client_ip}")

    try:
        files_delete_response = delete_files(request)
        log.info(f"API /vector_store/file/delete completed - request_id: {request_id}, "
                 f"response: {files_delete_response}, execution_time: {time.time() - start_time:.2f}s")
        return SuccessResponse(data=files_delete_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(
            f'Exception for /file/delete, request_id: {request_id}, index_id:{request.id} , e: {e}, trace: {trace_info}')
        log.info(f"API /vector_store/file/delete failed - request_id: {request_id}, "
                 f"error: {str(e)}, execution_time: {time.time() - start_time:.2f}s")
        return FailResponse(error=str(e))


# 8 根据file id查询文件内容
@store_router.get('/file/get/{file_id}')
async def vector_store_file_get(file_id):
    """
            根据file id查询知识库文件内容
        """
    start_time = time.time()
    request_id = f"file_get_{file_id}_{int(start_time * 1000)}"
    log.info(f"API /vector_store/file/get started - request_id: {request_id}, file_id: {file_id}")

    try:
        file_content_response = get_file(file_id)
        log.info(f"API /vector_store/file/get completed - request_id: {request_id}, "
                 f"response_size: {len(file_content_response) if file_content_response else 0}, "
                 f"execution_time: {time.time() - start_time:.2f}s")
        return SuccessResponse(data=file_content_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for /file/get, request_id: {request_id}, file_id:{file_id} , e: {e}, trace: {trace_info}')
        log.info(f"API /vector_store/file/get failed - request_id: {request_id}, "
                 f"error: {str(e)}, execution_time: {time.time() - start_time:.2f}s")
        return FailResponse(error=str(e))


# 9. 知识召回
@store_router.post('/retrieve')
async def vector_store_retrieve(request: RetrieveRequest):
    """
        召回知识库片段：根据检索内容召回知识库相关片段。
    """
    start_time = time.time()
    request_id = f"retrieve_{request.store_id}_{int(start_time * 1000)}"
    log.info(f"API /vector_store/retrieve started - request_id: {request_id}, "
             f"store_id: {request.store_id}, query: {request.query}, "
             f"top_k: {request.top_k}, score_threshold: {request.score_threshold}")

    try:
        retrieve_response = await retrieve(request)
        log.info(f"API /vector_store/retrieve completed - request_id: {request_id}, "
                 f"response_count: {len(retrieve_response)}, execution_time: {time.time() - start_time:.2f}s")
        return SuccessResponse(data=retrieve_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(
            f'Exception for /vector_store/retrieve, request_id: {request_id}, request: {request}, e: {e}, trace: {trace_info}')
        log.info(f"API /vector_store/retrieve failed - request_id: {request_id}, "
                 f"error: {str(e)}, execution_time: {time.time() - start_time:.2f}s")
        return FailResponse(error=str(e))


# 10.1 流式RAG
@store_router.post('/stream_query')
async def vector_store_stream_query(request: Request, query_request: QueryRequest):
    """
        流式知识库查询：使用流式方法查询知识库并调用大模型总结回答。
    """
    start_time = time.time()
    request_id = f"stream_query_{query_request.store_id}_{int(start_time * 1000)}"
    log.info(f"API /vector_store/stream_query started - request_id: {request_id}, "
             f"store_id: {query_request.store_id}, query: {query_request.query}, "
             f"stream: {query_request.stream}, history: {len(query_request.history) if query_request.history else 0}")

    try:
        async def event_stream():
            async for event in stream_query(query_request):
                if await request.is_disconnected():
                    break
                yield event

        log.info(f"API /vector_store/stream_query streaming started - request_id: {request_id}")
        return StreamingResponse(event_stream(), media_type='text/event-stream')
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(
            f'Exception for /vector_store/stream_query, request_id: {request_id}, request: {request}, e: {e}, trace: {trace_info}')
        log.info(f"API /vector_store/stream_query failed - request_id: {request_id}, "
                 f"error: {str(e)}, execution_time: {time.time() - start_time:.2f}s")
        return FailResponse(error=str(e))


# 10.2 常规RAG
@store_router.post('/query')
async def vector_store_query(request: QueryRequest):
    """
        知识库查询：查询知识库并调用大模型总结回答。
    """
    start_time = time.time()
    request_id = f"query_{request.store_id}_{int(start_time * 1000)}"
    log.info(f"API /vector_store/query started - request_id: {request_id}, "
             f"store_id: {request.store_id}, query: {request.query}, "
             f"stream: {request.stream}, history: {len(request.history) if request.history else 0}")

    try:
        query_response = await query(request)
        log.info(f"API /vector_store/query completed - request_id: {request_id}, "
                 f"response_length: {len(query_response) if query_response else 0}, "
                 f"execution_time: {time.time() - start_time:.2f}s")
        return SuccessResponse(data=query_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(
            f'Exception for /vector_store/query, request_id: {request_id}, request: {request}, e: {e}, trace: {trace_info}')
        log.info(f"API /vector_store/query failed - request_id: {request_id}, "
                 f"error: {str(e)}, execution_time: {time.time() - start_time:.2f}s")
        return FailResponse(error=str(e))


# 6. 列出参数 id 对应的知识库里状态异常的 docs
@store_router.get('/file/list_abnormal/{id}')
async def vector_store_get_file_list_abnormal(id: str, file_name: Optional[str] = Query(None)):
    """
        根据 id 查询知识库里状态异常的文件列表
    """
    start_time = time.time()
    request_id = f"list_abnormal_{id}_{int(start_time * 1000)}"
    log.info(f"API /vector_store/file/list_abnormal started - request_id: {request_id}, "
             f"store_id: {id}, file_name: {file_name}")

    try:
        abnormal_response = file_list_abnormal(id, file_name)
        log.info(f"API /vector_store/file/list_abnormal completed - request_id: {request_id}, "
                 f"response_count: {len(abnormal_response)}, execution_time: {time.time() - start_time:.2f}s")
        return SuccessResponse(data=abnormal_response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(
            f'Exception for /file/list_abnormal, request_id: {request_id}, index_id:{id} , e:{e}, trace:{trace_info}')
        log.info(f"API /vector_store/file/list_abnormal failed - request_id: {request_id}, "
                 f"error: {str(e)}, execution_time: {time.time() - start_time:.2f}s")
        return FailResponse(error=str(e))


# 6. 列出知识库里多个 document 对应的 file_id 以及其他若干参数
@store_router.post('/file/list_batch')
async def vector_store_file_list_batch(request: FileListBatchRequest):
    """
        列出知识库里多个 document 对应的 file_id 以及其他若干参数
    """
    start_time = time.time()
    request_id = f"list_batch_{request.index_id}_{int(start_time * 1000)}"
    log.info(f"API /vector_store/file/list_batch started - request_id: {request_id}, "
             f"index_id: {request.index_id}, file_names: {request.file_names}")

    try:
        response = file_list_batch(request.index_id, request.file_names)
        log.info(f"API /vector_store/file/list_batch completed - request_id: {request_id}, "
                 f"response_count: {len(response)}, execution_time: {time.time() - start_time:.2f}s")
        return SuccessResponse(data=response)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(
            f'Exception for /file/list_batch, request_id: {request_id}, index_id:{request.index_id}, file_names:{request.file_names}, e:{e}, trace:{trace_info}')
        log.info(f"API /vector_store/file/list_batch failed - request_id: {request_id}, "
                 f"error: {str(e)}, execution_time: {time.time() - start_time:.2f}s")
        return FailResponse(error=str(e))