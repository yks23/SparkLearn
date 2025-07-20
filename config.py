# model_name = "4.0Ultra"
model_name = "Pro/deepseek-ai/DeepSeek-V3"

"""
4.0Ultra
generalv3.5
max-32k
generalv3
pro-128k
lite
"""
max_thread_num = 8
""" Maximum number of threads for parallel processing """
# extra_models = ["generalv3.5", "max-32k", "generalv3", "pro-128k", "lite"]

extra_models = [
    "Pro/THUDM/glm-4-9b-chat",
    "THUDM/glm-4-9b-chat",
    "deepseek-ai/DeepSeek-V2.5",
    "deepseek-ai/DeepSeek-V3",
    "Pro/deepseek-ai/DeepSeek-V3",
]


""" List of additional models to use, e.g., ['4.0Ultra', 'generalv3.5'] """
# json_feature = {
#     "4.0Ultra": True,
#     "generalv3.5": True,
#     "max-32k": True,
#     "generalv3": True,
#     "pro-128k": True,
#     "lite": True,
# }
# for siliconflow
json_feature = {
    "THUDM/glm-4-9b-chat": True,
    "Pro/THUDM/glm-4-9b-chat": True,
    "deepseek-ai/DeepSeek-V2.5": True,
    "deepseek-ai/DeepSeek-V3": True,
    "Pro/deepseek-ai/DeepSeek-V3": False,
}
# API key configs
spark_api_key = "xqZXJdxoaaLEBIMuuCBg:FUuIHcWDmPLSpJcXsiSp"
silicon_api_key = "sk-nadkygsrqzgpzzvfgdvewsxkrbadfzwbphwdldvxliqcohof" # SiliconFlow API key, if applicable
openai_api_key = "" # OpenAI API key, if applicable
glm_api_key = "" # ChatGLM API key, if applicable
model_provider = "silicon"  # 'openai', 'chatglm', 'silicon', 'spark'
num_dims=2560
qa_temp = 1.3
# APP configs
APPID ="2d1bc910"
APISecret = "YzZjODMwNmNjNmRiMDVjOGI4MjcxZDVi"
APIKEY = "a1df9334fd048ded0c9304ccf12c20d1"