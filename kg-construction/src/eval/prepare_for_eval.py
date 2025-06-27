import json
import os
from src.utils.id_operation import graph_structure, GraphStructureType
from src.config import metadata_path
from src.utils.engine import initial_engine_with_str
from src.utils.file_operation import load_json
from src.model.entity import Entity
def internal2uniform(data_root: str = metadata_path):
    """
    将内部数据转换为统一格式
    data_root/eval/nodes.json
    data_root/eval/relations.json
    """
    nodes = graph_structure(
        type=[GraphStructureType.all_node],
        return_type="object",
        cache_path=os.path.join(data_root, "graph"),
    )[0]
    relations = graph_structure(
        type=[GraphStructureType.all_relation],
        return_type="object",
        cache_path=os.path.join(data_root, "graph"),
    )[0]
    data_uniform_node = []
    data_uniform_relation = []
    for node in nodes:
        data_uniform_node.append(
            {
                "id": node.id,
                "title": node.title,
                "description": (
                    node.descriptions[-1] if isinstance(node, Entity) else node.summary
                ),
            }
        )
    for relation in relations:
        data_uniform_relation.append(
            {
                "source_id": relation.source_id,
                "target_id": relation.target_id,
                "description": (
                    relation.descriptions[-1] if len(relation.descriptions) > 0 else ""
                ),
            }
        )
    eval_root = os.path.join(data_root, "eval")
    if os.path.exists(eval_root) == False:
        os.makedirs(eval_root)
    with open(os.path.join(eval_root, "relations.json"), "w", encoding="utf-8") as f:
        json.dump(data_uniform_relation, f, ensure_ascii=False, indent=4)
    titles = [node["title"] for node in data_uniform_node]
    engine_path = os.path.join(eval_root, "engine")
    if not os.path.exists(engine_path):
        os.makedirs(engine_path)
    engine = initial_engine_with_str(
        titles,
        os.path.join(engine_path, "engine.ann"),
        os.path.join(engine_path, "table.json"),
    )
    # meta
    for ent in data_uniform_node:
        if "title" not in ent.keys():
            ent["title"] = ent["name"]
        embedding = engine.get_vector_by_id(ent["id"])
        ent["embedding"] = embedding
        ent["embedding"] = [float(e) for e in ent["embedding"]]
    with open(os.path.join(eval_root, "nodes.json"), "w", encoding="utf-8") as f:
        json.dump(data_uniform_node, f, ensure_ascii=False, indent=4)


def external2uniform(data_root: str):
    nodes_path = os.path.join(data_root, "nodes.json")
    nodes = load_json(nodes_path)
    node_names = [node["title"] for node in nodes]
    engine = initial_engine_with_str(
        node_names,
        os.path.join(data_root, "engine", "engine.ann"),
        os.path.join(data_root, "engine", "table.json"),
    )
    engine.save_state(os.path.join(data_root, "engine"))
    for ent in nodes:
        if "title" not in ent.keys():
            ent["title"] = ent["name"]
        embedding = engine.get_vector_by_id(ent["id"])
        ent["embedding"] = embedding
        ent["embedding"] = [float(e) for e in ent["embedding"]]
    with open(os.path.join(data_root, "nodes.json"), "w", encoding="utf-8") as f:
        json.dump(nodes, f, ensure_ascii=False, indent=4)
