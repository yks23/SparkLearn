from typing import Tuple, List, Dict, Optional, Union
import os
import logging
from dataclasses import dataclass, field

from ....src.config import (
    graph_structure_path,
    request_cache_path,
    final_prompt_path,
    user_input,
    section_processing_type,
    extraction_type,
    is_async,
)
from ....src.utils.id_operation import graph_structure,deduplicate_relation, realloc_id
from ....src.model import Entity, Relation, Chunk, Section
from ....src.model.graph_structure import GraphStructureType
from ....src.utils import save_json, jsonalize, communicate_with_agent

@dataclass
class ExtractionPaths:
    """文件路径配置类"""
    nodes_file: str
    relations_file: str
    entity_file: str
    relation_file: str
    prompt_file: Optional[str] = None
    prompt_file_1: Optional[str] = None
    prompt_file_2: Optional[str] = None

@dataclass
class ExtractionResult:
    """实体抽取结果类"""
    entities: List[Entity] = field(default_factory=list)
    relations: List[Relation] = field(default_factory=list)
    current_id: int = 0
    current_relation_id: int = 0
def count_common_characters(str1, str2):
    # 将两个字符串转换为集合，求交集
    common_chars = set(str1) & set(str2)
    return len(common_chars)
def find_closest(set,str):
    max=0.0
    result=""
    for s in set:
        count=count_common_characters(s,str)
        if max<min(count/len(s),count/len(str)):
            max=min(count/len(s),count/len(str))
            result=s
    if max<0.6:
        return ""
    else:
        return result
def get_extraction_paths() -> ExtractionPaths:
    """获取所需的文件路径配置"""
    cache_folder = graph_structure_path
    prompt_folder = os.path.join(os.getcwd(), final_prompt_path)
    
    # 确定节点和关系文件
    file_prefix = "chunk" if section_processing_type == "split_into_chunks" else "section"
    nodes_file = os.path.join(cache_folder, f"{file_prefix}_nodes.json")
    relations_file = os.path.join(cache_folder, f"{file_prefix}_edges.json")
    
    # 实体和关系输出文件
    entity_file = os.path.join(cache_folder, "entity_nodes.json")
    relation_file = os.path.join(cache_folder, "entity_related.json")
    
    # 确定提示文件
    extraction_source = "raw" if extraction_type == "entity->relation" else "report"
    if is_async:
        prompt_file_1 = os.path.join(prompt_folder, f"async_extraction_from_{extraction_source}_1.txt")
        prompt_file_2 = os.path.join(prompt_folder, f"async_extraction_from_{extraction_source}_2.txt")
        return ExtractionPaths(nodes_file, relations_file, entity_file, relation_file,
                             prompt_file_1=prompt_file_1, prompt_file_2=prompt_file_2)
    else:
        prompt_file = os.path.join(prompt_folder, f"sync_extraction_from_{extraction_source}.txt")
        return ExtractionPaths(nodes_file, relations_file, entity_file, relation_file,
                             prompt_file=prompt_file)

def load_prompts(paths: ExtractionPaths) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """加载提示文件内容"""
    logging.info("Loading prompt files.")
    try:
        if is_async:
            with open(paths.prompt_file_1, "r", encoding="utf-8") as f1, \
                 open(paths.prompt_file_2, "r", encoding="utf-8") as f2:
                return None, f1.read(), f2.read()
        else:
            with open(paths.prompt_file, "r", encoding="utf-8") as f:
                return f.read(), None, None
    except FileNotFoundError as e:
        logging.error(f"Failed to load prompt file: {e}")
        raise

