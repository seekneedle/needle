from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()

# 创建一个 HTTPBearer 实例
security = HTTPBearer()


# 获取Authorization
def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return credentials.credentials


# 检查操作权限
def check_permission(token, resource):
    # TODO: call pmc service
    return True
