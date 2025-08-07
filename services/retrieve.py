from pydantic import BaseModel
from typing import Optional
from utils.bailian import create_client
from alibabacloud_bailian20231229 import models as bailian_20231229_models
from alibabacloud_tea_util import models as util_models
from utils.config import config
from typing import Dict, List
import traceback
from utils.log import log
import asyncio


class RetrieveRequest(BaseModel):
    ids: List = []
    id: Optional[str] = None
    query: Optional[str] = None
    top_k: Optional[int] = None
    rerank_top_k: Optional[int] = None
    sparse_top_k: Optional[int] = None
    rerank_threshold: Optional[float] = None
    search_filters: Optional[Dict[str, str]] = None
    min_score: Optional[float] = None


class RetrieveNode(BaseModel):
    text: str
    score: float
    metadata: Dict


class RetrieveResponse(BaseModel):
    chunks: Optional[List[RetrieveNode]] = None


async def _retrieve(request, id):
    """封装retrieve操作为一个独立的函数"""
    client = create_client()
    chunks = []
    if request.min_score is None:
        request.min_score = 0.3
    try:
        retrieve_request = bailian_20231229_models.RetrieveRequest(
            query=request.query,
            index_id=id,
            enable_reranking=True,
            dense_similarity_top_k=request.top_k,
            rerank_top_n=request.rerank_top_k,
            search_filters=request.search_filters,
            sparse_similarity_top_k=request.sparse_top_k,
            rerank_min_score=request.min_score
        )
        runtime = util_models.RuntimeOptions()
        headers = {}
        result = await client.retrieve_with_options_async(config['workspace_id'], retrieve_request, headers, runtime)
        if result.body and result.body.data and result.body.data.nodes:
            for node in result.body.data.nodes:
                chunks.append(RetrieveNode(score=node.score, text=node.text, metadata=node.metadata))
    except Exception as e:
        trace_info = traceback.format_exc()
        ids = str(request.ids)
        log.error(f'Exception for retrieve {ids}, index_id:{id} , e: {e}, trace: {trace_info}')
    return chunks


async def retrieve(request: RetrieveRequest):
    if request.id:
        if request.id not in request.ids:
            request.ids.append(request.id)
    if request.rerank_top_k is None:
        request.rerank_top_k = 5
    if request.top_k is None:
        request.top_k = 10
    if request.sparse_top_k is None:
        request.sparse_top_k = 10

    all_chunks = []

    # Create a list of tasks for each ID
    tasks = [_retrieve(request, id) for id in request.ids]

    # Run all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    for id, result in zip(request.ids, results):
        if isinstance(result, Exception):
            log.error(f'Retrieve generated an exception for index_id: {id}, exception: {result}')
        else:
            all_chunks.extend(result)

    return RetrieveResponse(chunks=all_chunks)