def prepare_input_data() -> Tuple[List[Union[Section]], List[str], int, int]:
    """准备输入数据"""
    logging.info("Preparing input data.")
    try:
        nodes_data = graph_structure([GraphStructureType.section_node], return_type="dict")[0]
        relations_data = graph_structure([GraphStructureType.section_all_relation], return_type="dict")[0]
        
        # 初始化ID计数器
        id_counter = max([node["id"] for node in nodes_data], default=0) + 1
        relation_id_counter = max([relation["id"] for relation in relations_data], default=0) + 1
        
        # 准备数据对象和输入内容
        if section_processing_type == "split_into_chunks":
            chunks = [Chunk(**node) for node in nodes_data]
            contents_input = [user_input.replace("{text}", chunk.raw_content) for chunk in chunks]
        else:
            chunks = [Section(**node) for node in nodes_data if node["is_elemental"] == True]
            examples=[]
            for c in chunks:
                if c.example==[]:
                    examples.append("")
                extra="章节的相关信息和例子：\n"
                for e in c.example:
                    try:
                        extra+=f"\n{e['title']}\n{e['content']}\n"
                    except Exception as e:
                        logging.error(f"Failed to process example: {e}")
                examples.append(extra)
            contents_input = [user_input.replace("{text}", section.summary+extra) for section,extra in zip(chunks,examples)]
        return chunks, contents_input, id_counter, relation_id_counter
    except Exception as e:
        logging.error(f"Failed to prepare input data: {e}")
        raise

def extract_entities_and_relations(
    response_json: dict,
    current_id: int,
    current_relation_id: int
) -> ExtractionResult:
    """从响应JSON中提取实体和关系"""
    logging.info("Extracting entities and relations from response.")
    result = ExtractionResult(current_id=current_id, current_relation_id=current_relation_id)
    if response_json == None:
        return None
    entities = response_json.get("entities", [])
    relations = response_json.get("relations", [])
    name_to_id = {}

    # 处理实体
    for ent in entities:
        try:
            entity = Entity(
                id=result.current_id,
                title=ent["name"],
                type=ent["type"],
                alias=ent.get("alias", []),
                descriptions=[ent.get("raw_content", "")],
            )
            name_to_id[ent["name"]] = result.current_id
            for alias in entity.alias:
                name_to_id[alias] = result.current_id
            result.entities.append(entity)
            result.current_id += 1
        except Exception as e:
            logging.error(f"Failed to process entity: {e}")
            continue
    for rel in relations:
        if rel["source"] not in name_to_id.keys():
            entity=Entity(
                id=result.current_id,
                title=rel["source"],
                type="entity",
                alias=[],
                descriptions=[rel["source"]]
            )
            result.entities.append(entity)
            name_to_id[rel["source"]]=result.current_id
            result.current_id+=1
        if rel["target"] not in name_to_id.keys():
            entity=Entity(
                id=result.current_id,
                title=rel["target"],
                type="entity",
                alias=[],
                descriptions=[rel["target"]]
            )
            result.entities.append(entity)
            name_to_id[rel["target"]]=result.current_id
            result.current_id+=1
    # name_set=set(name_to_id.keys())
    # 处理关系
    for rel in relations:
        source_name = rel["source"]
        target_name = rel["target"]
        if isinstance(source_name, list):
            source_name = source_name[0]
        if isinstance(target_name, list):
            target_name = target_name[0]
        
        # print(target_name,source_name)
        source_id = name_to_id.get(source_name)
        target_id = name_to_id.get(target_name)
        if source_id is None:
            continue
        if target_id is None:
            continue
        relation = Relation(
            id=result.current_relation_id,
            type=rel["type"],
            descriptions=[rel.get("raw_content", "")],
            source_id=source_id,
            target_id=target_id,
            is_tree=False
        )
        result.relations.append(relation)
        result.current_relation_id += 1
        # 更新实体的关系列表
        for entity in result.entities:
            if entity.id == source_id:
                entity.to_relation.append(relation.id)
            if entity.id == target_id:
                entity.from_relation.append(relation.id)
        print(len(result.relations),len(result.entities),"实体和关系数量")
        
    return result

