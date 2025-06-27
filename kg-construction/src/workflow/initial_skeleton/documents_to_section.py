import os
import re
from src.model.section import Section
from src.model.relation import Relation
from src.utils import save_json
from src.config import raw_path, graph_structure_path,re_expression
# 全局计数器
id_counter = 0
e_id_counter = 0

def load_documents(folder_path: str):
    documents = []
    folder_path = os.path.join(os.getcwd(), folder_path)
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".md"):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "r", encoding='utf-8') as file:
                document = file.read()
                documents.append([document, file_name.strip(".md")])
    return documents

def section_split(section: Section, document: str, max_level: int, Node: list, Edge: list, re_expression: list[str]):
    global id_counter, e_id_counter
    sections = []
    pattern = re_expression[section.level]

    matches = re.split(pattern, document)
    title = None
    content = None

    for match in matches:
        if match.strip() == "":
            continue
        if re.match(pattern, match):
            if title is not None and content is not None:
                subsection = Section(id=id_counter, title=title, level=section.level + 1)
                id_counter += 1
                subsection.raw_content = content.strip()
                sections.append(subsection)
                Node.append(subsection)

                if subsection.level < max_level:
                    subsections = section_split(subsection, content, max_level, Node, Edge, re_expression)
                    if len(subsections)!=0:
                        for subsubsection in subsections:
                            edge = Relation(id=e_id_counter, summary="", descriptions=[], type="has_subsection", source_id=subsection.id, target_id=subsubsection.id)
                            subsection.to_relation.append(edge.id)
                            e_id_counter += 1
                            subsubsection.from_relation.append(edge.id)
                            Edge.append(edge)
                    else:
                        subsection.is_elemental=True
                else:
                    subsection.is_elemental=True

            title = match.strip()
            content = None
        else:
            content = match if content is None else content + match

    if title is not None and content is not None:
        subsection = Section(id=id_counter, title=title, level=section.level + 1)
        id_counter += 1
        subsection.raw_content = content.strip()
        sections.append(subsection)
        Node.append(subsection)

        if subsection.level < max_level:
            subsections = section_split(subsection, content, max_level, Node, Edge, re_expression)
            if len(subsections)!=0:
                for subsubsection in subsections:
                    edge = Relation(id=e_id_counter, summary="", descriptions=[], type="has_subsection", source_id=subsection.id, target_id=subsubsection.id,is_tree=True)
                    subsection.to_relation.append(edge.id)
                    e_id_counter += 1
                    subsubsection.from_relation.append(edge.id)
                    Edge.append(edge)
            else:
                subsection.is_elemental=True
        else:
            subsection.is_elemental=True
                
    return sections

def process_documents(documents, max_level, re_expression):
    global id_counter, e_id_counter
    Node = []
    Edge = []

    for document, name in documents:
        section = Section(id=id_counter, title=name, level=0)
        id_counter += 1
        Node.append(section)
        subsections = section_split(section, document, max_level, Node, Edge, re_expression)
        for subsection in subsections:
            edge = Relation(id=e_id_counter, summary="", descriptions=[], type="has_subsection", source_id=section.id, target_id=subsection.id)
            e_id_counter += 1
            section.to_relation.append(edge.id)
            subsection.from_relation.append(edge.id)
            Edge.append(edge)

    return Node, Edge

def documents_to_sections():
    global id_counter, e_id_counter
    documents = load_documents(raw_path)
    max_level = len(re_expression)
    nodes, edges = process_documents(documents, max_level, re_expression)
    node_file_path = os.path.join(graph_structure_path, "section_nodes.json")
    edge_file_path = os.path.join(graph_structure_path, "has_subsection.json")
    print(f"共有{len(nodes)}个节点，{len(edges)}条边")
    # 创建文件夹
    if not os.path.exists(graph_structure_path):
        os.makedirs(graph_structure_path)
    save_json(node_file_path,nodes)
    save_json(edge_file_path,edges)
    
