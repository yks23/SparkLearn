import os
import re
from ....src.model.section import Section
from ....src.model.relation import Relation
from ....src.utils import save_json
from ....src.config import raw_path, graph_structure_path

# 全局计数器
id_counter = 0
e_id_counter = 0


def load_documents(folder_path: str):
    documents = []
    folder_path = os.path.join(os.getcwd(), folder_path)
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".md"):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "r", encoding="utf-8") as file:
                document = file.read()
                documents.append([document, file_name.strip(".md")])
    return documents


def load_folders(folder_path: str, depth=0):
    documents = {}
    if os.path.isdir(folder_path):
        documents['is_folder'] = True
        documents['name'] = os.path.basename(folder_path)
        documents['children'] = []
        documents['depth'] = depth
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if "images_" in item_path or item_path.endswith(".png"):
                continue
            documents["children"].append(load_folders(item_path, depth + 1))
    else:
        # 递归边界
        documents["is_folder"] = False
        documents["name"] = os.path.basename(folder_path).replace(".md", "")
        documents["content"] = ""
        documents["depth"] = depth
        with open(folder_path, "r", encoding="utf-8") as file:
            documents["content"] = file.read()
    return documents


def extract_sections(text: str, identifier: str = "#"):
    """
    提取标识符分隔的标题和内容

    Args:
        text: 要解析的文本
        identifier: 标识符，默认为 "#"

    Returns:
        List of tuples: [(title, content), ...]
    """
    escaped_id = re.escape(identifier)
    # pattern修正：内容部分用非贪婪，并且直到下一个标题或结尾
    pattern = rf"^{escaped_id}\s+(.+?)$\n(.*?)(?=^{escaped_id}\s|\Z)"

    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)

    result = []
    for title, content in matches:
        clean_content = content.strip()
        result.append((title.strip(), clean_content))

    return result


def D2S(documents):
    global e_id_counter
    global id_counter

    nodes = []
    relations = []
    if documents["is_folder"]:
        node = Section(id=id_counter, title=documents["name"], level=documents["depth"])
        id_counter += 1
        root_id = node.id
        for child in documents["children"]:
            child_nodes, child_relations = D2S(child)
            nodes.extend(child_nodes)
            relations.append(
                Relation(
                    id=e_id_counter,
                    summary="",
                    descriptions=[],
                    type="has_subsection",
                    source_id=root_id,
                    target_id=child_nodes[0].id,
                    is_tree=True,
                )
            )
            node.to_relation.append(e_id_counter)
            child_nodes[0].from_relation.append(e_id_counter)
            e_id_counter += 1
            relations.extend(child_relations)

        nodes.append(node)

    else:
        now_node = Section(
            id=id_counter,
            title=documents["name"],
            level=documents["depth"],
        )
        now_node.raw_content = documents["content"]
        id_counter += 1
        processing_nodes = [now_node]
        while len(processing_nodes) > 0:
            now_node = processing_nodes.pop(0)
            now_target = "#" * (now_node.level - documents["depth"] + 1)
            while now_target in now_node.raw_content:
                results = extract_sections(now_node.raw_content, now_target)
                if len(results) == 0:
                    now_target+='#'
                else:
                    break
            results = extract_sections(now_node.raw_content, now_target)
            if len(results):
                now_node.is_elemental = False
                now_node.raw_content = ""
                for title, content in results:
                    node = Section(id=id_counter, title=title, level=now_node.level + 1)
                    id_counter += 1
                    node.raw_content = content
                    processing_nodes.append(node)

                    relation = Relation(
                        id=e_id_counter,
                        summary="",
                        descriptions=[],
                        type="has_subsection",
                        source_id=now_node.id,
                        target_id=node.id,
                        is_tree=True,
                    )
                    now_node.to_relation.append(relation.id)
                    node.from_relation.append(relation.id)
                    relations.append(relation)
                    e_id_counter += 1
            else:
                now_node.is_elemental = True
            nodes.append(now_node)

    return nodes, relations


def section_split(
    section: Section,
    document: str,
    max_level: int,
    Node: list,
    Edge: list,
    re_expression: list[str],
):
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
                subsection = Section(
                    id=id_counter, title=title, level=section.level + 1
                )
                id_counter += 1
                subsection.raw_content = content.strip()
                sections.append(subsection)
                Node.append(subsection)

                if subsection.level < max_level:
                    subsections = section_split(
                        subsection, content, max_level, Node, Edge, re_expression
                    )
                    if len(subsections) != 0:
                        for subsubsection in subsections:
                            edge = Relation(
                                id=e_id_counter,
                                summary="",
                                descriptions=[],
                                type="has_subsection",
                                source_id=subsection.id,
                                target_id=subsubsection.id,
                            )
                            subsection.to_relation.append(edge.id)
                            e_id_counter += 1
                            subsubsection.from_relation.append(edge.id)
                            Edge.append(edge)
                    else:
                        subsection.is_elemental = True
                else:
                    subsection.is_elemental = True

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
            subsections = section_split(
                subsection, content, max_level, Node, Edge, re_expression
            )
            if len(subsections) != 0:
                for subsubsection in subsections:
                    edge = Relation(
                        id=e_id_counter,
                        summary="",
                        descriptions=[],
                        type="has_subsection",
                        source_id=subsection.id,
                        target_id=subsubsection.id,
                        is_tree=True,
                    )
                    subsection.to_relation.append(edge.id)
                    e_id_counter += 1
                    subsubsection.from_relation.append(edge.id)
                    Edge.append(edge)
            else:
                subsection.is_elemental = True
        else:
            subsection.is_elemental = True

    return sections


def documents_to_sections(graph_structure_path: str = graph_structure_path):
    global id_counter, e_id_counter
    documents = load_folders(raw_path)  # 此处可以改成返回多重文件结构
    nodes, edges = D2S(documents)
    for node in nodes:
        if len(node.to_relation) == 0:
            node.is_elemental = True
    node_file_path = os.path.join(graph_structure_path, "section_nodes.json")
    edge_file_path = os.path.join(graph_structure_path, "has_subsection.json")
    print(f"章节节点数量: {len(nodes)}, 边数量: {len(edges)}")
    # 创建文件夹
    if not os.path.exists(graph_structure_path):
        os.makedirs(graph_structure_path)
    save_json(node_file_path, nodes)
    save_json(edge_file_path, edges)
