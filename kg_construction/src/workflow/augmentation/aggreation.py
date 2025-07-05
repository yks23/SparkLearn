from src.model import Section, Entity
from src.model.graph_structure import GraphStructureType
from src.utils import save_json,communicate_with_agent
from src.model.base_operator import AggregationOperation
from src.config import request_cache_path,final_prompt_path,graph_structure_path
from src.utils.file_operation import save_json
from src.utils.id_operation import realloc_id,graph_structure,save_relation
import os
def  load_data():
    """加载数据"""
    [node_dict,edge_dict] = graph_structure([GraphStructureType.all_node,GraphStructureType.all_relation],return_type='dict')
    node_dict = {node["id"]: node for node in node_dict}
    edge_dict = {edge["id"]: edge for edge in edge_dict}
    [section_nodes,entity_nodes] = graph_structure([GraphStructureType.section_node,GraphStructureType.entity_node],return_type='object')
    with open(final_prompt_path + "/aggregation_prompt.txt","r",encoding="utf-8") as f:
        system_prompt1 = f.read()
    with open(final_prompt_path + "/relation_detection_prompt.txt","r",encoding="utf-8") as f:
        system_prompt2 = f.read()
    return section_nodes,entity_nodes,node_dict,edge_dict,system_prompt1,system_prompt2
def get_node_info(node_id, node_dict):
    """获取节点信息"""
    if node_id not in node_dict:
        return f"错误：未找到ID为{node_id}的节点"
        
    node = node_dict[node_id]
    node_info = ""
    
    # 使用.get()方法安全地获取字典值
    if node.get('level') is None:
        node_info += f"名称：{node.get('title', '未知')}\n"
        node_info += f"ID：{node_id}\n"
        descriptions = node.get('descriptions', [])
        node_info += f"描述：{descriptions[-1] if descriptions else '无描述'}\n"
    else:
        node_info += f"名称：{node.get('title', '未知')}\n"
        node_info += f"描述：{node.get('summary', '无描述')}\n"
    return node_info

def get_edge_update(node_id,source_id,node_dict):
    """获取边更新信息"""
    user_input="发生更改的实体是：\n"+get_node_info(node_id,node_dict)+"\n"+"与它相邻的实体是：\n"+get_node_info(source_id,node_dict)+"\n"+"请根据以上信息和提示词要求，完成边更新任务"
    return user_input
def aggreation_with_response(aggreation_response, edge_update_response, node_dict, edge_dict, aggreation_actions, relation_actions):
    """根据聚合和边更新响应更新节点和边"""
    for agg in aggreation_response:
        if agg=={} or agg==None or not isinstance(agg, dict):
            continue
        try:
            agg["aggregation"]["id"]=int(agg["aggregation"]["id"])
            agg["reserved_entities"]=[int(entity) for entity in agg["reserved_entities"]]
        except:
            agg={}
            continue
    for edge in edge_update_response:
        if edge!={} and edge!=None and isinstance(edge, dict):
            try:
                edge["source"]=int(edge["source_id"])
                edge["target"]=int(edge["target_id"])
            except:
                edge={}
                continue
    for aggreation, action in zip(aggreation_response, aggreation_actions):
        if aggreation=={} or aggreation==None or not isinstance(aggreation, dict): 
            continue
        node_id = action[0]
        if node_id not in node_dict:
            continue
        if aggreation.get("aggregation"):
            agg_data = aggreation["aggregation"]
            node_dict[node_id].update({
                "title": agg_data.get("name", node_dict[node_id].get("title")),
                "alias": agg_data.get("alias", []),
                "descriptions": [agg_data.get("raw_content", ""),agg_data.get("description", "")],
            })
        # 安全地获取保留的实体列表
        reserved_entities = aggreation.get("reserved_entities", [])
        reserved_entities=[int(entity) for entity in reserved_entities if isinstance(entity,int)]
        # 安全地移除被聚合的实体和边
        for rel_id in list(node_dict[node_id].get("from_relation", [])):
            if rel_id not in edge_dict:
                continue
            source_id = edge_dict[rel_id].get("source_id")
            if source_id and source_id not in reserved_entities and source_id in action[1]:
                node_dict.pop(int(source_id), None)
        for rel_id in list(node_dict[node_id].get("to_relation", [])):
            if rel_id not in edge_dict:
                continue
            target_id = edge_dict[rel_id].get("target_id")
            if target_id and target_id not in reserved_entities and target_id in action[1]:
                node_dict.pop(int(target_id), None)
    for rel_id,edge_update in zip(relation_actions,edge_update_response):
            if rel_id not in edge_dict.keys() or edge_update=={} or edge_update==None or not isinstance(edge_update, dict):
                continue
            if edge_update.get("raw_content")!=None:
                edge_dict[rel_id].get("descriptions",[]).append(edge_update["raw_content"])
            if edge_update.get("description")!=None:
                edge_dict[rel_id].get("descriptions",[]).append(edge_update["description"])
            
        
    for relation in list(edge_dict.values()):
        if relation.get("source_id") not in node_dict.keys() or relation.get("target_id") not in node_dict.keys():
            edge_dict.pop(relation["id"],None)
    # 将节点和边的Id按顺序排列
    node_list = list(node_dict.values())
    edge_list = list(edge_dict.values())
    sorted_nodes = sorted(node_list, key=lambda x: x["id"])
    sorted_edges = sorted(edge_list, key=lambda x: x["id"])
        # 创建新的ID映射
    node_id_map = {node["id"]: i + sorted_nodes[0]["id"] for i, node in enumerate(sorted_nodes)}
    edge_id_map = {edge["id"]: i + sorted_edges[0]["id"] for i, edge in enumerate(sorted_edges)}
        
        # 修改这部分代码，正确遍历字典
    for node_id in list(node_dict.keys()):
        node = node_dict[node_id]
        new_id = node_id_map[node["id"]]
        node["id"] = new_id
        node["from_relation"] = [edge_id_map[rel_id] for rel_id in node["from_relation"] if rel_id in edge_id_map.keys()]
        node["to_relation"] = [edge_id_map[rel_id] for rel_id in node["to_relation"] if rel_id in edge_id_map.keys()]

    for edge_id in list(edge_dict.keys()):
        edge = edge_dict[edge_id]
        edge["id"]=int(edge["id"])
        edge["source_id"]=int(edge["source_id"])
        edge["target_id"]=int(edge["target_id"])
        if edge["id"] in edge_id_map.keys():
            new_id = edge_id_map[int(edge["id"])]
            edge["id"] = new_id
            edge["source_id"] = node_id_map[edge["source_id"]]
            edge["target_id"] = node_id_map[edge["target_id"]]
