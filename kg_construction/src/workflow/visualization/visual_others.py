import os
import logging
import asyncio
import json
from dataclasses import dataclass
from typing import List, Dict
from collections import defaultdict

from neo4j import AsyncGraphDatabase, basic_auth
from src.config import NEO4j_PASSWORD, NEO4j_URI, NEO4j_USER

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
class Node:
    """节点类"""

    id: int
    name: str
    description: str


@dataclass
class Relation:
    """关系类"""

    source_id: int
    target_id: int
    description: str = ""


@dataclass
class Neo4jQuery:
    """Neo4j查询封装类"""

    query: str
    batch: List[Dict]


class DataLoader:
    """数据加载和预处理类"""

    def __init__(self, cache_folder: str):
        self.cache_folder = cache_folder

    def _load_file(self, filename: str) -> List:
        """加载JSON文件"""
        file_path = os.path.join(self.cache_folder, filename)
        if not os.path.exists(file_path):
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _calculate_node_degrees(self, edges: List[Dict]) -> Dict[int, int]:
        """计算节点度数"""
        node_degrees = defaultdict(int)
        for edge in edges:
            node_degrees[edge["source_id"]] += 1
            node_degrees[edge["target_id"]] += 1
        return dict(node_degrees)

    def load_data(self) -> DataBundle:
        """加载并处理所有数据"""
        # 加载节点数据
        nodes_data = self._load_file("nodes.json")
        nodes = [
            Node(id=idx, name=node["title"], description=node.get("description", ""))
            for idx, node in enumerate(nodes_data)
        ]

        # 加载边数据
        edges_data = self._load_file("relations.json")
        relations = [
            Relation(
                source_id=edge["source_id"],
                target_id=edge["target_id"],
                description=edge.get("description", ""),
            )
            for edge in edges_data
        ]

        # 计算节点度数
        node_degrees = self._calculate_node_degrees(edges_data)

        return DataBundle(nodes=nodes, relations=relations, node_degrees=node_degrees)


class Neo4jManager:
    """Neo4j数据库管理类"""

    def __init__(self, uri: str, user: str, password: str, batch_size: int = 1000):
        self.driver = AsyncGraphDatabase.driver(uri, auth=basic_auth(user, password))
        self.batch_size = batch_size

    @staticmethod
    def clean_properties(properties: Dict) -> Dict:
        """清理属性"""
        cleaned = {}
        for key, value in properties.items():
            if isinstance(value, (dict, list)):
                cleaned[key] = json.dumps(value, ensure_ascii=False)
            else:
                cleaned[key] = (
                    str(value) if not isinstance(value, (str, int, float)) else value
                )
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

    def __init__(self, batch_size: int):
        self.batch_size = batch_size

    def create_node_queries(self, nodes: List[Node]) -> List[Neo4jQuery]:
        """创建节点查询"""
        queries = []
        for i in range(0, len(nodes), self.batch_size):
            batch = [
                Neo4jManager.clean_properties(
                    {"id": node.id, "name": node.name, "description": node.description}
                )
                for node in nodes[i : i + self.batch_size]
            ]
            queries.append(
                Neo4jQuery(
                    query="UNWIND $batch AS props CREATE (n:Entity) SET n = props",
                    batch=batch,
                )
            )
        return queries


class RelationProcessor:
    """关系处理类"""

    def __init__(self, batch_size: int):
        self.batch_size = batch_size

    def create_relation_queries(self, relations: List[Relation]) -> List[Neo4jQuery]:
        """创建关系查询"""
        queries = []
        for i in range(0, len(relations), self.batch_size):
            batch = [
                Neo4jManager.clean_properties(
                    {
                        "source_id": rel.source_id,
                        "target_id": rel.target_id,
                        "description": rel.description,
                    }
                )
                for rel in relations[i : i + self.batch_size]
            ]
            queries.append(
                Neo4jQuery(
                    query="""UNWIND $batch AS rel
                MATCH (a:Entity) WHERE a.id = rel.source_id
                MATCH (b:Entity) WHERE b.id = rel.target_id
                CREATE (a)-[r:RELATION]->(b)
                SET r += rel""",
                    batch=batch,
                )
            )
        return queries


async def visualize_native_graph(cache_folder: str):
    """主可视化函数"""
    logger.info("Starting native graph visualization process.")

    try:
        # 初始化组件
        data_loader = DataLoader(cache_folder)
        neo4j_manager = Neo4jManager(
            NEO4j_URI, NEO4j_USER, NEO4j_PASSWORD, batch_size=5000
        )

        # 加载数据
        data_bundle = data_loader.load_data()

        # 初始化处理器
        node_processor = NodeProcessor(5000)
        relation_processor = RelationProcessor(5000)

        # 清空数据库
        await neo4j_manager.clear_database()

        # 创建节点
        logger.info("Creating nodes...")
        node_queries = node_processor.create_node_queries(data_bundle.nodes)
        for query in node_queries:
            await neo4j_manager.execute_query(query)

        # 创建索引加速关系创建
        async with neo4j_manager.driver.session() as session:
            try:
                await session.run("CREATE INDEX FOR (n:Entity) ON (n.id)")
            except Exception as e:
                pass

        # 创建关系
        logger.info("Creating relationships...")
        relation_queries = relation_processor.create_relation_queries(
            data_bundle.relations
        )
        for query in relation_queries:
            await neo4j_manager.execute_query(query)

        logger.info("Native graph visualization completed successfully!")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise
    finally:
        await neo4j_manager.close()


if __name__ == "__main__":
    asyncio.run(visualize_native_graph("./camera_ready"))
