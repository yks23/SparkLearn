import os
from ...src.model import Section, Relation, Entity
from ...src.utils.file_operation import load_json, save_json
from ...src.config import graph_structure_path
from ...src.model.graph_structure import GraphStructureType
def get_adjacency_matrix():
    relations=graph_structure([GraphStructureType.all_relation],return_type="object")[0]
    adjacency_matrix_to = {(rel.source_id, rel.target_id) for rel in relations}
    adjacency_matrix_from = {(rel.target_id, rel.source_id) for rel in relations}
    return adjacency_matrix_to | adjacency_matrix_from
def from_prev_to_new():
    
    all_relations=load_json(os.path.join(graph_structure_path,"all_relations.json"))
    all_nodes=load_json(os.path.join(graph_structure_path,"all_node.json"))
    entity_ids={node['id'] for node in all_nodes if "is_elemental" not in node.keys()}
    has_subsection_relations = [
        rel for rel in all_relations if rel["type"] == "has_subsection"
    ]
    has_entity_relations = [rel for rel in all_relations if rel["type"] == "has_entity"]
    section_related_relations = [
        rel
        for rel in all_relations
        if rel["source_id"] not in entity_ids
        and rel["target_id"] not in entity_ids
        and rel["type"] != "has_entity"
        and rel["type"] != "has_subsection"
    ]
    entity_related_relations = [
        rel
        for rel in all_relations
        if rel["source_id"] in entity_ids and rel["target_id"] in entity_ids
    ]
    save_json(os.path.join(graph_structure_path, "has_subsection.json"), has_subsection_relations)
    save_json(
        os.path.join(graph_structure_path, "section_related.json"), section_related_relations
    )
    save_json(os.path.join(graph_structure_path, "has_entity.json"), has_entity_relations)
    save_json(os.path.join(graph_structure_path, "entity_related.json"), entity_related_relations)

    
def save_relation(all_relations: list[dict | Relation], entity_ids: set):
    """
    用于存储关系。
    entity_ids代表的是实体id的集合
    用于区分relation的种类
    """
    if isinstance(all_relations[0], dict):
        has_subsection_relations = [
        rel for rel in all_relations if rel["type"] == "has_subsection"
    ]
        has_entity_relations = [rel for rel in all_relations if rel["type"] == "has_entity"]
        section_related_relations = [
            rel
            for rel in all_relations
            if rel["source_id"] not in entity_ids
            and rel["target_id"] not in entity_ids
            and rel["type"] != "has_entity"
            and rel["type"] != "has_subsection"
        ]
        entity_related_relations = [
            rel
            for rel in all_relations
            if rel["source_id"] in entity_ids and rel["target_id"] in entity_ids
        ]
        if len(has_subsection_relations) != 0:
            save_json(os.path.join(graph_structure_path, "has_subsection.json"), has_subsection_relations)
        if len(section_related_relations) != 0:
            save_json(
            os.path.join(graph_structure_path, "section_related.json"), section_related_relations
        )
        if len(has_entity_relations) != 0:
            save_json(os.path.join(graph_structure_path, "has_entity.json"), has_entity_relations)
        if len(entity_related_relations) != 0:
            save_json(os.path.join(graph_structure_path, "entity_related.json"), entity_related_relations)
    else:
        has_subsection_relations = [
        rel for rel in all_relations if rel.type == "has_subsection"
    ]
        has_entity_relations = [rel for rel in all_relations if rel.type == "has_entity"]
        section_related_relations = [
            rel
            for rel in all_relations
            if rel.source_id not in entity_ids
            and rel.target_id not in entity_ids
            and rel.type != "has_entity"
            and rel.type != "has_subsection"
        ]
        entity_related_relations = [
            rel
            for rel in all_relations
            if rel.source_id in entity_ids and rel.target_id in entity_ids
        ]
        if len(has_subsection_relations) != 0:
            save_json(os.path.join(graph_structure_path, "has_subsection.json"), has_subsection_relations)
        if len(section_related_relations) != 0:
            save_json(
            os.path.join(graph_structure_path, "section_related.json"), section_related_relations
        )
        if len(has_entity_relations) != 0:
            save_json(os.path.join(graph_structure_path, "has_entity.json"), has_entity_relations)
        if len(entity_related_relations) != 0:
            save_json(os.path.join(graph_structure_path, "entity_related.json"), entity_related_relations)


