import os
from src.model.graph_structure import GraphStructureType
from src.model.relation import Relation
from src.utils import communicate_with_agent
from src.utils import save_json
from src.utils.id_operation import graph_structure
from src.config import request_cache_path, final_prompt_path,user_input,graph_structure_path
import logging
def augment_entities(entity_nodes: list, prompt_template: str,relations:dict,entities:dict,is_first:bool):
    input_content=[]
    need_aug=[]
    for entity in entity_nodes:
        if entity.finish_augment==True:
            continue
        description = "实体名称:" +entity.title+"\n实体描述:\n"+entity.descriptions[-1]
        description+="\n局部相关描述:\n"
        for relation_id in (entity.to_relation+entity.from_relation):
            if relation_id not in relations.keys():
                continue
            relation=relations[relation_id]
            if relation.source_id==entity.id:
                description+='\n- '+entity.title+' '+relation.type+' '+entities[relation.target_id].title
                description+="\n 解释："+relation.descriptions[-1]
            else:
                description+='\n- '+entities[relation.source_id].title+' '+relation.type+' '+entity.title
                description+="\n 解释："+relation.descriptions[-1]
        full_user_input=user_input.replace("{text}", description)
        input_content.append(full_user_input)
        need_aug.append(entity)
    if is_first:
        responses=communicate_with_agent(system_prompt=prompt_template, user_input=input_content, need_json=False,cached_file_path=request_cache_path+"/entity_augmented_generation.json",)
        for i in range(len(need_aug)):
            need_aug[i].descriptions.append(responses[i])
    else:
        responses=communicate_with_agent(system_prompt=prompt_template, user_input=input_content, need_json=False,cached_file_path=request_cache_path+"/entity_augmented_generation.json")
        for i in range(len(need_aug)):
            need_aug[i].descriptions.append(responses[i])
def augment_relations(relation_edges: list[Relation], prompt_template: str,entities:dict,is_first:bool):
    input_content=[]
    need_aug=[]
    for relation in relation_edges:
        if relation.finish_augment==True:
            continue
        if not is_first:
            description = "\n源实体名称:"+entities[relation.source_id].title+"\n源实体解释:"+entities[relation.source_id].descriptions[-1]+"\n目标实体名称:"+entities[relation.target_id].title+"\n目标实体解释:"+entities[relation.target_id].descriptions[-1]
            description+="\n现有描述:\n"+relation.descriptions[-1]+"\n"
            full_user_input=user_input.replace("{text}", description)
            input_content.append(full_user_input)
            need_aug.append(relation)
        else:
            description = "- 关系三元组:"+entities[relation.source_id].title+" "+relation.type+" "+entities[relation.target_id].title
            description+="\n- 详细描述:"
            description+="\n- "+entities[relation.source_id].title+':'+entities[relation.source_id].descriptions[-1]
            description+="\n- "+entities[relation.target_id].title+':'+entities[relation.target_id].descriptions[-1]
            description+="\n- "+relation.type+':'+relation.descriptions[-1]
            full_user_input=user_input.replace("{text}", description)
            input_content.append(full_user_input)
            need_aug.append(relation)
    responses=communicate_with_agent(system_prompt=prompt_template, user_input=input_content, need_json=False,cached_file_path=request_cache_path+"/relation_augmented_generation.json")
    for i in range(len(need_aug)):
        need_aug[i].descriptions.append(responses[i])

def augmented_generation(need_entity:bool,need_relation:bool,is_first:bool):
    # 设置缓存路径和文件路径
    cache_folder = graph_structure_path
    nodes_file = os.path.join(cache_folder, "entity_nodes.json")
    relations_file = os.path.join(cache_folder, "entity_related.json")
    if is_first:
        entity_prompt_file=os.path.join(os.getcwd(),final_prompt_path,"entity_augmented_generation.txt")
    else:
        entity_prompt_file=os.path.join(os.getcwd(),final_prompt_path,"inc_entity_augmented_generation.txt")
    if is_first:
        rellation_prompt_file=os.path.join(os.getcwd(),final_prompt_path,"relation_augmented_generation.txt")
    else:
        rellation_prompt_file=os.path.join(os.getcwd(),final_prompt_path,"inc_relation_augmented_generation.txt")
    
    # 读取节点和关系数据
    with open(entity_prompt_file, 'r', encoding='utf-8') as file:
        entity_prompt_template = file.read()
    with open(rellation_prompt_file, 'r', encoding='utf-8') as file:
        relation_prompt_template = file.read()
    # 初始化实体节点和关系边
    [entity_nodes,relation_edges] = graph_structure(type=[GraphStructureType.entity_node,GraphStructureType.entity_related_relation],return_type='object')
    if is_first and need_entity:
        # 清空长度
        for entity in entity_nodes:
            entity.descriptions=[entity.descriptions[0]]
    if is_first and need_relation:
        for relation in relation_edges:
            relation.descriptions=[relation.descriptions[0]]
    redict={relation.id:relation for relation in relation_edges}
    endict={entity.id:entity for entity in entity_nodes}
    # 增强实体信息
    if need_entity:
        augment_entities(entity_nodes, entity_prompt_template,redict,endict,is_first)
    if need_relation:
        augment_relations(relation_edges, relation_prompt_template,endict,is_first)
    # 保存增强后的数据
    save_json(nodes_file,  entity_nodes)
    save_json(relations_file, relation_edges)
    logging.info(f"增强后的实体节点数：{len(entity_nodes)}")
    logging.info(f"增强后的关系边数：{len(relation_edges)}")
