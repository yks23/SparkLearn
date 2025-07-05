from src.model import Entity, Section
from src.model.graph_structure import GraphStructureType
from src.utils.communication import execute_operator
from src.model.base_operator import (
    EmbeddingEntityoperation,
    Embeddingstroperation,
    EmbeddingSectionoperation,
)
import os
import re
import faiss
from src.utils.file_operation import save_json, load_json
from src.utils.id_operation import graph_structure
import numpy as np
import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

class SearchEngine:
    def __init__(self, engine, table):
        self.engine = engine
        self.table = table
        self.table = {int(k): int(v) for k, v in table.items()}
        self.reverse_table = {int(v): int(k) for k, v in table.items()}

    def search_by_id(self, entity_id: int, top_k: int = 10) -> list[int]:
        """根据实体id搜索相似top_k节点，不包括本身"""
        res = self.engine.search(
            self.get_vector_by_id(entity_id)[np.newaxis, :], top_k + 1
        )
        ids = [self.reverse_table[i] for i in res[1][0] if i!=-1][1:]
        return ids

    def search_by_vector(self, vector: list[float], top_k: int = 10) -> list[int]:
        """根据向量搜索相似top_k节点"""
        res = self.engine.search(np.array([vector], dtype=np.float32), top_k)
        ids = [self.reverse_table[i] for i in res[1][0]]
        return ids

    def search_by_vector_raw(self, vector: list[float], top_k: int = 10) -> list[int]:
        """根据向量搜索相似top_k节点"""
        res = self.engine.search(np.array([vector], dtype=np.float32), top_k)
        ids = [i for i in res[1][0]]
        return ids

    @staticmethod
    def L2_distance(
        v1: list[float] | np.ndarray, v2: list[float] | np.ndarray
    ) -> float:
        return np.linalg.norm(np.array(v1) - np.array(v2))

    def get_distance(self, entity_id1: int, entity_id2: int) -> float:
        return np.linalg.norm(
            self.get_vector_by_id(entity_id1) - self.get_vector_by_id(entity_id2)
        )

    def insert_entity(self, entity_id: int, vector: list[float]):
        """插入实体id和向量"""
        vector_np = np.array([vector], dtype=np.float32)  # FAISS 需要 float32 类型
        self.engine.add(vector_np)
        self.table[entity_id] = self.search_by_vector_raw(vector, 1)[0]

    def get_vector_by_id(self, entity_id: int):
        return self.engine.reconstruct(self.table[entity_id])

    def delete_entity(self, entity_id: int):
        """删除实体id"""
        self.engine.remove_ids([self.table[entity_id]])
        self.table.pop(entity_id)

    def change_entity(self, entity_id: int, vector: list[float]):
        """修改实体id的向量"""
        # FAISS 需要 int64 类型的 ID
        entity_index = np.array([self.table[entity_id]], dtype=np.int64)

        # 移除旧的向量
        self.engine.remove_ids(entity_index)

        # 添加新的向量（确保是 2D 数组）
        vector_np = np.array([vector], dtype=np.float32)  # FAISS 需要 float32 类型
        self.engine.add(vector_np)

        # 更新索引表，新的 ID 是 `ntotal - 1`
        self.table[entity_id] = self.search_by_vector_raw(vector, 1)[0]

    def merge_to_one(self, new_id: int, entity_ids: list[int], vector: list[float]):
        """合并多个实体id为一个实体id"""
        # 删除旧的向量
        self.engine.remove_ids(entity_ids)
        # 添加新的向量
        self.engine.add(vector)
        # 删除旧的实体id
        for entity_id in entity_ids:
            self.table.pop(entity_id)
        # 更新新的实体id
        self.table[new_id] = self.search_by_vector_raw(vector, 1)[0]

    def save_state(self, folder_path: str):
        self.table = {int(k): int(v) for k, v in self.table.items()}
        save_json(os.path.join(folder_path, "table.json"), self.table)
        faiss.write_index(self.engine, os.path.join(folder_path, "engine.ann"))


def initialize_entity_engine(
    entitis: list[Entity] = None,
    engine_path: str = None,
    table_path: str = None,
    level: int = -1,
):
    """
    用于初始化引擎。
    entitis: 传入的实体列表.
    如果engine_path和table_path都不为None，且文件存在，则直接读取文件,不用重新初始化。
    如果engine_path和table_path都不为None，但文件不存在，则重新初始化，保存到engine_path和table_path。
    level代表使用的文本描述的编号，-1代表最后一个描述。
    """
    if (
        engine_path is not None
        and table_path is not None
        and os.path.exists(engine_path)
        and os.path.exists(table_path)
    ):
        entity_engine = faiss.read_index(engine_path)
        entity_table = load_json(table_path)
        return SearchEngine(entity_engine, entity_table)
    entitis = graph_structure(
        type=[GraphStructureType.entity_node], return_type="object"
    )[0]
    all_op = []
    for i in range(0, len(entitis), 16):
        vectorization_op = EmbeddingEntityoperation(entitis[i : i + 16], level=level)
        all_op.append(vectorization_op)
    results = execute_operator(
        all_op,
        cached_file_path=engine_path.replace(".ann", ".json"),
        need_read_from_cache=True,
    )
    vector_np = np.array(results, dtype=np.float32)
    entity_engine = faiss.IndexFlatL2(2048)
    entity_engine.add(vector_np)
    entity_table = {entity.id: i for i, entity in enumerate(entitis)}
    if engine_path is not None:
        faiss.write_index(entity_engine, engine_path)
    if table_path is not None:
        save_json(table_path, entity_table)
    return SearchEngine(entity_engine, entity_table)