def realloc_id(cache_path: str = graph_structure_path):
    """
    常用函数。
    效果是将当前存储的图结构进行分配id。使得id连续
    例如实体id:0 1 3 5，分配后变为0 1 2 3。对应的关系也会进行修改
    关系的id也会进行重新分配，关联的实体的对应字段也会修改
    """
    node_path = [
        os.path.join(cache_path, "section_nodes.json"),
        os.path.join(cache_path, "entity_nodes.json"),
    ]
    relation = [
        os.path.join(cache_path, "has_subsection.json"),
        os.path.join(cache_path, "section_related.json"),
        os.path.join(cache_path, "has_entity.json"),
        os.path.join(cache_path, "entity_related.json"),
    ]
    all_nodes = []
    all_relations = []
    for node in node_path:
        if os.path.exists(node):
            all_nodes.extend(load_json(node))
    for rel in relation:
        if os.path.exists(rel):
            all_relations.extend(load_json(rel))
    node_id_dict = {}
    rel_id_dict = {}
    
    for i, node in enumerate(all_nodes):
        node_id_dict[node["id"]] = int(i)
    
    for i, rel in enumerate(all_relations):
        rel_id_dict[rel["id"]] = int(i)
    for node in all_nodes:
        node["id"] = node_id_dict[node["id"]]
        node["to_relation"] = [rel_id_dict[rel_id] for rel_id in node["to_relation"] if rel_id in rel_id_dict.keys()]
        node["from_relation"] = [
            rel_id_dict[rel_id] for rel_id in node["from_relation"] if rel_id in rel_id_dict.keys()
        ]
    for rel in all_relations:
        rel["id"] = rel_id_dict[rel["id"]]
        rel["source_id"] = node_id_dict[rel["source_id"]]
        rel["target_id"] = node_id_dict[rel["target_id"]]
    
    save_json(os.path.join(cache_path, "all_node.json"), all_nodes)
    save_json(os.path.join(cache_path, "all_relations.json"), all_relations)
    all_section_nodes = [node for node in all_nodes if "is_elemental" in node]
    all_entity_nodes = [node for node in all_nodes if "is_elemental" not in node]
    entity_ids = [node["id"] for node in all_entity_nodes]

    has_subsection_relations = [
        rel for rel in all_relations if rel["type"] == "has_subsection"
    ]
    has_entity_relations = [rel for rel in all_relations if rel["type"] == "has_entity"]
    section_related_relations = [
        rel
        for rel in all_relations
        if rel["source_id"] not in entity_ids
        and rel["target_id"] not in entity_ids
        and rel["type"] != "has_entity"
        and rel["type"] != "has_subsection"
    ]
    entity_related_relations = [
        rel
        for rel in all_relations
        if rel["source_id"] in entity_ids and rel["target_id"] in entity_ids
    ]
    
    save_json(os.path.join(cache_path, "section_nodes.json"), all_section_nodes)
    save_json(os.path.join(cache_path, "entity_nodes.json"), all_entity_nodes)
    save_json(os.path.join(cache_path, "has_subsection.json"), has_subsection_relations)
    save_json(
        os.path.join(cache_path, "section_related.json"), section_related_relations
    )
    save_json(os.path.join(cache_path, "has_entity.json"), has_entity_relations)
    save_json(os.path.join(cache_path, "entity_related.json"), entity_related_relations)
    return node_id_dict, rel_id_dict


