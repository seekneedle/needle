from pydantic import BaseModel


# 定义通用的响应模型
class SuccessResponse(BaseModel):
    code: int = 200
    status: str = 'success'
    data: dict = {}


class FailResponse(BaseModel):
    code: int = 400
    status: str = 'fail'
    data: dict = {}
