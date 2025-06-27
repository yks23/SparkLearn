import os
import logging
import asyncio
import json
from dataclasses import dataclass
from typing import List, Dict, Tuple

from src.model import Entity, Section, Relation, Chunk, Example
from src.model.graph_structure import GraphStructureType
from src.utils import load_json
from src.utils.id_operation import graph_structure
from src.config import (
    request_cache_path,
    max_level,
    NEO4j_URI,
    NEO4j_USER,
    NEO4j_PASSWORD,
    section_processing_type,
)
from neo4j import AsyncGraphDatabase, basic_auth

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DataBundle:
    """数据包装类"""

    nodes: List
    relations: List
    node_degrees: Dict[int, int]


@dataclass
class Neo4jQuery:
    """Neo4j查询封装类"""

    query: str
    batch: List[Dict]


class DataLoader:
    """数据加载和预处理类"""

    def __init__(self, cache_folder: str):
        self.cache_folder = cache_folder

    def _load_file(self, filename: str) -> Dict:
        """加载单个JSON文件"""
        file_path = os.path.join(self.cache_folder, filename)
        return load_json(file_path)

    def _process_examples(self, nodes: List, edges_data: List) -> Tuple[List, List]:
        """处理示例数据"""
        node_id = max(node.id for node in nodes)
        edges_id = max(edge["id"] for edge in edges_data)
        example_nodes = []
        example_edges = []

        for node in nodes:
            if isinstance(node, Section) and node.level == max_level:
                for example in node.example:
                    example_nodes.append(
                        Example(
                            id=node_id,
                            title=example["title"],
                            content=example["content"],
                        )
                    )
                    example_edges.append(
                        Relation(
                            id=edges_id,
                            source_id=node.id,
                            target_id=node_id,
                            type="has_example",
                        )
                    )
                    node_id += 1
                    edges_id += 1

        return example_nodes, example_edges

    def _calculate_node_degrees(self, edges_data: List) -> Dict[int, int]:
        """计算节点度数"""
        node_degrees = {}
        for rel in edges_data:
            for node_id in (rel["source_id"], rel["target_id"]):
                node_degrees[node_id] = node_degrees.get(node_id, 0) + 1
        return node_degrees

    def load_data(self) -> DataBundle:
        """加载并处理所有数据"""
        # 加载基础数据
        [entity_edges_data] = graph_structure(
            [GraphStructureType.all_relation], return_type="dict"
        )

        # 创建基础节点和关系
        nodes = graph_structure([GraphStructureType.all_node], return_type="object")[0]
        relations = graph_structure(
            [GraphStructureType.all_relation], return_type="object"
        )[0]
        # 处理chunks或examples
        if section_processing_type == "split_into_chunks":
            chunk_node_data = self._load_file("chunk_nodes.json")
            chunk_edge_data = self._load_file("chunk_edges.json")
            nodes += [Chunk(**node) for node in chunk_node_data]
            relations += [Relation(**edge) for edge in chunk_edge_data]
        else:
            example_nodes, example_edges = self._process_examples(
                nodes, entity_edges_data
            )
            nodes += example_nodes
            relations += example_edges

        # 计算节点度数
        node_degrees = self._calculate_node_degrees(entity_edges_data)

        return DataBundle(nodes=nodes, relations=relations, node_degrees=node_degrees)


class Neo4jManager:
    """Neo4j数据库管理类"""

    def __init__(self, uri: str, user: str, password: str, batch_size: int = 100):
        self.driver = AsyncGraphDatabase.driver(uri, auth=basic_auth(user, password))
        self.batch_size = batch_size

    @staticmethod
    def clean_properties(properties: Dict) -> Dict:
        """清理属性"""
        cleaned = {}
        for key, value in properties.items():
            if isinstance(value, dict):
                cleaned[key] = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, list):
                cleaned_list = []
                for item in value:
                    if isinstance(item, dict):
                        cleaned_list.append(json.dumps(item, ensure_ascii=False))
                    else:
                        cleaned_list.append(item)
                cleaned[key] = cleaned_list
            else:
                cleaned[key] = value
        return cleaned

    async def clear_database(self):
        """清空数据库"""
        async with self.driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")

    async def execute_query(self, query: Neo4jQuery):
        """执行Neo4j查询"""
        async with self.driver.session() as session:
            await session.run(query.query, batch=query.batch)

    async def close(self):
        """关闭连接"""
        await self.driver.close()


