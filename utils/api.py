from multiprocessing import Pool, Manager
from typing import List, Dict
from tqdm import tqdm
from config import (
    model_name,
    max_thread_num,
    extra_models,
    json_feature,
    APISecret,
    APIKEY,
    APPID,
)
from openai import OpenAI
from zhipuai import ZhipuAI
import logging
from utils.edusp import get_embp_embedding, parser_Message

#TODO 完成tree-kg所需要的embedding格式函数

def get_default_client_sync():
    from config import silicon_api_key, glm_api_key, model_provider, spark_api_key

    if model_provider == "spark":
        return OpenAI(
            api_key=spark_api_key,
            base_url="https://spark-api-open.xf-yun.com/v1/",
        )
    elif model_provider == "silicon":
        return OpenAI(
            api_key=silicon_api_key,
            base_url="https://api.siliconflow.cn/v1",
        )
    elif model_provider == "chatglm":
        return ZhipuAI(api_key=glm_api_key)
    elif model_provider == "openai":
        return OpenAI(
            api_key=silicon_api_key,
            base_url="https://api.openai.com/v1",
        )
    else:
        return None


def get_embedding_client_sync():
    from config import spark_api_key, glm_api_key, model_provider

    if model_provider == "spark":
        return OpenAI(
            api_key=spark_api_key,
            base_url="https://spark-api-open.xf-yun.com/v1/",
        )
    elif model_provider == "chatglm":
        return ZhipuAI(api_key=glm_api_key)


def worker_conservation(args):
    conversations, counter, total, lock = args
    client = get_default_client_sync()
    results = []
    for i, (conversation, need_json) in enumerate(conversations):
        done = False
        for model in [model_name] + extra_models:
            try:
                if need_json and json_feature.get(model, False):
                    print('use_json_feature')
                    result = client.chat.completions.create(
                        model=model_name,
                        messages=conversation,
                        stream=False,
                        temperature=0.7,
                        response_format={"type": "json_object"},
                    )
                else:
                    result = client.chat.completions.create(
                        model=model_name,
                        messages=conversation,
                        stream=False,
                        temperature=0.7,
                    )
                results.append(result.choices[0].message.content)
                done = True
                break
            except Exception as e:
                # 这里防止没有 code 属性报错
                code = getattr(e, "code", None)
                logging.error(f"API 请求失败状态码: {code}")
                logging.error(f"请求对话: {conversation}")
                if code == 503:
                    logging.error("API 请求过多，尝试下一个模型")
                continue
        if not done:
            logging.error("所有模型都请求失败")
            results.append("")
        # 更新进度计数
        if counter is not None:
            with lock:
                counter.value += 1

    return results


def multi_process_api_conservation(
    conversations: List[List[Dict[str, str]]],
    num_processes: int = max_thread_num,
    show_progress: bool = False,
) -> List[str]:
    chunk_size = max(len(conversations) // num_processes, 1)
    conversations_chunks = [
        conversations[i : i + chunk_size]
        for i in range(0, len(conversations), chunk_size)
    ]

    manager = Manager()
    counter = manager.Value("i", 0) if show_progress else None
    lock = manager.Lock() if show_progress else None
    total = len(conversations)

    pool = Pool(processes=num_processes)

    # 把计数器传给worker
    args = [(chunk, counter, total, lock) for chunk in conversations_chunks]

    results_async = [pool.apply_async(worker_conservation, (arg,)) for arg in args]
    import time

    if show_progress:
        with tqdm(total=total) as pbar:
            last_val = 0
            while True:
                current_val = counter.value
                delta = current_val - last_val
                if delta > 0:
                    pbar.update(delta)
                    last_val = current_val
                if current_val >= total:
                    break
                time.sleep(2)

    pool.close()
    pool.join()

    final_results = []
    for r in results_async:
        final_results.extend(r.get())

    return final_results


def multi_conservation(
    system_prompt: List[str],
    user_input: List[str],
    need_json: List[bool] | bool = False,
    show_progress: bool = False,
) -> List[str]:
    """多并行单轮对话请求
    :param system_prompt: 系统提示词, List[str]
    :param user_input: 用户输入, List[str],与system_prompt一一对应
    :param need_json: 是否需要json格式的返回, List[bool] or bool
    :param show_progress: 是否显示进度条, bool
    """
    if isinstance(need_json, bool):
        need_json = [need_json] * len(system_prompt)
    conversations = []
    for prompt, user, nj in zip(system_prompt, user_input, need_json):
        conversations.append(
            (
                [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user},
                ],
                nj,
            )
        )
    results = multi_process_api_conservation(
        conversations, num_processes=max_thread_num, show_progress=show_progress
    )
    logging.info(f"{len(results)} Task Finished!")
    return results


