model_name = "4.0Ultra"
"""
4.0Ultra
generalv3.5
max-32k
generalv3
pro-128k
lite
"""
max_thread_num = 4
""" Maximum number of threads for parallel processing """
extra_models = ["generalv3.5", "max-32k", "generalv3", "pro-128k", "lite"]
""" List of additional models to use, e.g., ['4.0Ultra', 'generalv3.5'] """
json_feature = {
    "4.0Ultra": True,
    "generalv3.5": True,
    "max-32k": True,
    "generalv3": True,
    "pro-128k": True,
    "lite": True,
}
# API key configs
spark_api_key = "PqaddjxvbBSYjGckQcxD:qzaVIDUrLtMTVLZuEZkg"
silicon_api_key = "" # SiliconFlow API key, if applicable
openai_api_key = "" # OpenAI API key, if applicable
glm_api_key = "" # ChatGLM API key, if applicable
model_provider = "spark"  # 'openai', 'chatglm', 'silicon', 'spark'
num_dims=2560

# APP configs
APPID ='e7832989'
APISecret = 'NDY1YWZkZmJmNzhmYTYzNmI5NjViMjVl'
APIKEY = '6d024c927a931a7d244d332af67472e9'