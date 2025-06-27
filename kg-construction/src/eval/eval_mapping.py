from src.utils import load_json, save_json, SearchEngine
from src.utils.engine import initial_with_meta
from src.model.base_operator import CheckInOperation
from src.utils.graph_dist import compute_shortest_paths
from src.utils.communication import execute_operator
import os
import json


def get_equal_id_map(nodes1, nodes2, engine1: SearchEngine, engine2: SearchEngine):
    """nodes1:List[dict],nodes2:List[dict]"""
    # First , nodes1 fit nodes2
    raw = []
    candidates = []
    id_map = {}
    for i, node in enumerate(nodes1):
        vec1 = engine1.get_vector_by_id(i)
        closed_ = engine2.search_by_vector(vec1, 10)
        closed_ = closed_[:5]
        candidates.append(closed_)
        closed_name = [nodes2[c]["title"] for c in closed_]
        if "title" not in node.keys() and "name" in node.keys():
            node["title"] = node["name"]
        raw.append((node["title"], closed_name))
    groups = [raw[i : i + 10] for i in range(0, len(raw), 10)]
    opts = [CheckInOperation(group, type_=2) for group in groups]
    response_raw = execute_operator(
        opts,
        cached_file_path="./llm_description.json",
        need_read_from_cache=False,
        need_show_progress=True,
    )
    response = []
    for res in response_raw:
        response += res
    for i, res in enumerate(response):
        if res != -1:
            try:
                id_map[i] = candidates[i][res]
            except:
                pass
    return id_map


def MEC_MED(gt_root, pred_root):
    nodes1 = load_json(os.path.join(gt_root, "nodes.json"))
    nodes2 = load_json(os.path.join(pred_root, "nodes.json"))
    engine2 = initial_with_meta(os.path.join(pred_root, "nodes.json"))
    result_path = os.path.join(pred_root, "result")
    distance_path = os.path.join(pred_root, "distance.json")
    if os.path.exists(result_path) == False:
        os.makedirs(result_path)
    if os.path.exists(distance_path):
        dist_map = load_json(distance_path)
    else:
        dist_map = compute_shortest_paths(
            os.path.join(pred_root, "relations.json"), len(nodes2)
        )
        save_json(distance_path, dist_map)

    # calculate pair-wise distance average
    connect_pair = []
    for i in range(len(nodes2)):
        for j in range(i + 1, len(nodes2)):
            if dist_map[i][j] != -1:
                connect_pair.append((i, j, dist_map[i][j]))

    average_raw_dis = (
        sum([pair[2] for pair in connect_pair]) / len(connect_pair)
        if connect_pair
        else 0
    )
    gt_name_short = gt_root[-3:]
    if os.path.exists(os.path.join(pred_root, f"id_map_{gt_name_short}.json")):
        common_id_map = load_json(
            os.path.join(pred_root, f"id_map_{gt_name_short}.json")
        )
    else:
        engine1 = initial_with_meta(os.path.join(gt_root, "nodes.json"))
        common_id_map = get_equal_id_map(nodes1, nodes2, engine1, engine2)

    save_json(os.path.join(pred_root, f"id_map_{gt_name_short}.json"), common_id_map)

    """common_id_map:dict[int,int],key is the id of node in graph1,value is the id of node in graph2"""
    dists = []
    relations1 = load_json(os.path.join(gt_root, "relations.json"))
    common_id_map = {int(k): int(v) for k, v in common_id_map.items()}
    for rel in relations1:
        if (
            rel["source_id"] in common_id_map.keys()
            and rel["target_id"] in common_id_map.keys()
        ):
            newdis = dist_map[common_id_map[rel["source_id"]]][
                common_id_map[rel["target_id"]]
            ]
            if newdis != -1 and newdis != 0:
                dists.append(newdis)

    connection_rate = len(dists) / len(relations1)
    if connection_rate == 0:
        average_dis = 0
    else:
        average_dis = sum(dists) / len(dists)
    # average_dis = 1
    if not os.path.exists(os.path.join(pred_root, "result.json")):
        prev_data = []
    else:
        with open(os.path.join(pred_root, "result.json"), "r", encoding="utf-8") as f:
            prev_data = json.load(f)
    with open(os.path.join(pred_root, "result.json"), "w", encoding="utf-8") as f:
        result = {
            "name": "Mapping Evaluation",
            "pred_root": pred_root,
            "gt_root": gt_root,
            "MEC": connection_rate,
            "MED": average_dis,
            "average_raw_dis": average_raw_dis,
            "normalized_MED": (
                average_dis / average_raw_dis if average_raw_dis != 0 else 0
            ),
        }
        prev_data.append(result)
        json.dump(prev_data, f, ensure_ascii=False, indent=4)
