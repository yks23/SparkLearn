import os
from ....src.model.base_operator import AugmentationOperation,EmbeddingEntityoperation
from ....src.utils.id_operation import graph_structure, GraphStructureType
from ....src.utils.file_operation import save_json
from ....src.utils.engine import initialize_entity_engine
from ....src.config import request_cache_path,graph_structure_path
from ....src.utils.communication import execute_operator
def augment_with_relation(new_relations:list,engine_folder:str=None):
    # 初始化实体节点和关系边
    [entity_nodes,relation_edges] = graph_structure(type=[GraphStructureType.entity_node,GraphStructureType.entity_related_relation],return_type='object')
    entity_adjacency = {node.id:[] for node in entity_nodes}
    for rel in new_relations:
        entity_adjacency[rel.source_id].append((rel.target_id,rel.id))
        entity_adjacency[rel.target_id].append((rel.source_id,rel.id))
    entity_map = {node.id:node for node in entity_nodes}
    relation_map = {rel.id:rel for rel in relation_edges}
    ops=[]
    for ent,rels in entity_adjacency.items():
        if len(rels)==0:
            continue
        near_relations = [relation_map[rel[1]] for rel in rels] 
        near_nodes = [entity_map[rel[0]] for rel in rels]
        ops.append(AugmentationOperation(entity_map[ent],near_relations,near_nodes))
    # 执行操作
    response = execute_operator(ops,cached_file_path=os.path.join(request_cache_path,"augmentation.json"))
    # 保存结果
    changed_entities = []
    for op,res in zip(ops,response):
        entity_map[op.core_id].descriptions.append(res)
        changed_entities.append(entity_map[op.core_id])
    entities_group=[changed_entities[i:i+32] for i in range(0,len(changed_entities),32)]
    all_op = [EmbeddingEntityoperation(entities,level=-1) for entities in entities_group]
    response=execute_operator(all_op,cached_file_path=os.path.join(request_cache_path,"augmentation_embedding.json"))
    vector_np = [result["embedding"] for result in response]
    engine = initialize_entity_engine(entitis=changed_entities,engine_path=os.path.join(engine_folder,'engine.ann'),table_path=os.path.join(engine_folder,'table.json'))
    for id,vec in zip([ent.id for ent in changed_entities],vector_np):
        engine.change_entity(id,vec)
    # 重新嵌入
    engine.save_state(engine_folder)
    all_entities=[entity_map[ent.id] for ent in entity_nodes]
    save_json(os.path.join(graph_structure_path,'entity_nodes.json'),all_entities)
    
    