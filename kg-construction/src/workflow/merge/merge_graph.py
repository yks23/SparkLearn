from src.model.entity import Entity
from src.model.relation import Relation
from src.utils.engine import initialize_entity_engine
from src.utils.id_operation import (
    graph_structure,
    get_relation_id,
    realloc_id,
    get_node_id,
    save_relation,
)
from src.model.graph_structure import GraphStructureType
from src.workflow.augmentation.relation_predict import identical_merge
from src.utils.file_operation import save_json
from src.config import engine_cache_path
from src.config import graph_structure_path, engine_cache_path
import os


def merge_graph_with_unstructured(
    incremental_nodes: list[Entity], incremental_relations: list[Relation]
):
    """
    合并无结构化数据
    incremental_nodes: 新增的节点,以Entity列表传入
    incremental_relations: 新增的关系,以Relation列表传入
    """
    prev_entity = graph_structure(
        type=[GraphStructureType.entity_node], return_type="object"
    )[0]
    prev_section = graph_structure(
        type=[GraphStructureType.section_node], return_type="object"
    )[0]
    new_entity = incremental_nodes
    incremental_engine_folder = os.path.join(engine_cache_path, "merge_cache")
    # 重新编号Entity
    engine_old = initialize_entity_engine(
        prev_entity,
        engine_path=os.path.join(engine_cache_path, "engine.ann"),
        table_path=os.path.join(engine_cache_path, "table.json"),
    )
    engine_new = initialize_entity_engine(
        new_entity,
        engine_path=os.path.join(incremental_engine_folder, "engine.ann"),
        table_path=os.path.join(incremental_engine_folder, "table.json"),
    )
    all_relations_prev = graph_structure(
        type=[GraphStructureType.all_relation], return_type="object"
    )[0]
    nodes_id_begin = get_node_id()
    edges_id_begin = get_relation_id()
    new_entities = []
    nodes_id_map = {}
    # 直接插入新的点
    for new_ent in new_entity:
        nodes_id_begin += 1
        engine_old.insert_entity(
            nodes_id_begin, engine_new.get_vector_by_id(new_ent.id)
        )
        nodes_id_map[new_ent.id] = nodes_id_begin
        new_ent.id = nodes_id_begin
        new_ent.to_relation = []
        new_ent.from_relation = []
        new_entities.append(new_ent)
    id_to_node = {node.id: node for node in prev_entity + new_entities + prev_section}
    # 直接插入新的边
    new_relations = []
    for rel in incremental_relations:
        id1 = nodes_id_map[rel.source_id]
        id2 = nodes_id_map[rel.target_id]
        edges_id_begin += 1
        rel.id = edges_id_begin
        rel.source_id = id1
        rel.target_id = id2
        id_to_node[id1].to_relation.append(rel.id)
        id_to_node[id2].from_relation.append(rel.id)
        new_relations.append(rel)
    # 存储新的点
    save_json(
        os.path.join(graph_structure_path, "entity_nodes.json"),
        prev_entity + new_entities,
    )
    # 储存新的边
    entities_set = set([ent.id for ent in prev_entity + new_entities])
    save_relation(all_relations_prev + new_relations, entities_set)
    node_id_map, _ = realloc_id()
    # 更新引擎
    engine_old.table = {
        node_id_map[key]: value
        for key, value in engine_old.table.items()
        if key in node_id_map
    }
    engine_old.reverse_table = {value: key for key, value in engine_old.table.items()}
    engine_old.save_state(engine_cache_path)
    # 执行合并操作
    new_entity_set = set([ent.id for ent in new_entities])

    identical_merge(
        0.55,
        engine_path=os.path.join(engine_cache_path, "engine.ann"),
        table_path=os.path.join(engine_cache_path, "table.json"),
        folder_path=engine_cache_path,
        subset=new_entity_set,
    )
    realloc_id()
    # 执行实体去重


