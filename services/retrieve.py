from pydantic import BaseModel
from typing import Optional
from utils.bailian import create_client
from alibabacloud_bailian20231229 import models as bailian_20231229_models
from alibabacloud_tea_util import models as util_models
from utils.config import config
from typing import Dict, List


class RetrieveRequest(BaseModel):
    id: str
    query: str
    top_k: Optional[int] = None
    rerank_top_k: Optional[int] = None
    sparse_top_k: Optional[int] = None
    rerank_threshold: Optional[float] = None
    search_filters: Optional[Dict[str, str]] = None


class RetrieveNode(BaseModel):
    text: str
    score: float
    metadata: Dict


class RetrieveResponse(BaseModel):
    chunks: Optional[List[RetrieveNode]] = None


def retrieve(request: RetrieveRequest):
    client = create_client()
    if request.rerank_top_k is None:
        request.rerank_top_k = 5
    if request.top_k is None:
        request.top_k = 10
    if request.sparse_top_k is None:
        request.sparse_top_k = 10
    retrieve_request = bailian_20231229_models.RetrieveRequest(
        query=request.query,
        index_id=request.id,
        enable_reranking=True,
        dense_similarity_top_k=request.top_k,
        rerank_top_n=request.rerank_top_k,
        search_filters=request.search_filters,
        sparse_similarity_top_k=request.sparse_top_k
    )
    runtime = util_models.RuntimeOptions()
    headers = {}
    # 复制代码运行请自行打印 API 的返回值
    result = client.retrieve_with_options(config['workspace_id'], retrieve_request, headers, runtime)
    chunks = []
    for node in result.body.data.nodes:
        chunks.append(RetrieveNode(score=node.score, text=node.text, metadata=node.metadata))
    return RetrieveResponse(chunks=chunks)
