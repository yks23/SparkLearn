import os

from src.model.graph_structure import GraphStructureType
from src.utils import execute_operator
from src.utils import save_json
from src.utils.id_operation import graph_structure
from src.config import request_cache_path, graph_structure_path
from src.model.base_operator import LocalityRoleOperation
import logging

def get_local_role(need_ask=False):
    entities = graph_structure(
        type=[GraphStructureType.entity_node], return_type="object"
    )[0]
    relations = graph_structure(
        type=[GraphStructureType.entity_related_relation], return_type="object"
    )[0]
    ops = []
    entity_dict = {ent.id: ent for ent in entities}
    # 是否需要询问LLM以判断是否核心实体
    if need_ask:
        for entity in entities:
            op = LocalityRoleOperation(entity, entities)
            ops.append(op)
        response = execute_operator(
            ops,
            cached_file_path=os.path.join(request_cache_path, "locality_role.json"),
            need_read_from_cache=True,
        )
        cnt_core = 0
        for res, op in zip(response, ops):
            res = op.repair(res)
            op.core_entity.is_core_entity = res
            if res:
                cnt_core += 1
    else:
        cnt_core = 0
        for ent in entities:
            if len(ent.to_relation) + len(ent.from_relation) == 1:
                ent.is_core_entity = False
            else:
                ent.is_core_entity = True
                cnt_core += 1
    cnt_tree = 0
    for rel in relations:
        if (
            entity_dict[rel.source_id].is_core_entity
            != entity_dict[rel.target_id].is_core_entity
        ):
            rel.is_tree = True
            cnt_tree += 1
        else:
            rel.is_tree = False
    logging.info(
        f"core entity num: {cnt_core}, tree relation num: {cnt_tree}"
    )
    save_json(os.path.join(graph_structure_path, "entity_nodes.json"), entities)
    save_json(os.path.join(graph_structure_path, "entity_related.json"), relations)
