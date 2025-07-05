# 上面用来切换不同的配置文件
import os

from src.config_file.config_physics import *

# 下面不用改
from zhipuai import ZhipuAI
from openai import AsyncOpenAI, OpenAI

chatglm_client = ZhipuAI(api_key=glm_api_key)
openai_client = AsyncOpenAI(
    api_key=openai_api_key,
    base_url="https://api.openai.com",
)
openai_client_v2 = OpenAI(
    api_key=openai_api_key,
    base_url="https://api.openai.com/v1",
)
max_thread_num = 20
if 'meta_path' in os.environ:
    metadata_path = os.environ['meta_path'] # 路径地址
if 'raw_path' in os.environ:
    raw_path = os.environ['raw_path'] # 原始数据路径
graph_structure_path = os.path.join(metadata_path, "graph")
engine_cache_path = os.path.join(metadata_path, "engine")
request_cache_path = os.path.join(metadata_path, "cache")
extra_models = [
    "Pro/THUDM/glm-4-9b-chat",
    "THUDM/glm-4-9b-chat",
    "deepseek-ai/DeepSeek-V2.5",
    "deepseek-ai/DeepSeek-V3",
    "Pro/deepseek-ai/DeepSeek-V3",
]
json_feature = {
    "THUDM/glm-4-9b-chat": True,
    "Pro/THUDM/glm-4-9b-chat": True,
    "deepseek-ai/DeepSeek-V2.5": True,
    "deepseek-ai/DeepSeek-V3": True,
    "Pro/deepseek-ai/DeepSeek-V3": False,
}
