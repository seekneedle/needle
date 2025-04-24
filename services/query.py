from pydantic import BaseModel
from typing import Dict, List, Optional
from openai import OpenAI
from utils.security import decrypt
from utils.config import config
from services.retrieve import RetrieveRequest, retrieve
from server.response import SuccessResponse


class QueryRequest(BaseModel):
    ids: List = []
    id: Optional[str] = None
    messages: List[Dict[str, str]]
    temperature: Optional[float] = None
    system: Optional[str] = None
    top_k: Optional[int] = None
    rerank_top_k: Optional[int] = None
    sparse_top_k: Optional[int] = None
    rerank_threshold: Optional[float] = None
    search_filters: Optional[Dict[str, str]] = None


class QueryResponse(BaseModel):
    content: str


SYSTEM = """# 角色
你化身为Yoyo，众信旅游——一家上市公司背后的智囊AI助理，专为内部业务团队提供高效且个性化的支持服务。你的交流风格简练而专业，每次对话皆以"老板"尊称启齿，彰显无微不至的敬意与周到。

## 技能
### 技能1: 定制化业务支持
- **快速响应**：以"老板"尊称开始每一次互动，体现高度的专业性和礼貌。
- **系统精通**：优先介绍新系统UUX的功能特性，辅助团队成员顺利过渡自旧系统TISP。

### 技能2: 知识整合与应用
- **信息调用**：所有问题，首先灵活运用已记忆的材料(${documents})，精准匹配问题需求，提供全面且针对性的解答。如果可以找到答案。就直接根据答案进行回复。如果知识库没有相关内容，使用你自己的知识进行回复。如果遇到公司规定，或者公司内部管理的问题，严格按照知识库内的材料进行回答，如果没有找到，不要使用网络信息进行回复，说明无法找到相关答案，但是可以给出一些参考信息，将参考信息输出。

## 限制与注意事项
- **服务对象明确**：明确服务于公司内部员工，非直接面向终端客户。措辞尽可能简练，清晰，体现专业性。如果遇到无法回答的问题，或者没有把握的问题，统一回复为，对不起，这个问题我无法回答，建议您询问您所在分公司的门服或者总经理，如果还无法解决，请联系全国分公司负责人艳磊总：13261203840，北京分公司振玥总：13601207715。
- **数据准确性**：确保如果询问公司规定，制度，公司要求等内容时，严格按照知识库内的材料进行回答。不要引用网络信息。
- **系统优先级**：在提及系统功能时，始终将UUX作为首要介绍对象，除非特别指明或UUX无法满足需求的情况。
- **其他注意事项**：在生成回答时，主要不要出现重复的内容。   
- **没有找到相关内容**： 如果在记忆材料中没有找到问题答案，请回答根据已知信息我们无法给出明确答案，但是可以给出一些参考信息。
- **没有找到客服电话**： 如果在记忆材料中没有找到客服电话，请不要编造电话号码或者使用其他号码。
        """


def _query(request: QueryRequest):
    if request.id:
        if request.id not in request.ids:
            request.ids.append(request.id)
    client = OpenAI(
        api_key=decrypt(config['api_key']),
        base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    )
    history_messages = request.messages[-7:]
    prompt = f'''你是一个知识库检索助手，可以根据聊天历史生成知识库检索句子。
要求只能根据聊天历史进行总结，不允许总结超出聊天历史的内容。

聊天历史是：
{history_messages}

输出：检索知识库的句子。'''
    messages = [
        {
            'role': 'user',
            'content': prompt
        }
    ]
    messages = messages + request.messages
    completion = client.chat.completions.create(
        model="qwen-plus-2024-09-19",
        messages=messages,
        temperature=0.5
    )
    query_content = completion.choices[0].message.content
    retrieve_request = RetrieveRequest(
        ids=request.ids,
        query=query_content,
        top_k=request.top_k,
        rerank_top_k=request.rerank_top_k,
        sparse_top_k=request.sparse_top_k,
        rerank_threshold=request.rerank_threshold,
        search_filters=request.search_filters
    )
    retrieve_response = retrieve(retrieve_request)
    documents = []
    for chunk in retrieve_response.chunks:
        documents.append(chunk.text)
    documents = '\n'.join(documents)
    system = request.system
    if system is None:
        system = SYSTEM
    system = system.replace('${documents}', documents)
    messages = [
        {
            'role': 'system',
            'content': system
        }
    ]
    messages = messages + history_messages
    return client, messages


async def stream_query(request: QueryRequest):
    client, messages = _query(request)
    if request.temperature is not None:
        temperature = request.temperature
    else:
        temperature = 0.5
    completion = client.chat.completions.create(
        model="qwen-plus-2024-09-19",
        messages=messages,
        temperature=temperature,
        stream=True,
        stream_options={"include_usage": True}
    )
    for chunk in completion:
        if len(chunk.choices) > 0:
            response = SuccessResponse(data=QueryResponse(content=chunk.choices[0].delta.content)).json()
            yield f"data: {response}\n\n"


def query(request: QueryRequest):
    client, messages = _query(request)
    if request.temperature is not None:
        temperature = request.temperature
    else:
        temperature = 0.5
    completion = client.chat.completions.create(
        model="qwen-plus-2024-09-19",
        temperature=temperature,
        messages=messages
    )
    return QueryResponse(content=completion.choices[0].message.content)
