from pydantic import BaseModel
from typing import List, Optional
from utils.config import config
from utils.bailian import list_store


class Store(BaseModel):
    id: str
    name: str


class StoreListResponse(BaseModel):
    vector_stores: Optional[List[Store]] = None


def get_store_list(name: str = None):
    stores = []
    all_stores = list_store(name) # 用名字，如 '产品检索_uat'；不能用 index_id，如 'icmp3tfyk6'
    for store in all_stores:
        if '_' in store.name:
            if config['env'] in store.name:
                stores.append(Store(name=store.name, id=store.id))
        else:
            stores.append(Store(name=store.name, id=store.id))
    return StoreListResponse(vector_stores=stores)
