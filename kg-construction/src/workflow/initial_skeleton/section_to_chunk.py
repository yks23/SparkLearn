import os
from src.model.section import Section
from src.model.relation import Relation
from src.model.chunk import Chunk
from transformers import GPT2Tokenizer
from src.utils import load_json,save_json
from src.config import chunk_length,max_level,graph_structure_path

def chunk_nodes(nodes: list, chunk_length: int, id_start: int, e_id_start: int):
    """将节点内容切分成指定长度的块"""
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    chunked_nodes = []
    edges = []
    id_counter = id_start
    e_id_counter = e_id_start

    for node in nodes:
        raw_content = node.raw_content
        tokens = tokenizer.encode(raw_content, add_special_tokens=False)
        num_chunks = (len(tokens) + chunk_length - 1) // chunk_length

        for i in range(num_chunks):
            start_idx = i * chunk_length
            end_idx = min((i + 1) * chunk_length, len(tokens))
            chunk_tokens = tokens[start_idx:end_idx]
            chunk_text = tokenizer.decode(chunk_tokens)

            rel = Relation(id=e_id_counter, summary="", descriptions=[], type="has_chunk", source_id=node.id, target_id=id_counter)
            chunk_node = Chunk(id=id_counter, raw_content=chunk_text)
            chunk_node.from_relation.append(rel.id)
            node.to_relation.append(rel.id)
            chunked_nodes.append(chunk_node)
            edges.append(rel)

            id_counter += 1
            e_id_counter += 1

    return chunked_nodes, edges, id_counter, e_id_counter

def section_to_chunk():
    """主函数：处理文档并生成切分节点和关系"""
    cache_folder = graph_structure_path
    nodes_file = os.path.join(cache_folder, "section_nodes.json")
    relations_file = os.path.join(cache_folder, "section_edges.json")

    nodes_data, relations_data = load_json(nodes_file),load_json(relations_file)
    
    id_start = len(nodes_data)
    e_id_start = len(relations_data)

    nodes = [Section(**node) for node in nodes_data if node['level'] ==max_level]
    chunked_nodes, edges, _,_ = chunk_nodes(nodes, chunk_length, id_start, e_id_start)

    node_file_path = os.path.join(cache_folder, "chunk_nodes.json")
    edge_file_path = os.path.join(cache_folder, "chunk_edges.json")
    save_json(node_file_path,chunked_nodes)
    save_json(edge_file_path,edges)