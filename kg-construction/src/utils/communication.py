from src.config import model_name
from utils.api import multi_conservation, multi_embedding
import logging as log
import logging
import os
import json
import time

log = logging.getLogger(__name__)
from src.model.base_operator import (
    EmbeddingEntityoperation,
    KGoperator,
    EmbeddingSectionoperation,
    Embeddingstroperation,
)
from src.utils.file_operation import jsonalize, load_json


# 同步调用
def chat_completion(client, system_prompt: str, user_input: str) -> dict:
    """使用聊天完成模型获取响应。"""
    log.info("ask for api...")
    response = client.chat.completions.create(
        model=model_name,  # 可以根据需要替换为其他模型
        messages=[
            {"role": "user", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        temperature=0.3,  # 较低的温度以获得更确定的输出
    )
    return response


# 异步调用
def request(client, system_prompt, user_input, id):
    log.info(f"请求 API for input: {id}...")
    # 发起请求
    for _ in range(2):  # 尝试三次
        try:
            if system_prompt is not None:
                response = client.chat.asyncCompletions.create(
                    model=model_name,  # 根据需要替换为其他模型
                    messages=[
                        {"role": "user", "content": system_prompt},
                        {"role": "user", "content": user_input},
                    ],
                    temperature=0.3,  # 较低的温度以获得更确定的输出
                    max_tokens=10000,
                )
                return response.id
            else:
                response = client.embeddings.create(
                    model="embedding-3", input=user_input  # 填写需要调用的模型编码
                )
                return response.data
        except Exception as e:
            log.error(f"Error while requesting API for input {id}: {e}")
            log.error(f"user_input: {user_input}")
            time.sleep(5)
            continue
    return None


# 异步调用检查
def check_request(client, task_id):
    logging.info(f"check task {task_id}...")
    task_status = "PROCESSING"
    time.sleep(0.2)
    # 检查任务状态
    while task_status not in ["SUCCESS", "FAILED"]:
        try:
            result_response = client.chat.asyncCompletions.retrieve_completion_result(
                id=task_id
            )
        except Exception as e:
            log.error(f"Error while checking task {task_id}: {e}")
            return None
        task_status = result_response.task_status
        if task_status == "SUCCESS":
            log.info(f"Task {task_id} succeeded.")
            return result_response
        elif task_status == "FAILED":
            log.error(f"Task {task_id} failed.")
            return None

        time.sleep(3)  # 适当的延迟


def batch_chat_completion(
    client, system_prompt: str, user_inputs: list[str]
) -> list[dict]:
    """批量处理多个消息，异步调用API并返回响应。"""
    log.info("Entering batch_chat_completion...")
    log.info(f"Processing {len(user_inputs)} inputs...")
    final_result = []
    tasks_id = []
    mp = {}
    for i in range(len(user_inputs)):
        tasks_id.append(request(client, system_prompt, user_inputs[i], i % 70))
        mp[len(tasks_id) - 1] = user_inputs[i]
        if i % 70 == 69 or i == len(user_inputs) - 1:
            time.sleep(15)
            tasks = [check_request(client, task_id) for task_id in tasks_id]
            # 添加错误处理
            results = []
            for j, task in enumerate(tasks):
                if task is None:
                    log.error(f"query {mp[j]} failed, adding empty result")
                    results.append("")
                else:
                    results.append(task.choices[0].message.content)
            final_result += results
            tasks_id = []

    return final_result


# 用于单一输入
def communicate_with_agent(
    system_prompt: str,
    user_input: list[str],
    need_json: bool,
    cached_file_path: str = "",
    need_read_from_cache: bool = False,
):
    if need_read_from_cache:
        if cached_file_path != "" and os.path.exists(cached_file_path):
            return load_json(cached_file_path)
        else:
            print("cached file not found:", cached_file_path)
    result = multi_conservation(
        [system_prompt] * len(user_input), user_input, [need_json] * len(user_input)
    )
    result = [jsonalize(res) if need_json else res for res in result]
    if cached_file_path != "":
        if not os.path.exists(cached_file_path):
            os.makedirs(os.path.dirname(cached_file_path), exist_ok=True)
            with open(cached_file_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
    return result


def batch_execute_ops(client, ops: list[KGoperator]) -> list[dict]:
    """批量处理多个消息，异步调用API并返回响应。"""
    log.info("Entering batch_chat_completion...")
    log.info(f"Processing {len(ops)} inputs...")
    final_result = []
    tasks_id = []
    prompts_map = {}
    for i, op in enumerate(ops):
        if op.prompt_path not in prompts_map and op.prompt_path is not None:
            prompts_map[op.prompt_path] = open(
                op.prompt_path, "r", encoding="utf-8"
            ).read()
        request_id = request(
            client, prompts_map.get(op.prompt_path), op.user_input, i % 70
        )
        if (
            isinstance(op, EmbeddingEntityoperation)
            or isinstance(op, EmbeddingSectionoperation)
            or isinstance(op, Embeddingstroperation)
        ):
            final_result.append(request_id)
            continue
        if request_id is None:
            final_result.append(op.default_response)
            continue
        tasks_id.append((request_id, op))
        if i % 70 == 69 or i == len(ops) - 1:
            time.sleep(15)
            tasks = [check_request(client, task_id) for (task_id, opt) in tasks_id]
            # 添加错误处理
            results = []
            for j, task in enumerate(tasks):
                if task is None:
                    log.error(f"query {op.user_input} failed, adding default result")
                    results.append(tasks_id[j][1].default_response)
                else:
                    if op.prompt_path is not None:
                        results.append(task.choices[0].message.content)
                    else:
                        results.append(task["data"])

            final_result += results
            tasks_id = []
    return final_result


def execute_operator(
    ops: list[KGoperator],
    cached_file_path: str = "",
    need_read_from_cache: bool = False,
    need_show_progress: bool = True,
):
    # 存在缓存
    if need_read_from_cache:
        if cached_file_path != "":
            if os.path.exists(cached_file_path):
                return load_json(cached_file_path)
    # 长度为0
    if len(ops) == 0:
        return []
    # 要求向量
    if (
        isinstance(ops[0], EmbeddingEntityoperation)
        or isinstance(ops[0], EmbeddingSectionoperation)
        or isinstance(ops[0], Embeddingstroperation)
    ):
        result = multi_embedding([op.user_input for op in ops], need_show_progress)
        if cached_file_path != "":
            if not os.path.exists(cached_file_path):
                os.makedirs(os.path.dirname(cached_file_path), exist_ok=True)
            with open(cached_file_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
        return result
    # 要求补全
    else:
        prompts = {}
        for op in ops:
            if op.prompt_path not in prompts and op.prompt_path is not None:
                prompts[op.prompt_path] = open(
                    op.prompt_path, "r", encoding="utf-8"
                ).read()
        result = multi_conservation(
            [prompts[op.prompt_path] for op in ops],
            [op.user_input for op in ops],
            [op.return_type == "json" for op in ops],
            need_show_progress,
        )
        result = [
            jsonalize(res) if op.return_type == "json" else res
            for (op, res) in zip(ops, result)
        ]
        if cached_file_path != "":
            if not os.path.exists(cached_file_path):
                os.makedirs(os.path.dirname(cached_file_path), exist_ok=True)
                with open(cached_file_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=4)
        return result
