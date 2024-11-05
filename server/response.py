from pydantic import BaseModel


# 定义通用的响应模型
class BaseResponse(BaseModel):
    code: int = 200
    status: str = 'success'
    data: dict = {}