def merge_graph_with_structured(
    incremental_cache_folder: str, incremental_engine_folder: str
):
    """
    将两个图谱进行合并，都是有结构化数据。旧图谱路径以config中的给出，新图谱以参数给出
    incremental_cache_folder: 新增的图谱的缓存文件夹
    incremental_engine_folder: 新增的图谱的引擎文件夹
    """
    prev_section = graph_structure(
        type=[GraphStructureType.section_node], return_type="object"
    )[0]
    prev_entity = graph_structure(
        type=[GraphStructureType.entity_node], return_type="object"
    )[0]
    new_section = graph_structure(
        type=[GraphStructureType.section_node],
        return_type="object",
        cache_path=incremental_cache_folder,
    )[0]
    new_entity = graph_structure(
        type=[GraphStructureType.entity_node],
        return_type="object",
        cache_path=incremental_cache_folder,
    )[0]
    # 首先重新编号Section.如果重合直接换,没重合就新建
    section_map = {sec.title: sec for sec in prev_section}
    all_relations_prev = graph_structure(
        type=[GraphStructureType.all_relation], return_type="object"
    )[0]
    all_relations_new = graph_structure(
        type=[GraphStructureType.all_relation],
        return_type="object",
        cache_path=incremental_cache_folder,
    )[0]
    exists_rel = set((rel.source_id, rel.target_id) for rel in all_relations_prev)
    new_sections = []
    nodes_id_begin = get_node_id()
    edges_id_begin = get_relation_id()
    nodes_id_map = {}
    for new_sec in new_section:
        if new_sec.title in section_map:
            nodes_id_map[new_sec.id] = section_map[new_sec.title].id
            new_sec.id = section_map[new_sec.title].id
            continue
        else:
            nodes_id_begin += 1
            nodes_id_map[new_sec.id] = nodes_id_begin
            new_sec.id = nodes_id_begin
            new_sec.to_relation = []
            new_sec.from_relation = []
            new_sections.append(new_sec)
    # 重新编号Entity
    engine_old = initialize_entity_engine(
        prev_entity,
        engine_path=os.path.join(engine_cache_path, "engine.ann"),
        table_path=os.path.join(engine_cache_path, "table.json"),
    )
    engine_new = initialize_entity_engine(
        new_entity,
        engine_path=os.path.join(incremental_engine_folder, "engine.ann"),
        table_path=os.path.join(incremental_engine_folder, "table.json"),
    )
    new_entities = []
    for new_ent in new_entity:
        nodes_id_begin += 1
        engine_old.insert_entity(
            nodes_id_begin, engine_new.get_vector_by_id(new_ent.id)
        )
        nodes_id_map[new_ent.id] = nodes_id_begin
        new_ent.id = nodes_id_begin
        new_ent.to_relation = []
        new_ent.from_relation = []
        new_entities.append(new_ent)
        print(new_ent.id)
    # 重新编号Relation,处理对应关系
    id_to_node = {
        node.id: node
        for node in prev_entity + new_sections + new_entities + prev_section
    }
    new_relations = []
    for rel in all_relations_new:
        id1 = nodes_id_map[rel.source_id]
        id2 = nodes_id_map[rel.target_id]
        if (
            (id1, id2) in exists_rel or (id2, id1) in exists_rel
        ) and rel.is_tree == True:
            continue
        edges_id_begin += 1
        rel.id = edges_id_begin
        rel.source_id = id1
        rel.target_id = id2
        id_to_node[id1].to_relation.append(rel.id)
        id_to_node[id2].from_relation.append(rel.id)
        new_relations.append(rel)
    # 存储新的图
    save_json(
        os.path.join(graph_structure_path, "section_nodes.json"),
        prev_section + new_sections,
    )
    save_json(
        os.path.join(graph_structure_path, "entity_nodes.json"),
        prev_entity + new_entities,
    )
    entities_set = set([ent.id for ent in prev_entity + new_entities])
    save_relation(all_relations_prev + new_relations, entities_set)
    node_id_map, _ = realloc_id()
    engine_old.table = {
        node_id_map[key]: value
        for key, value in engine_old.table.items()
        if key in node_id_map
    }
    engine_old.reverse_table = {value: key for key, value in engine_old.table.items()}
    engine_old.save_state(engine_cache_path)
    # 执行合并操作
    new_entity_set = set([ent.id for ent in new_entities])
    identical_merge(
        0.55,
        engine_path=os.path.join(engine_cache_path, "engine.ann"),
        table_path=os.path.join(engine_cache_path, "table.json"),
        folder_path=engine_cache_path,
        subset=new_entity_set,
    )
    realloc_id()
    # 执行实体去重
