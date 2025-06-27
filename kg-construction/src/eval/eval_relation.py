# 衡量三个指标：1.关系逻辑性 2.关系完整性 3.关系丰富度
# 方法：1.对于所有的计算关系逻辑性的得分和关系完整性得分，取平均值作为得分
# 2. 关系完整性支持两种方法比较。第一种直接关键词匹配；第二种算关键词向量embedding之后找最近距离
from src.model.base_operator import RelationEvalOperation
from src.utils.file_operation import load_json
import os
import json
from src.utils.communication import execute_operator
    
def RS_external(root_path:str):
    """
    Evaluate the relation equality of the external data.
    data_folder_path:
        nodes.json
        [
            - id
            - title
            - alias
        ]
        relations.json
        [
            - source_id
            - target_id
            - description
        ]
        
    """
    # 加载entity
    nodes_path=os.path.join(root_path,'nodes.json')
    relations_path=os.path.join(root_path,'relations.json')
    nodes=load_json(nodes_path)
    relations=load_json(relations_path)
    raw=[]
    for rel in relations:
        if 'description' not in rel.keys():
            rel['description'] = rel['name']
        if rel['description']=='':
            continue
        raw.append((nodes[rel['source_id']]['title'],rel['description'],nodes[rel['target_id']]['title']))
    groups=[raw[i:i+16] for i in range(0,len(raw),16)]
    ops=[RelationEvalOperation(group) for group in groups]
    response=execute_operator(ops,cached_file_path=os.path.join(root_path,"relation_equality.json"),need_read_from_cache=False)
    score=[]
    for res in response:
        if res==None:
            continue
        score+=res
    average_relevance=sum(score)/len(score)
    
    if not os.path.exists(os.path.join(root_path, "result.json")):
        prev_data = []
    else:
        with open(os.path.join(root_path, "result.json"), "r", encoding="utf-8") as f:
            prev_data = json.load(f)
    with open(os.path.join(root_path, "result.json"), "w", encoding="utf-8") as f:
        result = {
            "name": "RS_eval",
            "root": root_path,
            "average_relevance": average_relevance,
        }
        prev_data.append(result)
        json.dump(prev_data, f, ensure_ascii=False, indent=4)
    

def RS_internal(data_root:str):
    """
    Evaluate the relation equality of the internal data.
    data_folder_path:
        nodes.json
        [
            - id
            - title
            - alias
        ]
        relations.json
        [
            - source_id
            - target_id
            - description
        ]
        
    """
    # 加载entity
    relations_path=os.path.join(data_root,'graph','relations.json')
    nodes_path=os.path.join(data_root,'graph','nodes.json')
    relations=load_json(relations_path)
    nodes=load_json(nodes_path)
    id_to_node={node['id']:node for node in nodes}
    raw=[]
    for rel in relations:
        if rel['description']=='':
            continue
        raw.append((id_to_node[rel['source_id']]['title'],rel['description'],id_to_node[rel['target_id']]['title']))
    groups=[raw[i:i+16] for i in range(0,len(raw),16)]
    ops=[RelationEvalOperation(group) for group in groups]
    response=execute_operator(ops,cached_file_path=os.path.join(data_root,'cache',"relation_equality.json"),need_read_from_cache=True)
    score=[]
    for res in response:
        if res==None:
            continue
        score+=res
    average_relevance=sum(score)/len(score)
    print(f'average_equality:{average_relevance}')
    if not os.path.exists(os.path.join(data_root,'eval')):
        os.makedirs(os.path.join(data_root,'eval'))
    with open(os.path.join(data_root,'eval','relation_equality.txt'),'w',encoding='utf-8') as f:
        f.write(f'average_relevance:{average_relevance}\n')