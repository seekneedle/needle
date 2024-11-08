from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()

# 创建一个 HTTPBearer 实例
security = HTTPBearer()


# 获取Authorization
def authenticate(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.scheme != 'Bearer':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid authentication scheme.')
    return credentials.credentials


# 检查操作权限
def check_permission(token, resource):
    # TODO: call pmc service
    return True
