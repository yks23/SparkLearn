from src.utils.engine import initialize_with_title,initial_engine_with_str
from src.utils.file_operation import save_json, load_json
from src.utils.id_operation import graph_structure,get_parent
from src.model.graph_structure import GraphStructureType
import os
def prepare_gt_data(data_raw_path:str,save_path:str):
    gt=load_json(data_raw_path)
    for ent in gt:
        if 'title' not in ent.keys():
            ent['title']=ent['name']
    gt=[ent for ent in gt if ent['title']!=""]
    titles=[ent['title'] for ent in gt]
    engine=initial_engine_with_str(titles,os.path.join(save_path,"engine.ann"),os.path.join(save_path,"table.json"))
    for i,ent in enumerate(gt):
        ent['embedding']=engine.get_vector_by_id(i)
        ent['embedding']=[float(e) for e in ent['embedding']]
        ent['name']=ent['title']
    save_json(os.path.join(save_path,'nodes.json'),gt)
    
def prepare_engine_special_section(core_id:int,cache_path:str,engine_save_folder:str):
    if os.path.exists(engine_save_folder) == False:
        os.makedirs(engine_save_folder)
    entities=graph_structure(type=[GraphStructureType.all_node],return_type='object',cache_path=cache_path)[0]
    relations=graph_structure(type=[GraphStructureType.all_relation],return_type='object',cache_path=cache_path)[0]
    
    f=get_parent(cache_path)
    needed_nodes=[]
    q=[]
    for ent in entities:
        q=[ent.id]
        while len(q):
            node=q[0]
            if node==core_id:
                needed_nodes.append(ent)
                break
            q.pop(0)
            q.extend(f[node] if node in f.keys() else [])
            if node not in f.keys():
                continue
    if core_id==-1:
        needed_nodes=entities
    engine,id_map=initialize_with_title(needed_nodes,os.path.join(engine_save_folder,"engine.ann"),os.path.join(engine_save_folder,"table.json"))
    print(id_map)
    rels=[]
    for rel in relations:
        if rel.source_id in id_map.keys() and rel.target_id in id_map.keys():
            r={
                'source_id':id_map[rel.source_id],
                'target_id':id_map[rel.target_id],
                'description':rel.descriptions[-1] if len(rel.descriptions)>0 else ""
            }
            rels.append(r)
    save_json(os.path.join(engine_save_folder,"relations.json"),rels)
    engine.save_state(engine_save_folder)
    
def prepare_entity_data_1(cache_path:str,engine_save_folder:str):
    entitis=graph_structure(type=[GraphStructureType.entity_node],return_type='object',cache_path=cache_path)[0]
    engine=initialize_with_title(entitis,os.path.join(engine_save_folder,"engine.ann"),os.path.join(engine_save_folder,"table.json"))
    engine.save_state(engine_save_folder)
def prepare_entity_data(cache_path:str,engine_save_folder:str):
    data=load_json(cache_path)
    data=[list(d.values())[0] for d in data]
    engine=initial_engine_with_str(data,engine_path=os.path.join(engine_save_folder,"engine.ann"),table_path=os.path.join(engine_save_folder,"table.json"))
    engine.save_state(engine_save_folder)
def translation_data(data_raw_path:str,save_path:str):
    gt_data=load_json(data_raw_path)
    name_list=[ent['title'] for ent in gt_data]
    print(name_list)
    save_json(save_path,name_list)
    # gt_title=[ent['name'] for ent in gt_data]
    # gt_groups=[gt_title[i:i+100] for i in range(0,len(gt_title),100)]
    # ops=[TranslationOperation(title) for title in gt_groups]
    
    # response1=execute_operator(ops,cached_file_path='./embedding_cache.json',need_batch=True)
    # for res , ent in zip(response1,gt_data):
    #     ent['name']=res
    # save_json(save_path,gt_data)


def prepare_itext2kg():
    nodedata=load_json('.\experiment\itext2kg\data_txt\\txt_0.7_nodes.json')
    reldata=load_json('.\experiment\itext2kg\data_txt\\txt_0.7_edges.json')
    name_to_id={}
    for i in range(len(nodedata)):
        name_to_id[nodedata[i]['name']]=i
        nodedata[i]['id']=i
    for rel in reldata:
        rel['source']['id']=name_to_id[rel['source']['name']]
        rel['target']['id']=name_to_id[rel['target']['name']]
    all_names=[ent['name'] for ent in nodedata]
    engine=initial_engine_with_str(all_names,engine_path='.\GroundTruth\Itext2kg\engine\engine.ann',table_path='.\GroundTruth\Itext2kg\engine\\table.json')
    engine.save_state('.\GroundTruth\Itext2kg\engine')
    save_json('.\GroundTruth\Itext2kg\\raw\\nodes.json',nodedata)
    save_json('.\GroundTruth\Itext2kg\\raw\\edges.json',reldata)
