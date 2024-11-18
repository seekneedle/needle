import base64
import os
import shutil
from utils.config import config
import hashlib
from pydantic import BaseModel

class File(BaseModel):
    name: str
    file_base64: str

def file_to_base64(file_path):
    """将文件内容转换成Base64编码的字符串"""
    with open(file_path, 'rb') as file:  # 以二进制读模式打开文件
        encoded_string = base64.b64encode(file.read()).decode('utf-8')  # 读取文件内容，编码，然后解码成utf-8字符串  
    return encoded_string


def base64_to_file(base64_str, file_path):
    """将Base64编码的字符串解码并写入文件"""
    with open(file_path, 'wb') as file:  # 以二进制写模式打开文件
        decoded_bytes = base64.b64decode(base64_str)  # 解码Base64字符串  
        file.write(decoded_bytes)  # 写入文件  


def save_file_to_index_path(index_id, filename, base64):
    """文件流转成File，保存到index_id命名的文件夹"""
    file_path_root = os.path.join(os.path.dirname('__file__'), config['filestore_root_dir'])
    index_path = os.path.join(file_path_root, index_id)
    if not os.path.exists(index_path):
        os.makedirs(index_path)
    files_path = os.path.join(index_path, filename)
    base64_to_file(base64, files_path)
    return files_path


def delete_file(file_path):
    """  
    删除指定路径的文件  
    """
    try:
        os.remove(file_path)
        print(f'文件 {file_path} 已成功删除。')
    except FileNotFoundError:
        print(f'错误: 文件 {file_path} 不存在。')
    except PermissionError:
        print(f'错误: 没有权限删除文件 {file_path}。')
    except Exception as e:
        print(f'删除文件 {file_path} 时发生错误: {e}')


def delete_directory(dir_path):
    """  
    删除指定路径的文件夹  
    """
    try:
        shutil.rmtree(dir_path)
        print(f'文件夹 {dir_path} 已成功删除。')
    except FileNotFoundError:
        print(f'错误: 文件夹 {dir_path} 不存在。')
    except PermissionError:
        print(f'错误: 没有权限删除文件夹 {dir_path}。')
    except Exception as e:
        print(f'删除文件夹 {dir_path} 时发生错误: {e}')


def calculate_md5(file_path):
    """
    计算文件的 MD5 哈希值
    :param file_path: 文件路径
    :return: 文件的 MD5 哈希值
    """
    # 创建一个 md5 对象
    md5_hash = hashlib.md5()

    try:
        # 以二进制模式打开文件
        with open(file_path, "rb") as file:
            # 分块读取文件内容，防止大文件占用过多内存
            for chunk in iter(lambda: file.read(4096), b""):
                md5_hash.update(chunk)

        # 返回 MD5 哈希值
        return md5_hash.hexdigest()
    except FileNotFoundError:
        print('文件未找到')
        return None
    except PermissionError:
        print('没有权限访问文件')
        return None
    except Exception as e:
        print(f'发生错误: {e}')
        return None


def read_file(file_path):
    # 读取文件内容
    with open(file_path, 'rb') as file:
        file_content = file.read()
    return file_content

import os
import requests
import traceback
from utils.log import log
from data.task import TaskEntry, TaskStatus
from alibabacloud_bailian20231229 import models as bailian_20231229_models

def upload_file(client, category_id: str, workspace_id: str, task_id: str, file: File):
    """
    上传文件到指定的 category 中，并将操作添加到任务用于观察中。

    该函数分为三个主要步骤：
    1. 申请文档上传租约。
    2. 上传文件。
    3. 添加操作到任务中。

    参数:
    - client: 用于与服务器通信的客户端对象。
    - category_id: category的ID。
    - workspace_id: workspace的ID。
    - task_id: 任务的ID。
    - file: 要上传的文件对象，包含文件名和Base64编码的内容。

    返回:
    - 成功上传并添加文档后返回 (True, None)。
    - 如果任一步骤失败，则返回 (False, error_message)。
    """
    # 1. 申请文档上传租约
    file_name = file.name
    file_path = save_file_to_index_path(task_id, file_name, file.file_base64)
    md_5 = calculate_md5(file_path)
    size_in_bytes = str(os.path.getsize(file_path))
    apply_file_upload_lease_request = bailian_20231229_models.ApplyFileUploadLeaseRequest(
        file_name=file_name,
        md_5=md_5,
        size_in_bytes=size_in_bytes
    )
    try:
        result = client.apply_file_upload_lease_with_options(category_id, workspace_id,
                                                              apply_file_upload_lease_request)
        if result.status_code != 200 or not result.body.success:
            raise RuntimeError(result.body)
        lease_id = result.body.data.file_upload_lease_id
        url = result.body.data.param.url
        upload_file_headers = result.body.data.param.headers
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for upload_file/add_lease, task_id: {task_id}, e: {e}, trace: {trace_info}')
        return False, str(e)

    # 2. 上传文件
    file_content = read_file(file_path)
    response = requests.put(url, data=file_content, headers=upload_file_headers)
    if not response or response.status_code != 200 or not response.ok:
        log.error('Exception for upload_file/put_file')
        return False, 'Exception for upload_file/put_file'

    # 3. 添加文档
    add_file_request = bailian_20231229_models.AddFileRequest(
        lease_id=lease_id,
        parser='DASHSCOPE_DOCMIND',
        category_id=category_id
    )
    try:
        result = client.add_file_with_options(workspace_id, add_file_request)
        if result.status_code != 200 or not result.body.success:
            raise RuntimeError(result.body)
    except Exception as e:
        trace_info = traceback.format_exc()
        log.error(f'Exception for upload_file/add_file, task_id: {task_id}, e: {e}, trace: {trace_info}')
        return False, str(e)

    return True, None
    
if __name__ == '__main__':
    file_path = 'output/server.log'
    encode_str = file_to_base64(file_path)
    print(encode_str)
    file_path = save_file_to_index_path('test', 'server.log', encode_str)
    print(file_path)
    file_size = os.path.getsize(file_path)
    print(file_size)
