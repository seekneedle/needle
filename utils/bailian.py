from alibabacloud_bailian20231229.client import Client as bailian20231229Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_bailian20231229 import models as bailian_20231229_models
from utils.security import decrypt
from utils.config import config
from utils.files_utils import save_file_to_index_path, calculate_md5, read_file
import os
from data.store import StoreEntity, FileEntity
from data.task import StoreTaskEntity, FileTaskEntity, TaskStatus
import traceback
import requests


def create_client() -> bailian20231229Client:
    """
    使用AK&SK初始化账号Client
    @return: Client
    @throws Exception
    """
    client_config = open_api_models.Config(
        access_key_id=decrypt(config['ak']),
        access_key_secret=decrypt(config['sk'])
    )
    # Endpoint 请参考 https://api.aliyun.com/product/bailian
    client_config.endpoint = 'bailian.cn-beijing.aliyuncs.com'
    return bailian20231229Client(client_config)


def get_category_from_index(index_id: str):
    #to do: get category_id from index_id
    return index_id


workspace_id = config['workspace_id']
runtime = util_models.RuntimeOptions()
headers = {}
client = create_client()


def add_category(name):
    category_type = 'UNSTRUCTURED'
    parent_category_id = config['parent_category_id']
    add_category_request = bailian_20231229_models.AddCategoryRequest(
        parent_category_id=parent_category_id,
        category_name=name,
        category_type=category_type
    )
    result = client.add_category_with_options(workspace_id, add_category_request, headers, runtime)
    if result.status_code != 200 or not result.body.success:
        raise RuntimeError(result.body)
    category_id = result.body.data.category_id
    return category_id


def create_index(name, category_id, chunk_size, overlap_size, separator):
    params = {
        'sink_type': 'DEFAULT',
        'name': name,
        'structure_type': 'unstructured',
        'source_type': 'DATA_CENTER_CATEGORY',
        'category_ids': [category_id]
    }

    # 动态添加可选参数
    if chunk_size:
        params['chunk_size'] = chunk_size
    if overlap_size:
        params['overlap_size'] = overlap_size
    if separator:
        params['separator'] = separator
    create_index_request = bailian_20231229_models.CreateIndexRequest(
        **params
    )
    result = client.create_index_with_options(workspace_id, create_index_request, headers, runtime)
    if result.status_code != 200 or not result.body.success:
        raise RuntimeError(result.body)
    index_id = result.body.data.id
    return index_id


def update_index(index_id):
    submit_index_job_request = bailian_20231229_models.SubmitIndexJobRequest(
        index_id=index_id
    )
    result = client.submit_index_job_with_options(workspace_id, submit_index_job_request, headers, runtime)
    if result.status_code != 200 or not result.body.success:
        raise RuntimeError(result.body)
    job_id = result.body.data.id
    return job_id


def get_index_result(index_id, job_id):
    get_index_job_status_request = bailian_20231229_models.GetIndexJobStatusRequest(
        job_id=job_id,
        index_id=index_id
    )
    result = client.get_index_job_status_with_options(workspace_id, get_index_job_status_request, headers, runtime)
    if result.status_code != 200 or not result.body.success:
        raise RuntimeError(result.body)
    return result

def add_file_lease(task_id, category_id, file_name, file_content):
    file_name = file_name
    file_path = save_file_to_index_path(task_id, file_name, file_content)
    md_5 = calculate_md5(file_path)
    size_in_bytes = str(os.path.getsize(file_path))
    apply_file_upload_lease_request = bailian_20231229_models.ApplyFileUploadLeaseRequest(
        file_name=file_name,
        md_5=md_5,
        size_in_bytes=size_in_bytes
    )
    result = client.apply_file_upload_lease_with_options(category_id, workspace_id,
                                                         apply_file_upload_lease_request,
                                                         headers,
                                                         runtime)
    if result.status_code != 200 or not result.body.success:
        raise RuntimeError(result.body)
    lease_id = result.body.data.file_upload_lease_id
    url = result.body.data.param.url
    upload_file_headers = result.body.data.param.headers
    return lease_id, url, upload_file_headers, file_path


def upload_file(file_path, url, upload_file_headers):
    file_content = read_file(file_path)
    response = requests.put(url, data=file_content, headers=upload_file_headers)
    if response.status_code != 200 or not response.ok:
        raise RuntimeError(f'Exception for upload_file: {file_path}, url: {url}, response: {response.status_code}'
                           f' {response.text}')


def add_file(category_id, lease_id):
    add_file_request = bailian_20231229_models.AddFileRequest(
        lease_id=lease_id,
        parser='DASHSCOPE_DOCMIND',
        category_id=category_id
    )
    result = client.add_file_with_options(workspace_id, add_file_request, headers, runtime)
    if result.status_code != 200 or not result.body.success:
        raise RuntimeError(result.body)
    file_id = result.body.data.file_id
    return file_id


def add_store(task_id, name, chunk_size, overlap_size, separator):
    task = StoreTaskEntity.create(task_id=task_id)
    store = StoreEntity.create()
    task.set(status=TaskStatus.RUNNING, store_id=store.id)
    try:
        category_id = add_category(name)
        store.set(category_id=category_id)
        index_id = create_index(name, category_id, chunk_size, overlap_size, separator)
        store.set(index_id=index_id)
        return store
    except Exception as e:
        trace_info = traceback.format_exc()
        task.set(status=TaskStatus.FAILED,
                 message=f'Exception for add_store, task_id: {task.task_id},  name: {name}, e: {e}, '
                         f'trace: {trace_info}')
        return None


def add_files(task_id, index_id, files):
    task = StoreTaskEntity.get_or_create(task_id=task_id)
    store = StoreEntity.query_first(index_id=index_id)
    task.set(status=TaskStatus.RUNNING, store_id=store.id)
    if files:
        for file in files:
            file_entity = FileEntity.create(store_id=store.id, doc_name=file.name.split('.')[0])
            file_task = FileTaskEntity.create(task_id=task.task_id, status=TaskStatus.RUNNING, file_id=file_entity.id)
            try:
                lease_id, url, upload_file_headers, file_path = add_file_lease(task.task_id, store.category_id,
                                                                               file.name, file.file_content)
                file_entity.set(local_path=file_path)
                upload_file(file_path, url, upload_file_headers)
                file_id = add_file(store.category_id, lease_id)
                file_entity.set(doc_id=file_id)
            except Exception as e:
                trace_info = traceback.format_exc()
                file_task.set(status=TaskStatus.FAILED,
                         message=f'Exception for add_files, task_id: {task.task_id},  id: {store.id}, file_name: '
                                 f'{file.name}, e: {e}'
                                 f', trace: {trace_info}')
        try:
            job_id = update_index(store.index_id)
            task.set(job_id=job_id)
        except Exception as e:
            trace_info = traceback.format_exc()
            task.set(status=TaskStatus.FAILED,
                     message=f'Exception for add_files, task_id: {task.task_id},  index_id: {index_id}, e: {e}, '
                             f'trace: {trace_info}')
    else:
        task.set(status=TaskStatus.COMPLETED)


def list_file(category_id):
    list_file_request = bailian_20231229_models.ListFileRequest(
        category_id=category_id
    )
    result = client.list_file_with_options(workspace_id, list_file_request, headers, runtime)
    if result.status_code != 200 or not result.body.success:
        raise RuntimeError(result.body)
    all_files = result.body.data.file_list
    return all_files
