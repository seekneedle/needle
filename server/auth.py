from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
from utils.config import config
import json

app = FastAPI()

# 创建一个 HTTPBearer 实例
security = HTTPBearer()


# 获取Authorization
def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.scheme.lower() != 'bearer':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme."
        )
    return f"{credentials.scheme} {credentials.credentials}"


# 检查操作权限
def check_permission(token, action):
    ip = config['pms_ip']
    port = config['pms_port']
    # 定义URL
    url = f'http://{ip}:{port}/user/getPermission'

    # 定义headers，包括Authorization头
    headers = {
        'Content-Type': 'application/json',
        'Authorization': token
    }

    # 定义请求体
    data = {
        'action': action
    }

    # 发送POST请求
    response = requests.post(url, headers=headers, data=json.dumps(data))

    return response.json()['code'] == 200
