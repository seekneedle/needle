import base64
import os
import shutil
from config import config


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
    if (not os.path.exists(index_path)):
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
