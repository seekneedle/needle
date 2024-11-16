from alibabacloud_bailian20231229.client import Client as bailian20231229Client
from alibabacloud_tea_openapi import models as open_api_models
from utils.security import decrypt
from utils.config import config


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