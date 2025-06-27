# 衡量三个指标：1.领域相关度 2.实体完整性 3.实体丰富度
# 方法：1.对于所有的计算领域相关度的得分和实体完整性得分，取平均值作为领域相关度得分和实体完整性得分
# 2. 实体丰富度支持两种方法比较。第一种直接关键词匹配；第二种算关键词向量embedding之后找最近距离
from src.utils.id_operation import graph_structure, GraphStructureType
from src.utils.engine import initial_with_meta
import json
from src.model.base_operator import (
    CheckInOperation,
    RelevanceOperation,
)
from src.utils.file_operation import load_json
import os
from src.utils.communication import execute_operator
def ER_CROSS(gt_root: str, pred_root: str):
    gt_meta_path = os.path.join(gt_root, "nodes.json")
    pred_meta_path = os.path.join(pred_root, "nodes.json")
    engine = initial_with_meta(pred_meta_path)
    gt_data = load_json(gt_meta_path)
    pred_data = load_json(pred_meta_path)
    hits = 0
    opts = []
    raw = []
    for data in gt_data:
        closed_ = engine.search_by_vector(data["embedding"], 4)
        closed_name = [pred_data[c]["title"] for c in closed_]
        raw.append((data["title"] if "title" in data else data["name"], closed_name))
    groups = [raw[i : i + 5] for i in range(0, len(raw), 5)]
    opts = [CheckInOperation(group, type_=1) for group in groups]
    response = execute_operator(opts, cached_file_path="./llm_description.json")
    all_response = []
    for res in response:
        all_response += res
    for res, data in zip(all_response, gt_data):
        if res:
            hits += 1
    if not os.path.exists(os.path.join(pred_root, "result.json")):
        prev_data = []
    else:
        with open(os.path.join(pred_root, "result.json"), "r", encoding="utf-8") as f:
            prev_data = json.load(f)
    if isinstance(prev_data, dict):
        prev_data=[prev_data]
    with open(os.path.join(pred_root, "result.json"), "w", encoding="utf-8") as f:
        result = {
            "name": "ER_eval",
            "pred_root": pred_root,
            "gt_root": gt_root,
            "hit_rate": hits / len(gt_data),
            "hit_num": hits,
            "effective": hits / len(engine.table),
            "F1": 2 * hits / (len(gt_data) + len(engine.table)),
        }
        prev_data.append(result)
        json.dump(prev_data, f, ensure_ascii=False, indent=4)


def ES_external(overall_summary: str, data_path: str):
    """

    Evaluate the entity specifility of the external data.
    data_path:
        [
            - id
            - title
            - description
        ]
    overall_summary: the overall summary of the data
    """
    # 加载entity
    meta_path = os.path.join(data_path, "nodes.json")
    entities = load_json(meta_path)
    input = []
    ops = []
    for ent in entities:
        ent["description"] = ent.get("description", "")
        s = (
            "实体名称：" + ent["title"] + "\n" + "实体描述：" + str(ent["description"])
            if ent["description"] != ""
            else "实体名称：" + ent["title"]
        )
        input.append(s)
    groups = [input[i : i + 16] for i in range(0, len(input), 16)]
    ops = [RelevanceOperation(overall_summary, group) for group in groups]
    response = execute_operator(
        ops,
        cached_file_path=os.path.join(
            os.path.dirname(data_path), "cache", "entity_eval_relevance.json"
        ),
    )
    score = []
    for res in response:
        sub_scores = RelevanceOperation.repair(res)
        score += sub_scores
    average_relevance = sum(score) / len(score)
    if not os.path.exists(os.path.join(data_path, "result.json")):
        prev_data = []
    else:
        with open(os.path.join(data_path, "result.json"), "r", encoding="utf-8") as f:
            prev_data = json.load(f)
    with open(os.path.join(data_path, "result.json"), "w", encoding="utf-8") as f:
        result = {
            "name": "ES_eval",
            "root": data_path,
            "average_specifility": average_relevance,
        }
        prev_data.append(result)
        json.dump(prev_data, f, ensure_ascii=False, indent=4)


def ES_internal(overall_summary: str, data_root: str):
    """
    Evaluate the entity specifility of the internal data.
    """
    entities = graph_structure(
        type=[GraphStructureType.entity_node], return_type="dict"
    )[0]
    input = []
    ops = []
    for ent in entities:
        ent["description"] = ent.get("description", "")
        s = (
            "实体名称：" + ent["title"] + "\n" + "实体描述：" + ent["description"][-1]
            if len(ent["description"])
            else "实体名称：" + ent["title"]
        )
        input.append(s)
    groups = [input[i : i + 16] for i in range(0, len(input), 16)]
    ops = [RelevanceOperation(overall_summary, group) for group in groups]
    response = execute_operator(
        ops, cached_file_path=os.path.join(data_root, "entity_eval_relevance.json")
    )
    score = []
    for res in response:
        sub_scores = RelevanceOperation.repair(res)
        score += sub_scores
    average_relevance = sum(score) / len(score)
    if not os.path.exists(os.path.join(data_root, "result.json")):
        prev_data = []
    else:
        with open(os.path.join(data_root, "result.json"), "r", encoding="utf-8") as f:
            prev_data = json.load(f)
    with open(os.path.join(data_root, "result.json"), "w", encoding="utf-8") as f:
        result = {
            "name": "ES_eval",
            "root": data_root,
            "average_specifility": average_relevance,
        }
        prev_data.append(result)
        json.dump(prev_data, f, ensure_ascii=False, indent=4)