def worker_embedding(args):
    texts, counter, total, lock = args
    results = []
    print(len(texts), "texts")
    for text in texts:
        try:
            results.append(single_embedding(text))
        except Exception as e:
            code = getattr(e, "code", None)
            logging.error(f"API 请求失败状态码: {code}")
            logging.error(f"请求文本: {text}")
            if code == 503:
                logging.error("API 请求过多，尝试下一个模型")
            continue
        # 更新进度计数
        if counter is not None:
            with lock:
                counter.value += 1

    return results


def multi_process_api_embedding(
    texts: List[str],
    num_processes: int = max_thread_num,
    show_progress: bool = False,
) -> List[List[float]]:
    chunk_size = max(len(texts) // num_processes, 1)
    texts_chunks = [texts[i : i + chunk_size] for i in range(0, len(texts), chunk_size)]

    manager = Manager()
    counter = manager.Value("i", 0) if show_progress else None
    lock = manager.Lock() if show_progress else None
    total = len(texts)

    pool = Pool(processes=num_processes)
    args = [(chunk, counter, total, lock) for chunk in texts_chunks]
    results_async = [pool.apply_async(worker_embedding, (arg,)) for arg in args]

    if show_progress:
        with tqdm(total=total) as pbar:
            last_val = 0
            import time

            while True:
                current_val = counter.value
                delta = current_val - last_val
                if delta > 0:
                    pbar.update(delta)
                    last_val = current_val
                if current_val >= total:
                    break
                time.sleep(1)
    pool.close()
    pool.join()

    results1 = []
    for r in results_async:
        results1.extend(r.get())

    result2 = []
    for result in results1:
        result2.extend(result)

    return result2


def multi_embedding(
    texts: List[str], show_progress: bool = False
) -> List[List[float]]:
    results = multi_process_api_embedding(
        texts, num_processes=max_thread_num, show_progress=show_progress
    )
    return results


def single_conversation(
    system_prompt: str,
    user_input: str,
    need_json: bool = False,
    show_progress: bool = False,
) -> str:
    """
    单次对话请求
    :param system_prompt: 系统提示词,str
    :param user_input: 用户输入,str
    :param need_json: 是否需要json格式的返回, bool
    :param show_progress: 是否显示进度条, bool

    """

    conversations = [
        (
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            need_json,
        )
    ]
    results = multi_process_api_conservation(
        conversations, num_processes=1, show_progress=show_progress
    )
    return results[0] if results else ""


def single_embedding(text: str) -> List[float]:
    """
    单次文本嵌入请求
    :param text: 文本内容,str
    """
    print("开始单次文本嵌入请求")
    print(f"文本内容: {text}")
    conversation = {'messages': [{'content': text, 'role': 'user'}]}
    result = get_embp_embedding(conversation, APPID, APIKEY, APISecret)
    return parser_Message(result)


class multiroundConversation:
    """多轮对话管理类
    用于管理多轮对话的历史记录和交互
    """

    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.conversation = [
            {"role": "system", "content": system_prompt}
        ]  # 初始化对话历史
        self.client = get_default_client_sync()

    def add_user_input(self, user_input: str):
        self.conversation.append({"role": "user", "content": user_input})

    def get_response(self, need_json: bool = False) -> str:
        response = (
            self.client.chat.completions.create(
                model=model_name,
                messages=self.conversation,
                stream=False,
                temperature=0.7,
                response_format={"type": "json_object"} if need_json else None,
            )
            .choices[0]
            .message.content
        )
        self.conversation.append({"role": "assistant", "content": response})
        return response
