import os

from ....src.model.section import Section
from ....src.utils import save_json
from ....src.config import request_cache_path, final_prompt_path,max_level,graph_structure_path
from ....src.model.base_operator import RelationExtractionoperation,Summaryoperator
from ....src.utils.communication import execute_operator
from ....src.utils.id_operation import graph_structure,GraphStructureType,get_sons
def get_community_report(level:int,nodes:list[Section]):
    tackle_nodes=[node for node in nodes if node.level==level]
    type_1_node=[node for node in tackle_nodes if node.is_elemental==True]
    type_2_node=[node for node in tackle_nodes if node.is_elemental==False]
    id_to_sons=get_sons()
    if len(type_1_node)!=0:
        ops=[Summaryoperator(node) for node in type_1_node]
        request_response=execute_operator(ops,cached_file_path=os.path.join(request_cache_path,f"community_summary_{level}.json"),need_read_from_cache=True)
        for (node,response) in zip(type_1_node,request_response):
            if response==None:
                node.summary=node.raw_content
                node.example=[]
                continue
            node.summary=response.get("summary","")
            node.example=response.get("example",[])
    print(id_to_sons.keys())
    if len(type_2_node)!=0:
        ops=[Summaryoperator(node,id_to_sons[node.id]) for node in type_2_node]
        request_response=execute_operator(ops,cached_file_path=os.path.join(request_cache_path,f"community_summary_{level}.json"),need_read_from_cache=True)
        for (node,response) in zip(type_2_node,request_response):
            if response==None:
                node.summary=node.raw_content
                continue
            node.summary=response
            if isinstance(response,dict):
                node.summary=response.get("summary",[])
    return 
    
def community_report():
    nodes=graph_structure([GraphStructureType.section_node],return_type="object")[0]
    relations=graph_structure([GraphStructureType.section_belong_connection],return_type="object")[0]
    relation_id_begin=len(graph_structure([GraphStructureType.all_relation],return_type="object")[0])
    node_dict,edge_dict={ node.id:node for node in nodes},{relation.id:relation for relation in relations}
    prompt3_path = os.path.join(final_prompt_path, "section_rel_extract.txt")
    # 自下而上处理
    for i in range(max_level):
        get_community_report(max_level-i, nodes)
    all_opt=[]
    # 提取关系
    for section in nodes:
        if section.is_elemental==False:
            subsection=[node_dict[edge_dict[edge_id].target_id] for edge_id in section.to_relation]
            opt=RelationExtractionoperation(section.summary,subsection,system_prompt_path=prompt3_path)
            all_opt.append(opt)
    response=execute_operator(ops=all_opt,cached_file_path=os.path.join(request_cache_path,"community_report_cache.json"),need_read_from_cache=True)
    last_id=relation_id_begin
    for i in range(len(response)):
        if not isinstance(response[i].get('relations',None),list):
            continue
        for j in response[i]['relations']:
            j['id']=last_id
            processed_reponse=RelationExtractionoperation.get_relation_from_response(j)
            if processed_reponse is  None:
                continue
            relations.append(processed_reponse)
            node_dict[processed_reponse.source_id].to_relation.append(processed_reponse.id)  
            node_dict[processed_reponse.target_id].from_relation.append(processed_reponse.id)
            last_id+=1
    has_subsection_relations = [
        rel
        for rel in relations
        if rel.type == "has_subsection"
    ]
    section_related_relations = [
        rel
        for rel in relations
        if rel.type != "has_subsection"
    ]
    save_json(os.path.join(graph_structure_path, "section_nodes.json"),nodes)
    save_json(os.path.join(graph_structure_path, "has_subsection.json"),has_subsection_relations)
    save_json(os.path.join(graph_structure_path, "section_related.json"),section_related_relations)
    # os.remove(os.path.join(request_cache_path,"community_report_cache.json"))