def process_extraction(
    contents_input: List[str],
    sync_system_prompt: Optional[str] = None,
    async_system_prompt_1: Optional[str] = None,
    async_system_prompt_2: Optional[str] = None
) -> List[Dict]:
    """处理实体抽取"""
    logging.info("Processing extraction with agent.")
    try:
        if is_async:
            # 第一步：抽取实体
            step_1_output = communicate_with_agent(
                system_prompt=async_system_prompt_1,
                user_input=contents_input,
                need_json=True,
                cached_file_path=os.path.join(request_cache_path,"step_1_output.json"),
                need_read_from_cache=True
            )
            # 第二步：抽取关系
            step_2_input = [
                f"关系来源的原文:\n{contents_input[i]}\n以下是用户提供的实体:\n{step_1_output[i]}"
                for i in range(len(step_1_output))
            ]
            
            response_data = communicate_with_agent(
                system_prompt=async_system_prompt_2,
                user_input=step_2_input,
                need_json=True,
                cached_file_path=request_cache_path + "/step_2_output.json",
                need_read_from_cache=True
            )
            
            # 合并实体数据
            
            for i, resp in enumerate(response_data):
                if resp is None:
                    resp = {}
                try:
                    resp["entities"] = jsonalize(step_1_output[i])["entities"]
                except Exception as e:
                    logging.error(f"error data: {step_1_output[i]}")
                    resp["entities"]=[]
            
            return response_data
        else:
            return communicate_with_agent(
                system_prompt=sync_system_prompt,
                user_input=contents_input,
                need_json=True,
                cached_file_path=os.path.join(request_cache_path,"step_2_output.json"),
                need_read_from_cache=True
            )
    except Exception as e:
        logging.error(f"Failed to process extraction: {e}")
        raise

def process_chunk_data(
    section_or_chunks: List[Union[Chunk, Section]],
    response_data: List[Dict],
    id_counter: int,
    relation_id_counter: int
) -> Tuple[List[Entity], List[Relation]]:
    """处理分块数据并生成实体和关系"""
    logging.info("Processing chunk data.")
    entity_nodes = []
    relation_edges = []
    
    for i, data in enumerate(response_data):
        # 提取实体和关系
        extraction_result = extract_entities_and_relations(
            data, id_counter, relation_id_counter
        )
        if extraction_result is None:
            logging.warning(f"No entities or relations found in response {i}.")
            continue
        # 更新计数器
        id_counter = extraction_result.current_id
        relation_id_counter = extraction_result.current_relation_id
        
        # 处理实体和关系
        for entity in extraction_result.entities:
            entity_nodes.append(entity)
            # 创建has_entity关系
            has_entity_relation = Relation(
                id=relation_id_counter,
                summary="",
                descriptions=[],
                type="has_entity",
                source_id=section_or_chunks[i].id,
                target_id=entity.id,
                is_tree=True
            )
            relation_id_counter += 1
            section_or_chunks[i].to_relation.append(has_entity_relation.id)
            extraction_result.relations.append(has_entity_relation)
            entity.from_relation.append(has_entity_relation.id)
        relation_edges.extend(extraction_result.relations)
        
        
    return entity_nodes, relation_edges

def entity_extraction():
    """实体抽取主函数"""
    logging.info("Starting entity extraction process.")
    try:
        # 获取路径配置
        paths = get_extraction_paths()
        
        # 加载提示文件
        sync_system_prompt, async_system_prompt_1, async_system_prompt_2 = load_prompts(paths)
        
        # 准备输入数据
        section_or_chunks, contents_input, id_counter, relation_id_counter = prepare_input_data(
        )
        
        # 执行实体抽取
        response_data = process_extraction(
            contents_input, sync_system_prompt, async_system_prompt_1, async_system_prompt_2
        )
        
        # 处理结果数据
        entity_nodes, relation_edges = process_chunk_data(
            section_or_chunks, response_data, id_counter, relation_id_counter
        )
        
        # 保存结果
        save_json(paths.entity_file, entity_nodes)
        related_edges=[relation for relation in relation_edges if relation.type!="has_entity"]
        has_entity_edges=[relation for relation in relation_edges if relation.type=="has_entity"]
        save_json(os.path.join(graph_structure_path,'entity_related.json'), related_edges)
        save_json(os.path.join(graph_structure_path,'has_entity.json'), has_entity_edges)
        logging.info("Entity extraction and relation update completed successfully.")
        realloc_id()
        deduplicate_relation()
        
    except Exception as e:
        logging.error(f"Entity extraction failed: {e}")
        raise
