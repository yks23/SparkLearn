from sklearn.metrics import max_error
from ...src.utils.id_operation import graph_structure,GraphStructureType
import numpy as np
def get_aa_score()->dict[(int,int),float]:
    """返回一个字典，键为两个实体id，值为两个实体之间的aa_score"""
    """aa_score=∑1/log(degree(node))"""
    entities = graph_structure(type=[GraphStructureType.entity_node], return_type="object")[0]
    relations = graph_structure(type=[GraphStructureType.entity_related_relation], return_type="object")[0]
    degree_map={ent.id:len(ent.to_relation+ent.from_relation)-1 for ent in entities}
    adjoint_nodes={ent.id:set() for ent in entities}
    for rel in relations:
        adjoint_nodes[rel.source_id].add(rel.target_id)
        adjoint_nodes[rel.target_id].add(rel.source_id)
    aa_score={}
    for ent1 in entities:
        for ent2 in entities:
            i=ent1.id
            j=ent2.id
            if i>=j:
                continue
            if j in adjoint_nodes[i]:
                continue
            common_nodes=adjoint_nodes[i]&adjoint_nodes[j]
            if len(common_nodes)==0:
                continue
            score=0
            for node in common_nodes:
                score+=1/np.log(degree_map[node])
            aa_score[(i,j)]=score
            aa_score[(j,i)]=score
    return aa_score

def get_ra_score() -> dict[(int, int), float]:
    """返回一个字典，键为两个实体id，值为两个实体之间的RA_score"""
    """RA_score=∑1/degree(node)"""
    entities = graph_structure(type=[GraphStructureType.entity_node], return_type="object")[0]
    relations = graph_structure(type=[GraphStructureType.entity_related_relation], return_type="object")[0]
    
    degree_map = {ent.id: len(ent.to_relation + ent.from_relation - 1) for ent in entities}
    adjoint_nodes = {ent.id: set() for ent in entities}
    for rel in relations:
        adjoint_nodes[rel.source_id].add(rel.target_id)
        adjoint_nodes[rel.target_id].add(rel.source_id)
    
    ra_score = {}
    for ent1 in entities:
        for ent2 in entities:
            i = ent1.id
            j = ent2.id
            if i >= j:
                continue
            if j in adjoint_nodes[i]:
                continue
            common_nodes = adjoint_nodes[i] & adjoint_nodes[j]
            if len(common_nodes) == 0:
                continue
            score = sum(1 / degree_map[node] for node in common_nodes)
            ra_score[(i, j)] = score
            ra_score[(j, i)] = score
    
    return ra_score
def get_pa_score() -> dict[(int, int), float]:
    """返回一个字典，键为两个实体id，值为两个实体之间的PA_score"""
    """PA_score=degree(node1)*degree(node2)"""
    entities = graph_structure(type=[GraphStructureType.entity_node], return_type="object")[0]
    relations = graph_structure(type=[GraphStructureType.entity_related_relation], return_type="object")[0]
    
    degree_map = {ent.id: len(ent.to_relation + ent.from_relation - 1) for ent in entities}
    adjoint_nodes = {ent.id: set() for ent in entities}
    for rel in relations:
        adjoint_nodes[rel.source_id].add(rel.target_id)
        adjoint_nodes[rel.target_id].add(rel.source_id)
    
    pa_score = {}
    for ent1 in entities:
        for ent2 in entities:
            i = ent1.id
            j = ent2.id
            if i >= j:
                continue
            if j in adjoint_nodes[i]:
                continue
            score = degree_map[i] * degree_map[j]
            pa_score[(i, j)] = score
            pa_score[(j, i)] = score
    
    return pa_score
def get_cn_score() -> dict[(int, int), float]:
    """返回一个字典，键为两个实体id，值为两个实体之间的CN_score"""
    """CN_score=|common_nodes|"""
    entities = graph_structure(type=[GraphStructureType.entity_node], return_type="object")[0]
    relations = graph_structure(type=[GraphStructureType.entity_related_relation], return_type="object")[0]
    
    adjoint_nodes = {ent.id: set() for ent in entities}
    for rel in relations:
        adjoint_nodes[rel.source_id].add(rel.target_id)
        adjoint_nodes[rel.target_id].add(rel.source_id)
    
    cn_score = {}
    for ent1 in entities:
        for ent2 in entities:
            i = ent1.id
            j = ent2.id
            if i >= j:
                continue
            if j in adjoint_nodes[i]:
                continue
            common_nodes = adjoint_nodes[i] & adjoint_nodes[j]
            if len(common_nodes) == 0:
                continue
            cn_score[(i, j)] = len(common_nodes)
            cn_score[(j, i)] = len(common_nodes)
    return cn_score
def get_common_score() -> dict[(int,int),int]:
    """common_score=|common_parents|，描述的是两个实体最多共同祖先的多少"""
    has_entity=graph_structure(type=[GraphStructureType.has_entity_relation],return_type='object')[0]
    has_subsection=graph_structure(type=[GraphStructureType.section_belong_connection],return_type='object')[0]
    entity_node=graph_structure(type=[GraphStructureType.entity_node],return_type='object')[0]
    parent={}
    for rel in has_entity+has_subsection:
        parent[rel.target_id]=parent.get(rel.target_id,[])+[rel.source_id]
    common_score={}
    for ent1 in entity_node:
        for ent2 in entity_node:
            if ent1.id>=ent2.id:
                continue    
            max_common=0
            for ii in parent[ent1.id]:
                for jj in parent[ent2.id]:
                    i=ii
                    j=jj
                    parents_1={i}
                    while parent.get(i) is not None:
                        i=parent[i][0]
                        parents_1.add(i)
                    parents_2={j}
                    while parent.get(j) is not None:
                        j=parent[j][0]
                        parents_2.add(j)
                    common=parents_1&parents_2
                    max_common=max(max_common,len(common))
            
            common_score[(ent1.id,ent2.id)] = max_common
            common_score[(ent2.id,ent1.id)] = max_common
    
    return common_score
    
