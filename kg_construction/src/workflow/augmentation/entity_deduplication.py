"""
实体去重模块
用于合并和去重实体及其关系
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
import logging
from collections import defaultdict
import os

from ....src.model.graph_structure import GraphStructureType
from ....src.model.entity import Entity
from ....src.model.relation import Relation
from ....src.model.section import Section
from ....src.utils import save_json,execute_operator
from ....src.config import graph_structure_path
from ....src.model.base_operator import CheckMergeoperation
# from kg4edu.exceptions import DeduplicationError
from ....src.utils.id_operation import graph_structure, realloc_id,save_relation
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class UnionFind:
    """并查集数据结构，用于实体合并"""
    parent: Dict[int, int] = field(default_factory=dict)
    rank: Dict[int, int] = field(default_factory=dict)

    def __init__(self, elements: List[int]):
        """初始化并查集
        
        Args:
            elements: 需要管理的元素ID列表
        """
        self.parent = {element: element for element in elements}
        self.rank = {element: 1 for element in elements}

    def find(self, u: int) -> Optional[int]:
        """查找元素的根节点，使用路径压缩
        
        Args:
            u: 要查找的元素ID
            
        Returns:
            元素的根节点ID，如果元素不存在则返回None
        """
        if u not in self.parent:
            return None
        if self.parent[u] != u:
            self.parent[u] = self.find(self.parent[u])
        return self.parent[u]

    def union(self, u: int, v: int) -> None:
        """合并两个元素所在的集合，使用按秩合并
        
        Args:
            u: 第一个元素ID
            v: 第二个元素ID
        """
        root_u = self.find(u)
        root_v = self.find(v)
        
        if any(root is None for root in [root_u, root_v]) or root_u == root_v:
            return
            
        if self.rank[root_u] > self.rank[root_v]:
            self.parent[root_v] = root_u
        elif self.rank[root_u] < self.rank[root_v]:
            self.parent[root_u] = root_v
        else:
            self.parent[root_v] = root_u
            self.rank[root_u] += 1
    def getset(self)->List[Set[int]]:
        """获取并查集中的所有集合"""
        allequals=set()
        equals=[]
        # 等价类
        for i in self.parent.keys():
            allequals.add(self.find(i))
        for i in allequals:
            # 对于每个等价类
            temp=set()
            for j in self.parent.keys():
                if self.find(j)==i:
                    temp.add(j)
            
            equals.append(temp)
        return equals
def get_merge_operation_result(result:list[int],new_entity_index:int,entity_nodes:List[Entity])->Entity:
    """从list[int]中获取合并的实体"""
    merged_entity=None
    for ent in entity_nodes:
        if ent.id==result[0]:
            merged_entity=Entity(id=new_entity_index,title=ent.title,alias=ent.alias,descriptions=ent.descriptions,from_relation=ent.from_relation,to_relation=ent.to_relation)
            break
    for id in result[1:]:
        merged_entity.alias.extend(entity_nodes[id].alias)
        merged_entity.descriptions.extend(entity_nodes[id].descriptions)
        merged_entity.from_relation.extend(entity_nodes[id].from_relation)
        merged_entity.to_relation.extend(entity_nodes[id].to_relation)
    return merged_entity
@dataclass
class EntityMerger:
    """实体合并器类"""
    entity_nodes: List[Entity]
    relation_edges: List[Relation]
    name_to_ids: Dict[str, List[int]] = field(default_factory=lambda: defaultdict(list))
    uf: Optional[UnionFind] = None
    root_to_entity: Dict[int, Entity] = field(default_factory=dict)
    entity_id_map: Dict[int, int] = field(default_factory=dict)
    merge_type:str="no-agent"
    
    def __post_init__(self):
        """初始化名称到ID的映射和并查集"""
        self._build_name_mapping()
        self.uf = UnionFind([entity.id for entity in self.entity_nodes])
        
    def _build_name_mapping(self) -> None:
        """构建实体名称到ID的映射"""
        for entity in self.entity_nodes:
            all_names = set(list(entity.alias) + [entity.title])
            for name in all_names:
                self.name_to_ids[name].append(entity.id)
                
    def _merge_entity_properties(self, merged_entity: Entity, entity: Entity) -> None:
        """合并实体属性
        
        Args:
            merged_entity: 合并后的目标实体
            entity: 要合并的源实体
        """
        if isinstance(merged_entity.alias,dict):
            merged_entity.alias=list(merged_entity.alias.keys())
        if isinstance(entity.alias,dict):
            entity.alias=list(entity.alias.keys())
        if entity.title not in merged_entity.title:
            merged_entity.alias.append(entity.title)
            
        merged_entity.alias.extend(
            alias for alias in entity.alias 
            if alias not in merged_entity.alias
        )
        merged_entity.descriptions.extend(entity.descriptions)
        merged_entity.from_relation.extend(entity.from_relation)
        merged_entity.to_relation.extend(entity.to_relation)
        
    def merge_entities(self) -> Tuple[List[Entity], List[Relation]]:
        """执行实体合并
        
        Returns:
            Tuple[List[Entity], List[Relation]]: 合并后的实体列表和关系列表
        """
        logger.info("Starting entity merging process")
        
        # 合并具有相同名称的实体
        for ids in self.name_to_ids.values():
            for other_id in ids[1:]:
                self.uf.union(ids[0], other_id)
        
        # 创建新的实体
        
        new_entity_index = self.entity_nodes[0].id
        if self.merge_type=="with-agent":
            equals=self.uf.getset()
            ops=[]
            merged_entities=[]
            for equal in equals:
                entities=[]
                for id in equal:
                    entities.append(self.entity_nodes[id])
                check_merge=CheckMergeoperation(system_prompt_path="kg4edu/prompt/check_merge.txt",entities=entities)
                ops.append(check_merge)
            results=execute_operator(ops)
            for result in results:
                for res in result:
                    merged_entity=get_merge_operation_result(res,new_entity_index)
                    merged_entities.append(merged_entity)
                    for id in res:
                        self.entity_id_map[id]=new_entity_index
                    new_entity_index+=1
            merged_relations=self._process_relations()
            logger.info(f"Merged {len(self.entity_nodes)} entities into {len(merged_entities)} entities")
            logger.info("Entity merging process completed successfully")
            return merged_entities,merged_relations
        for entity in self.entity_nodes:
            root = self.uf.find(entity.id)
            if root is None:
                continue
                
            if root not in self.root_to_entity:
                # 创建新实体
                merged_entity = Entity(
                    id=new_entity_index,
                    title=entity.title,
                    alias=entity.alias.copy(),
                    descriptions=entity.descriptions.copy(),
                    from_relation=entity.from_relation.copy(),
                    to_relation=entity.to_relation.copy(),
                )
                self.root_to_entity[root] = merged_entity
                self.entity_id_map[root] = new_entity_index
                new_entity_index += 1
            else:
                # 合并到现有实体
                self._merge_entity_properties(self.root_to_entity[root], entity)
            self.entity_id_map[entity.id] = self.entity_id_map[root]
        
        # 处理关系
        merged_relations = self._process_relations()
        logger.info(f"Merged {len(self.entity_nodes)} entities into {len(self.root_to_entity)} entities")
        return list(self.root_to_entity.values()), merged_relations
    
    def _process_relations(self) -> List[Relation]:
        """处理并更新关系
        Returns:
            List[Relation]: 更新后的关系列表    
        """
        merged_relations = []
        for relation in self.relation_edges:
            relation.source_id = self.entity_id_map.get(relation.source_id, relation.source_id)
            relation.target_id = self.entity_id_map.get(relation.target_id, relation.target_id)
            merged_relations.append(relation)
        return merged_relations

class EntityDeduplicator:
    """实体去重器类"""
    
    def __init__(self,merge_type:str="no-agent"):
        """初始化文件路径"""
        self.merge_type=merge_type
    def load_data(self) -> Tuple[List[Entity], List[Relation], List[Section]]:
        """加载实体和关系数据"""
        try:
            entity_nodes = graph_structure([GraphStructureType.entity_node], return_type="object")[0]
            relation_edges = graph_structure([GraphStructureType.all_relation], return_type="object")[0]
            sections_nodes = graph_structure([GraphStructureType.section_node], return_type="object")[0]
            return entity_nodes, relation_edges, sections_nodes
        except Exception as e:
            raise Exception(f"Failed to load data: {e}")
            
    def deduplicate_and_remap(self) -> None:
        """执行实体去重和重新映射流程"""
        try:
            logger.info("Starting entity deduplication and remapping process")
            
            # 加载数据
            entity_nodes, relation_edges, sections_nodes = self.load_data()
            
            # 获取最小ID
            # min_relation_id = min(relation.id for relation in relation_edges)
            
            # 创建合并器并执行合并
            merger = EntityMerger(entity_nodes, relation_edges,merge_type=self.merge_type)
            merged_entity_nodes, merged_relation_edges = merger.merge_entities()
            save_relation(merged_relation_edges, set(node.id for node in merged_entity_nodes))
            save_json(os.path.join(graph_structure_path, "entity_nodes.json"), merged_entity_nodes)
            save_json(os.path.join(graph_structure_path, "section_nodes.json"), sections_nodes)
            realloc_id()
            logger.info("Entity deduplication and remapping completed successfully")
            logger.info("实体去重和重新映射完成。")
            
        except Exception as e:
            logger.error(f"Entity deduplication and remapping failed: {e}")
            print(f"实体去重和重新映射失败：{e}")
            raise

def entity_deduplication(merge_type:str="no-agent"):
    """实体去重入口函数"""
    entity_deduplicator = EntityDeduplicator(merge_type=merge_type)
    try:
        entity_deduplicator.deduplicate_and_remap()
        realloc_id()
    except Exception as e:
        logger.error(f"Entity deduplication and remapping failed: {e}")
        print(f"实体去重和重新映射失败：{e}")
        raise
    
    
if __name__ == "__main__":
    entity_deduplication()