def initialize_with_title(
    entitis: list[Entity] = None,
    engine_path: str = None,
    table_path: str = None,
):
    if (
        engine_path is not None
        and table_path is not None
        and os.path.exists(engine_path)
        and os.path.exists(table_path)
    ):
        entity_engine = faiss.read_index(engine_path)
        entity_table = load_json(table_path)
        return SearchEngine(entity_engine, entity_table)
    if entitis is None:
        entitis = graph_structure(
            type=[GraphStructureType.entity_node], return_type="object"
        )[0]
    entity_titles = [entity.title for entity in entitis]
    
    re_expression = [r"(# 第\d+部分)", r"(## 第\d+章)", r"(## \d+\.\d+)"]
    # re_expression=[r"(## 第\d+章)", r"(### \d+\.\d+节)",r"(#### \d+\.\d+\.\d+节)"]
    
    for re_exp in re_expression:
        entity_titles = [re.sub(re_exp, "", entity) for entity in entity_titles]
    entity_titles = [entity.replace(" ","").replace("#","").replace("\n","") for entity in entity_titles]
    table=[]
    for title,ent  in zip(entity_titles,entitis):
        if title=="":
            continue
        else:
            if isinstance(ent,Entity):  
                table.append({'title':title,'description':ent.descriptions[-1]})
            else:
                table.append({'title':title,'description':ent.summary})
    save_json(table_path.replace('table.json','nodes.json'),table)
    new_id=0
    maps={}
    for ent,tit in zip(entitis,entity_titles):
        if tit!="":
            maps[ent.id]=new_id
            new_id+=1
    entity_titles=[title for title in entity_titles if title!=""]
    all_op = []
    for i in range(0, len(entitis), 64):
        vectorization_op = Embeddingstroperation(entity_titles[i : i +  64])
        all_op.append(vectorization_op)
    results = execute_operator(
        all_op,
        cached_file_path=engine_path.replace(".ann", ".json"),
        # need_read_from_cache=True,
    )
    vector_np = np.array(results, dtype=np.float32)
    entity_engine = faiss.IndexFlatL2(2048)
    entity_engine.add(vector_np)
    entity_table = {i:i for i in range(len(entitis))}
    if engine_path is not None:
        faiss.write_index(entity_engine, engine_path)
    if table_path is not None:
        save_json(table_path, entity_table)
        
    return SearchEngine(entity_engine, entity_table),maps


def initialize_section_engine(
    sections: list[Section] = None, engine_path: str = None, table_path: str = None
):
    if (
        engine_path is not None
        and table_path is not None
        and os.path.exists(engine_path)
        and os.path.exists(table_path)
    ):
        entity_engine = faiss.read_index(engine_path)
        entity_table = load_json(table_path)
        return SearchEngine(entity_engine, entity_table)
    sections = graph_structure(
        type=[GraphStructureType.section_node], return_type="object"
    )[0]
    all_op = []
    for i in range(0, len(sections), 16):
        vectorization_op = EmbeddingSectionoperation(sections[i : i + 16])
        all_op.append(vectorization_op)
    results = execute_operator(
        all_op,
        cached_file_path=engine_path.replace(".ann", ".json"),
        need_read_from_cache=True,
    )
    vector_np = np.array(results, dtype=np.float32)
    section_engine = faiss.IndexFlatL2(2048)
    section_engine.add(vector_np)
    section_table = {section.id: i for i, section in enumerate(sections)}
    if engine_path is not None:
        faiss.write_index(section_engine, engine_path)
    if table_path is not None:
        save_json(table_path, section_table)
    return SearchEngine(section_engine, section_table)


def initial_engine_with_str(entities: list[Entity], engine_path: str, table_path: str):
    if (
        engine_path is not None
        and table_path is not None
        and os.path.exists(engine_path)
        and os.path.exists(table_path)
    ):
        entity_engine = faiss.read_index(engine_path)
        entity_table = load_json(table_path)
        return SearchEngine(entity_engine, entity_table)
    all_op = []
    for i in range(0, len(entities), 16):
        vectorization_op = Embeddingstroperation(entities[i : i + 16])
        all_op.append(vectorization_op)
    print("all_op", len(all_op))    
    results = execute_operator(
        all_op,
        cached_file_path=engine_path.replace(".ann", ".json"),
        need_read_from_cache=True,
    )
    print("results",len(results))
    vector_np = np.array(results, dtype=np.float32)
    entity_engine = faiss.IndexFlatL2(2048)
    entity_engine.add(vector_np)
    entity_table = {i:i for i in range(len(entities))}
    if engine_path is not None:
        faiss.write_index(entity_engine, engine_path)
    if table_path is not None:
        save_json(table_path, entity_table)
    return SearchEngine(entity_engine, entity_table)
def initial_with_meta(meta_path:str):
    entities=load_json(meta_path)
    embeds = [ent['embedding'] for ent in entities]
    vector_np = np.array(embeds, dtype=np.float32)
    entity_engine = faiss.IndexFlatL2(2048)
    entity_engine.add(vector_np)
    entity_table = {i:i for i in range(len(entities))}
    return SearchEngine(entity_engine, entity_table)