class NodeProcessor:
    """节点处理类"""

    def __init__(self, batch_size: int, node_degrees: Dict[int, int]):
        self.batch_size = batch_size
        self.node_degrees = node_degrees
        self._calculate_degree_thresholds()

    def _calculate_degree_thresholds(self):
        """计算度数阈值"""
        degree_list = sorted(self.node_degrees.values())
        if degree_list:
            self.percent_10_du = degree_list[int(len(degree_list) * 0.9)]
            self.percent_30_du = degree_list[int(len(degree_list) * 0.7)]
        else:
            self.percent_10_du = self.percent_30_du = 0

    def _classify_entities(self, entities: List[Dict]) -> Dict[str, List[Dict]]:
        """将实体分类"""
        classified = {"level1": [], "level2": [], "level3": []}

        for entity in entities:
            degree = self.node_degrees.get(entity["id"], 0)
            if degree > self.percent_10_du:
                classified["level1"].append(entity)
            elif degree > self.percent_30_du:
                classified["level2"].append(entity)
            else:
                classified["level3"].append(entity)

        return classified

    def create_node_queries(self, nodes: List) -> List[Neo4jQuery]:
        """创建节点查询"""
        queries = []
        for i in range(0, len(nodes), self.batch_size):
            batch = nodes[i : i + self.batch_size]

            # 分类节点
            entities = [
                Neo4jManager.clean_properties(node.to_dict())
                for node in batch
                if isinstance(node, Entity)
            ]
            sections = [
                Neo4jManager.clean_properties(node.to_dict())
                for node in batch
                if isinstance(node, Section)
            ]
            chunks = [
                Neo4jManager.clean_properties(node.to_dict())
                for node in batch
                if isinstance(node, Chunk)
            ]
            examples = [
                Neo4jManager.clean_properties(node.to_dict())
                for node in batch
                if isinstance(node, Example)
            ]

            # 处理实体节点
            if entities:
                classified = self._classify_entities(entities)
                for level, nodes in classified.items():
                    if nodes:
                        queries.append(
                            Neo4jQuery(
                                query=f"UNWIND $batch AS props CREATE (e:{level.capitalize()}Entity) SET e = props",
                                batch=nodes,
                            )
                        )

            # 处理其他类型节点
            node_types = [
                ("Section", sections),
                ("Chunk", chunks),
                ("Example", examples),
            ]

            for node_type, node_list in node_types:
                if node_list:
                    queries.append(
                        Neo4jQuery(
                            query=f"UNWIND $batch AS props CREATE (n:{node_type}) SET n = props",
                            batch=node_list,
                        )
                    )

        return queries


class RelationProcessor:
    """关系处理类"""

    def __init__(self, batch_size: int):
        self.batch_size = batch_size
        self.relation_types = {
            "has_subsection": "HAS_SUBSECTION",
            "has_entity": "HAS_ENTITY",
            "has_chunk": "HAS_CHUNK",
            "has_example": "HAS_EXAMPLE",
            "related": "RELATED",
        }

    def _classify_relations(self, relations: List[Dict]) -> Dict[str, List[Dict]]:
        """将关系分类"""
        classified = {rel_type: [] for rel_type in self.relation_types.keys()}

        for rel in relations:
            if rel["type"] in self.relation_types:
                classified[rel["type"]].append(rel)
            else:
                classified["related"].append(rel)

        return classified

    def create_relation_queries(self, relations: List[Relation]) -> List[Neo4jQuery]:
        """创建关系查询"""
        queries = []
        for i in range(0, len(relations), self.batch_size):
            batch = [
                Neo4jManager.clean_properties(rel.to_dict())
                for rel in relations[i : i + self.batch_size]
            ]
            classified = self._classify_relations(batch)

            for rel_type, rel_list in classified.items():
                if rel_list:
                    neo4j_type = self.relation_types[rel_type]
                    query = f"""
                    UNWIND $batch AS rel
                    MATCH (a {{id: rel.source_id}})
                    MATCH (b {{id: rel.target_id}})
                    CREATE (a)-[r:{neo4j_type}]->(b)
                    SET r += rel
                    """
                    queries.append(Neo4jQuery(query=query, batch=rel_list))

        return queries


async def visualization():
    """主可视化函数"""
    logger.info("Starting visualization process.")

    try:
        # 初始化组件
        cache_folder = os.path.join(os.getcwd(), request_cache_path)
        data_loader = DataLoader(cache_folder)
        neo4j_manager = Neo4jManager(NEO4j_URI, NEO4j_USER, NEO4j_PASSWORD)

        # 加载数据
        data_bundle = data_loader.load_data()

        # 初始化处理器
        node_processor = NodeProcessor(10000, data_bundle.node_degrees)
        relation_processor = RelationProcessor(10000)

        # 清空数据库
        await neo4j_manager.clear_database()

        # 处理并创建节点
        logger.info("Creating nodes in Neo4j.")
        node_queries = node_processor.create_node_queries(data_bundle.nodes)
        for query in node_queries:
            await neo4j_manager.execute_query(query)

        # 处理并创建关系
        logger.info("Creating relationships in Neo4j.")
        relation_queries = relation_processor.create_relation_queries(
            data_bundle.relations
        )
        for query in relation_queries:
            await neo4j_manager.execute_query(query)

        logger.info("Visualization process completed successfully.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
    finally:
        if "neo4j_manager" in locals():
            await neo4j_manager.close()


if __name__ == "__main__":
    asyncio.run(visualization())