def graph_structure(type: list, return_type: str = "dict",cache_path:str=graph_structure_path):
    """返回图结构的节点和关系"""
    return_list = []
    for ttype in type:
        if ttype == GraphStructureType.all_node:
            """ "在这种情况下，返回字典，包含所有的点"""
            nodes = load_json(os.path.join(cache_path, "all_node.json"))
            if return_type != "dict":
                nodes = [
                    (
                        Section(**node)
                        if node.get("is_elemental") != None
                        else Entity(**node)
                    )
                    for node in nodes
                ]
            return_list.append(nodes)
        if ttype == GraphStructureType.all_relation:
            """在这种情况下，返回所有的章节节点和关系"""
            relations = load_json(os.path.join(cache_path, "all_relations.json"))
            if return_type != "dict":
                relations = [Relation(**relation) for relation in relations]
            return_list.append(relations)
        if ttype == GraphStructureType.section_node:
            """在这种情况下，返回所有的章节节点"""
            nodes = load_json(os.path.join(cache_path, "section_nodes.json"))
            if return_type != "dict":
                nodes = [Section(**node) for node in nodes]
            return_list.append(nodes)
        if ttype == GraphStructureType.entity_node:
            """在这种情况下，返回所有的实体节点"""
            nodes = load_json(os.path.join(cache_path, "entity_nodes.json"))
            if return_type != "dict":
                nodes = [Entity(**node) for node in nodes]
            return_list.append(nodes)
        if ttype == GraphStructureType.section_belong_connection:
            """在这种情况下，返回所有的章节关系"""
            relations = load_json(os.path.join(cache_path, "has_subsection.json"))
            if return_type != "dict":
                relations = [Relation(**relation) for relation in relations]
            return_list.append(relations)
        if ttype == GraphStructureType.section_related_connection:
            """在这种情况下，返回所有的章节关系"""
            relations = load_json(os.path.join(cache_path, "section_related.json"))
            if return_type != "dict":
                relations = [Relation(**relation) for relation in relations]
            return_list.append(relations)
        if ttype == GraphStructureType.section_all_relation:
            relations = load_json(
                os.path.join(cache_path, "has_subsection.json")
            ) + load_json(os.path.join(cache_path, "section_related.json"))
            if return_type != "dict":
                relations = [Relation(**relation) for relation in relations]
            return_list.append(relations)
        if ttype == GraphStructureType.has_entity_relation:
            relations = load_json(os.path.join(cache_path, "has_entity.json"))
            if return_type != "dict":
                relations = [Relation(**relation) for relation in relations]
            return_list.append(relations)
        if ttype == GraphStructureType.entity_related_relation:
            relations = load_json(os.path.join(cache_path, "entity_related.json"))
            if return_type != "dict":
                relations = [Relation(**relation) for relation in relations]
            return_list.append(relations)
        if ttype == GraphStructureType.adjacency_matrix:
            if return_type=='all':
                relations = load_json(os.path.join(cache_path, "all_relations.json"))
            if return_type=='entity':
                relations = load_json(os.path.join(cache_path, "entity_related.json"))
            if return_type=='section':
                relations = load_json(os.path.join(cache_path, "section_related.json"))+load_json(os.path.join(cache_path, "has_subsection.json"))
            adjacency_matrix_to = {(rel["source_id"], rel["target_id"]) for rel in relations}
            adjacency_matrix_from = {(rel["target_id"], rel["source_id"]) for rel in relations}
            return_list.append(adjacency_matrix_to | adjacency_matrix_from)
            
    return return_list
def get_relation_id()->int:
    relations=graph_structure([GraphStructureType.all_relation],return_type="object")[0]
    id = max([relation.id for relation in relations])
    return id
def get_node_id()->int:
    nodes=graph_structure([GraphStructureType.all_node],return_type="object")[0]
    id = max([node.id for node in nodes])
    return id
def deduplicate_relation():
    relations=graph_structure([GraphStructureType.all_relation],return_type="object")[0]
    relation_dict={}
    entities=graph_structure([GraphStructureType.entity_node],return_type="object")[0]
    entity_ids={entity.id for entity in entities}
    for rel in relations:
        if (rel.target_id,rel.source_id) in relation_dict.keys():
            relation_dict[(rel.target_id,rel.source_id)].descriptions+=rel.descriptions
        else:
            relation_dict[(rel.source_id,rel.target_id)]=rel
    save_relation(list(relation_dict.values()),entity_ids)
    realloc_id()
def get_parent():
    relations=graph_structure([GraphStructureType.section_belong_connection],return_type="object")[0]+graph_structure([GraphStructureType.has_entity_relation],return_type="object")[0]
    parent={}
    for rel in relations:
        parent[rel.target_id]=parent.get(rel.target_id,[])+[rel.source_id]
    return parent
def get_sons():
    relations=graph_structure([GraphStructureType.section_belong_connection],return_type="object")[0]+graph_structure([GraphStructureType.has_entity_relation],return_type="object")[0]
    nodes=graph_structure([GraphStructureType.all_node],return_type="object")[0]
    id_to_node={node.id:node for node in nodes}
    to_nodes={}
    for rel in relations:
        to_nodes[rel.source_id]=to_nodes.get(rel.source_id,[])+[rel.target_id]
    for key in to_nodes.keys():
        to_nodes[key]=[id_to_node[node_id] for node_id in to_nodes[key]]
    return to_nodes