def aggreation():
    section_nodes,entity_nodes,node_dict,edge_dict,system_prompt1,system_prompt2 = load_data()
    
    len1,len2=len(edge_dict),len(node_dict)
    considered_nodes = set()
    aggreation_input=[]
    edge_update=[]
    ents=graph_structure(type=[GraphStructureType.entity_node],return_type='object')[0]
    ents={ent.id:ent for ent in ents}
    aggreation_actions=[]
    for node in entity_nodes:
        du = len(node.from_relation)+len(node.to_relation)-1
        if du <= 2:
            continue
        else:
            near_leaves_nodes = []
            for relation_id in node.from_relation:
                relation = edge_dict[relation_id]
                if relation["type"]=="has_entity":
                    continue
                if (len(node_dict[relation["source_id"]]["from_relation"])+len(node_dict[relation["source_id"]]["to_relation"])) == 2 and relation["source_id"] not in considered_nodes and relation["type"]!="has_entity":
                    near_leaves_nodes.append(relation["source_id"])
                    considered_nodes.add(relation["source_id"])
            for relation_id in node.to_relation:
                relation = edge_dict[relation_id]
                if (len(node_dict[relation["target_id"]]["from_relation"])+len(node_dict[relation["target_id"]]["to_relation"])) == 2 and relation["target_id"] not in considered_nodes and relation["type"]!="has_entity":
                    near_leaves_nodes.append(relation["target_id"])
                    considered_nodes.add(relation["target_id"])
            
            considered_nodes.add(node.id)
            if len(near_leaves_nodes) >= (len(node.from_relation)+len(node.to_relation)-2)*0.75:
                aggreation_input.append(AggregationOperation(core_entity=ents[node.id],near_leaves=[ents[ent] for ent in near_leaves_nodes]).user_input)
                aggreation_actions.append((node.id,near_leaves_nodes))
    
    aggreation_response = communicate_with_agent(system_prompt1,aggreation_input,need_json=True,need_batch=True,cached_file_path=os.path.join(request_cache_path,"aggregation_response.json"),need_read_from_cache=True)
    changed_nodes=[]
    for agg,act in zip(aggreation_response,aggreation_actions):
        if agg=={} or agg==None or not isinstance(agg, dict):
            continue
        if agg.get("aggregation")==None or agg.get("reserved_entities")==None:
            continue
        if len(agg['reserved_entities'])!=len(act[1]):
            changed_nodes.append(act[0])
            print("changed: ",act[0])
            for ent in act[1]:
                if ent not in agg['reserved_entities']:
                    print("deleted: ",ent)
    relation_actions=[]
    for (node_id,near_leaves_nodes) in aggreation_actions:
        if node_id not in changed_nodes:
            continue
        for rel_id in node_dict[node_id]["from_relation"]:
            if node_dict[edge_dict[rel_id]["source_id"]].get("level")!=None or edge_dict[rel_id]["source_id"] in near_leaves_nodes or edge_dict[rel_id]["type"]=="has_entity":
                continue
            else:
                edge_update.append(get_edge_update(node_id,edge_dict[rel_id]["source_id"],node_dict))
                relation_actions.append(rel_id)
        for rel_id in node_dict[node_id]["to_relation"]:
            if node_dict[edge_dict[rel_id]["target_id"]].get("level")!=None or edge_dict[rel_id]["target_id"] in near_leaves_nodes or edge_dict[rel_id]["type"]=="has_entity":
                continue
            else:
                relation_actions.append(rel_id)
                edge_update.append(get_edge_update(node_id,edge_dict[rel_id]["target_id"],node_dict))
    edge_update_response = communicate_with_agent(system_prompt2,edge_update,need_json=True,need_batch=True,cached_file_path=os.path.join(request_cache_path,"edge_update_response.json"),need_read_from_cache=True)
    aggreation_with_response(aggreation_response,edge_update_response,node_dict,edge_dict,aggreation_actions,relation_actions)
    # 将node_dict和edge_dict转换为列表，并分割成sections和entities
    section_nodes=[Section(**node) for node in node_dict.values() if node.get("level")!=None]
    entity_nodes=[Entity(**node) for node in node_dict.values() if node.get("level")==None]
    entity_ids={node.id for node in entity_nodes}
    save_relation(list(edge_dict.values()),entity_ids)
    print("消去了",len1-len(edge_dict),"条边","删除了",len2-len(node_dict),"个节点")
    save_json(graph_structure_path + "/section_nodes.json",section_nodes)
    save_json(graph_structure_path + "/entity_nodes.json",entity_nodes)
    realloc_id()
    os.remove(os.path.join(request_cache_path,"aggregation_response.json"))
    os.remove(os.path.join(request_cache_path,"edge_update_response.json"))