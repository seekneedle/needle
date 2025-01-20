from pydantic import BaseModel
from typing import Optional
from utils.bailian import create_client
from alibabacloud_bailian20231229 import models as bailian_20231229_models
from alibabacloud_tea_util import models as util_models
from utils.config import config
from typing import Dict, List
import traceback
from utils.log import log


class RetrieveRequest(BaseModel):
    ids: List = []
    id: Optional[str] = None
    query: Optional[str] = None
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
    if request.id:
        if request.id not in request.ids:
            request.ids.append(request.id)
    client = create_client()
    if request.rerank_top_k is None:
        request.rerank_top_k = 5
    if request.top_k is None:
        request.top_k = 10
    if request.sparse_top_k is None:
        request.sparse_top_k = 10
    chunks = []
    for id in request.ids:
        try:
            retrieve_request = bailian_20231229_models.RetrieveRequest(
                query=request.query,
                index_id=id,
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
            for node in result.body.data.nodes:
                chunks.append(RetrieveNode(score=node.score, text=node.text, metadata=node.metadata))
        except Exception as e:
            trace_info = traceback.format_exc()
            ids = str(request.ids)
            log.error(f'Exception for retrieve {ids}, index_id:{id} , e: {e}, trace: {trace_info}')
    return RetrieveResponse(chunks=chunks)
