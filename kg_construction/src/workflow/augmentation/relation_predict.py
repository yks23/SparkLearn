from numpy import average
from src.utils.engine import initialize_entity_engine
from src.utils.id_operation import graph_structure, get_relation_id, realloc_id
from src.model.graph_structure import GraphStructureType
from src.model.base_operator import (
    CheckMergeoperation,
    RelationPredictoperation,
    RelationevalOperation,
)
from src.model.relation import Relation
from src.utils.communication import execute_operator
from src.utils.file_operation import save_json, load_json
from src.config import engine_cache_path, max_level
from src.utils.score import get_aa_score, get_common_score
from src.config import request_cache_path, graph_structure_path
import os
import logging
import tqdm
def get_parent(mp: dict[int, int], id: int):
    if mp[id] == id:
        return id
    mp[id] = get_parent(mp, mp[id])
    return mp[id]


def from_dis_to_cos(dis) -> float:
    return (2 - dis**2) / 2


def relation_predict():
    engine_path = os.path.join(engine_cache_path, "engine.ann")
    table_path = os.path.join(engine_cache_path, "table.json")
    engine = initialize_entity_engine(engine_path=engine_path, table_path=table_path)
    entities = graph_structure(
        type=[GraphStructureType.entity_node], return_type="object"
    )[0]
    relations = graph_structure(
        type=[GraphStructureType.entity_related_relation], return_type="object"
    )[0]

    aa_score = get_aa_score()
    common_score = get_common_score()
    exists_rel = {(rel.source_id, rel.target_id) for rel in relations}
    entity_map = {entity.id: entity for entity in entities}
    priorities = []

    for ent1 in entities:
        for ent2 in entities:
            if ent1.id >= ent2.id:
                continue
            if (ent1.id, ent2.id) in exists_rel:
                continue
            score = aa_score.get((ent1.id, ent2.id), 0) * 0.3 + (
                1 - 0.3
            ) * from_dis_to_cos(engine.get_distance(ent1.id, ent2.id))
            priorities.append((ent1.id, ent2.id, score))
    priorities.sort(key=lambda x: x[2], reverse=True)
    priorities = priorities[:len(entities)*0.5]
    for p in priorities:
        print(p)
        print(engine.get_distance(p[0], p[1]))
        print(common_score.get((p[0], p[1]), -1))
    ops = [
        RelationPredictoperation(entity_map[p[0]], entity_map[p[1]]) for p in priorities
    ]
    predictions = execute_operator(
        ops,
        cached_file_path=os.path.join(request_cache_path, "relation_predict.json"),
        need_read_from_cache=True,
    )
    start_id = get_relation_id()
    newrelations = []
    eval_ops = []
    for pred, op in zip(predictions, ops):
        if pred == None or pred == {} or pred.get("is_relevant", False) == False:
            continue
        start_id += 1
        newrelation = Relation(
            id=start_id,
            source_id=op.src_entity.id,
            target_id=op.tar_entity.id,
            type=pred.get("type", "related"),
            descriptions=[pred.get("description", "")],
        )
        eval_ops.append(
            RelationevalOperation(
                entity_map[op.src_entity.id],
                [newrelation],
                [entity_map[op.tar_entity.id]],
                level=-1,
            )
        )
        newrelations.append(newrelation)

    response = execute_operator(
        eval_ops,
        cached_file_path=os.path.join(request_cache_path, "relation_eval_new.json"),
        need_read_from_cache=True,
    )
    score_logic = 0
    score_completency = 0
    score_valid = 0
    score_novelty = 0
    for eval in response:
        eval = RelationevalOperation.repair(eval)[0]
        if eval[0] == -1:
            continue
        score_valid += 1
        score_logic += eval[1]
        score_completency += eval[2]
        score_novelty += eval[3]

    print(f"Add {len(newrelations)} relations")
    print(f"Logic:{score_logic/score_valid}")
    print(f"Completency:{score_completency/score_valid}")
    print(f"Novelty:{score_novelty/score_valid}")
    relations.extend(newrelations)
    save_json(os.path.join(graph_structure_path, "entity_edges.json"), relations)


def continue_predict(threshold: float = 7, dist: int = 1):
    """
    threshold: 关系预测的阈值
    dist: 关系预测的距离
    """
    engine_path = os.path.join(engine_cache_path, "engine.ann")
    table_path = os.path.join(engine_cache_path, "table.json")
    engine = initialize_entity_engine(engine_path=engine_path, table_path=table_path)
    entities = graph_structure(
        type=[GraphStructureType.entity_node], return_type="object"
    )[0]
    relations = graph_structure(
        type=[GraphStructureType.entity_related_relation], return_type="object"
    )[0]

    aa_score = get_aa_score()
    common_score = get_common_score()
    exists_rel = {(rel.source_id, rel.target_id) for rel in relations}
    entity_map = {entity.id: entity for entity in entities}
    priorities = []
    cnt_common = {}
    for ent1 in entities:
        for ent2 in entities:
            if ent1.id >= ent2.id:
                continue
            if (ent1.id, ent2.id) in exists_rel:
                continue
            if common_score.get((ent1.id, ent2.id), 0) >= max_level - dist:
                continue
            score = (
                aa_score.get((ent1.id, ent2.id), 0) * 0.3
                + (1 - 0.3 - 0.1)
                * from_dis_to_cos(engine.get_distance(ent1.id, ent2.id))
                + 0.1 * common_score.get((ent1.id, ent2.id), 0)
            )
            priorities.append((ent1.id, ent2.id, score))
            cnt_common[common_score[(ent1.id, ent2.id)]] = (
                cnt_common.get(common_score[(ent1.id, ent2.id)], 0) + 1
            )
    pre_common = {}
    # 确定优先级
    priorities.sort(key=lambda x: x[2], reverse=True)
    # 保留前#entities个
    priorities = priorities[: len(entities)//2]
    for p in priorities:
        pre_common[common_score[(p[0], p[1])]] = (
            pre_common.get(common_score[(p[0], p[1])], 0) + 1
        )
    ops = [
        RelationPredictoperation(entity_map[p[0]], entity_map[p[1]]) for p in priorities
    ]
    predictions = execute_operator(
        ops,
        cached_file_path=os.path.join(request_cache_path, "relation_predict.json"),
        need_read_from_cache=True,
        need_show_progress=True
    )
    start_id = get_relation_id()
    # 进行加边操作
    newrelations = []
    novelty_sum = 0
    all_score = []
    for response, op in zip(predictions, ops):
        # 判断边的质量是否达到要求
        novelty = RelationPredictoperation.get_strength(response)
        if novelty < threshold:
            continue
        relation = op.get_relation(start_id, response)
        if relation == None:
            continue
        start_id += 1
        newrelations.append(relation)
        novelty_sum += novelty
        all_score.append(novelty)
    if len(newrelations) < 10:
        finish = True
    else:
        finish = False
    relations = relations + newrelations
    save_json(os.path.join(graph_structure_path, "entity_related.json"), relations)
    return finish, newrelations


def connection_predict(threshold: float = 7):
    """将指定层次的图补至联通"""
    entities = graph_structure(
        type=[GraphStructureType.entity_node], return_type="object"
    )[0]
    relations = graph_structure(
        type=[GraphStructureType.entity_related_relation], return_type="object"
    )[0]
    engine = initialize_entity_engine(
        engine_path=os.path.join(engine_cache_path, "engine.ann"),
        table_path=os.path.join(engine_cache_path, "table.json"),
    )
    exists_rel = {(rel.source_id, rel.target_id) for rel in relations}
    entity_map = {entity.id: entity for entity in entities}
    newrelations = []
    injection = {ent.id: ent.id for ent in entities}
    allcnt = 0
    successcnt = 0
    for rel in exists_rel:
        # 建立已有并查集
        injection[get_parent(injection, rel[0])] = get_parent(injection, rel[1])
    common_score = get_common_score()
    priorities = []
    for ent1 in entities:
        for ent2 in entities:
            if ent1.id >= ent2.id:
                continue
            if get_parent(injection, ent1.id) == get_parent(injection, ent2.id):
                continue
            score = from_dis_to_cos(
                engine.get_distance(ent1.id, ent2.id)
            ) + 0.2 * common_score.get((ent1.id, ent2.id), 0)
            priorities.append((ent1.id, ent2.id, score))
    # 确定优先级
    priorities.sort(key=lambda x: x[2], reverse=True)
    for ent1, ent2, score in priorities:
        ent1 = entity_map[ent1]
        ent2 = entity_map[ent2]
        if ent1.id >= ent2.id:
            continue
        if get_parent(injection, ent1.id) == get_parent(injection, ent2.id):
            continue
        logging.info(f"ALL {allcnt}: SUCCESS {successcnt}")
        allcnt += 1
        op = RelationPredictoperation(entity_map[ent1.id], entity_map[ent2.id])
        response = execute_operator([op])[0]
        logging.info(f"Try to connect {entity_map[ent1.id].title} {entity_map[ent2.id].title}")
        novelty = RelationPredictoperation.get_strength(response)
        if novelty < threshold:
            continue
        relation = op.get_relation(get_relation_id(), response)
        if relation == None:
            continue
        successcnt += 1
        newrelations.append(relation)
        injection[get_parent(injection, ent1.id)] = get_parent(injection, ent2.id)
    relations = relations + newrelations
    save_json(os.path.join(graph_structure_path, "entity_related.json"), relations)


def identical_predict(
    threshold: float, engine_path: str, table_path: str, folder_path: str
):
    """Target:补齐连边，使得为后续augmented做准备"""
    engine = initialize_entity_engine(engine_path=engine_path, table_path=table_path)
    entities = graph_structure(
        type=[GraphStructureType.entity_node], return_type="object"
    )[0]
    [relations_2, relations_1] = graph_structure(
        type=[
            GraphStructureType.has_entity_relation,
            GraphStructureType.entity_related_relation,
        ],
        return_type="object",
    )
    exists_rel = {(rel.source_id, rel.target_id) for rel in relations_1}
    entity_map = {entity.id: entity for entity in entities}
    not_equal_pairs = set()
    dist = []
    jection = {ent.id: ent.id for ent in entities}
    cnt_success = 0
    cnt_all = 0
    all_pair = []
    for entity in entities:
        similarity = engine.search_by_id(entity.id, 20)
        for sim in similarity:
            if entity_map[sim].is_core_entity != entity.is_core_entity:
                continue
            all_pair.append((entity.id, sim, engine.get_distance(entity.id, sim)))
    all_pair.sort(key=lambda x: x[2])
    relation_cache = []
    batch_num = 20
    predict_all = sum([1 if pair[2] < threshold else 0 for pair in all_pair])
    tqdm_bar = tqdm.tqdm(total=predict_all)
    for ent1, ent2, new_dis in all_pair:
        if (ent1, ent2) in exists_rel:
            continue
        if new_dis > threshold:
            break
        idx = get_parent(jection, ent1)
        idy = get_parent(jection, ent2)
        if idx == idy:
            continue
        if (idx, idy) in not_equal_pairs:
            continue
        else:
            cnt_all += 1
            # 剪枝
            dist.append(new_dis)
            relation_cache.append((ent1, ent2))
            if len(relation_cache) == batch_num:
                ops = []
                asked_pairs = []
                for e1, e2 in relation_cache:
                    if entity_map[e1].title == entity_map[e2].title:
                        cnt_success += 1
                        idx = get_parent(jection, e1)
                        idy = get_parent(jection, e2)
                        jection[idx] = idy
                        not_equal_pairs = {
                            (jection[id1], jection[id2]) for id1, id2 in not_equal_pairs
                        }
                    else:
                        ops.append(CheckMergeoperation(entity_map[e1], entity_map[e2]))
                        asked_pairs.append((e1, e2))
                response = execute_operator(ops,need_show_progress=False)
                for res, (e1, e2) in zip(response, asked_pairs):
                    if res == None:
                        continue
                    res = CheckMergeoperation.repair(res)
                    idx = get_parent(jection, e1)
                    idy = get_parent(jection, e2)
                    if res == True and (idx, idy) not in not_equal_pairs:
                        cnt_success += 1
                        jection[idx] = idy
                        not_equal_pairs = {
                            (jection[id1], jection[id2]) for id1, id2 in not_equal_pairs
                        }
                    if res == False and idx != idy:
                        not_equal_pairs.add((idx, idy))
                        not_equal_pairs.add((idy, idx))
                logging.info(
                    f"Success:Total {cnt_success} : {cnt_all} ratio :{cnt_success/cnt_all}"
                )
                tqdm_bar.update(batch_num)
                relation_cache = []
            if cnt_all == len(entities):
                break
            exists_rel.add((ent1, ent2))
    id_to_identica = {}
    for ent in entities:
        id = get_parent(jection, ent.id)
        if id_to_identica.get(id) == None:
            id_to_identica[id] = []
            id_to_identica[id].append(ent)
        else:
            id_to_identica[id].append(ent)
    merged_entities = []
    for id, ents in id_to_identica.items():
        merged_entity = ents[0]
        for ent in ents[1:]:
            merged_entity.merge(ent)
        merged_entity.id = id
        merged_entities.append(merged_entity)
    for rel in relations_1 + relations_2:
        if rel.source_id in jection.keys():
            rel.source_id = get_parent(jection, rel.source_id)
        if rel.target_id in jection.keys():
            rel.target_id = get_parent(jection, rel.target_id)
    save_json(os.path.join(graph_structure_path, "entity_related.json"), relations_1)
    save_json(os.path.join(graph_structure_path, "has_entity.json"), relations_2)
    save_json(os.path.join(graph_structure_path, "entity_nodes.json"), merged_entities)
    node_id_map, _ = realloc_id()
    engine.table = {node_id_map.get(k, k): v for k, v in engine.table.items()}
    engine.reverse_table = {v: k for k, v in engine.table.items()}
    engine.save_state(folder_path=folder_path)


def test_search_with(strategy: str, engine_path: str, table_path: str):
    """Target:测试搜索引擎的性能"""
    engine = initialize_entity_engine(engine_path=engine_path, table_path=table_path)
    entities = graph_structure(
        type=[GraphStructureType.entity_node], return_type="object"
    )[0]
    if strategy == "abs-nearest":
        # 5个实体，找5个最近的实体
        dist = []
        for ent in entities:
            sumdis = sum(
                [
                    engine.get_distance(ent.id, ner)
                    for ner in engine.search_by_id(ent.id, 5)
                ]
            )
            dist.append((ent.id, engine.search_by_id(ent.id, 5), sumdis))
        dist.sort(key=lambda x: x[2])
        tosave = [[dis[0], dis[1]] for dis in dist]
        save_json("near_5.json", tosave)
    elif strategy == "abs-furthest":
        pass
    elif strategy == "abs-nearest":
        pass


def print_relation_dis(engine_path: str, table_path: str):
    engine = initialize_entity_engine(engine_path=engine_path, table_path=table_path)
    relations = graph_structure(
        type=[GraphStructureType.entity_related_relation], return_type="object"
    )[0]
    entities = graph_structure(
        type=[GraphStructureType.entity_node], return_type="object"
    )[0]
    entmap = {entity.id: entity for entity in entities}
    diss = []
    for relation in relations:
        diss.append(
            (
                engine.get_distance(relation.source_id, relation.target_id),
                relation.type,
                entmap[relation.source_id].title,
                entmap[relation.target_id].title,
            )
        )
    diss.sort()
    for dis in diss:
        print(dis)


def get_pair_dis(pair_file: str, engine_path: str, table_path: str):
    pair = load_json(pair_file)
    engine = initialize_entity_engine(engine_path=engine_path, table_path=table_path)
    diss = []
    for p in pair:
        diss.append((engine.get_distance(p[0], p[1]), p[0], p[1]))
    average_dis = average([dis[0] for dis in diss])
    print(average_dis)


def identical_merge(
    threshold: float, engine_path: str, table_path: str, folder_path: str, subset: set
):
    """
    等价合并算法函数。
    threshold: 实体对被检查的阈值
    engine_path: 引擎ann路径
    table_path: 引擎表路径
    folder_path: 引擎文件夹路径
    subset: 新加入的实体编号集合

    流程：
    1. 初始化引擎（根据传入的engine_path和table_path）
    2. 执行合并
    3. 重新分配id编号（健壮性）
    4. 更新引擎，存储新的点和边
    """
    engine = initialize_entity_engine(engine_path=engine_path, table_path=table_path)
    entities = graph_structure(
        type=[GraphStructureType.entity_node], return_type="object"
    )[0]
    [relations_2, relations_1] = graph_structure(
        type=[
            GraphStructureType.has_entity_relation,
            GraphStructureType.entity_related_relation,
        ],
        return_type="object",
    )
    exists_rel = {(rel.source_id, rel.target_id) for rel in relations_1}
    entity_map = {entity.id: entity for entity in entities}
    not_equal_pairs = set()
    dist = []
    jection = {ent.id: ent.id for ent in entities}
    cnt_success = 0
    cnt_all = 0
    all_pair = []
    for entity in entities:
        similarity = engine.search_by_id(entity.id, 30)
        for sim in similarity:
            if entity_map[sim].is_core_entity != entity.is_core_entity:
                continue
            if (entity.id in subset and sim in subset) or (
                entity.id not in subset and sim not in subset
            ):
                continue
            all_pair.append((entity.id, sim, engine.get_distance(entity.id, sim)))
    all_pair.sort(key=lambda x: x[2])
    for ent1, ent2, new_dis in all_pair:
        if (ent1, ent2) in exists_rel:
            continue
        if new_dis > threshold:
            break
        else:
            idx = get_parent(jection, ent1)
            idy = get_parent(jection, ent2)
            # 剪枝
            if idx == idy:
                continue
            if (idx, idy) in not_equal_pairs:
                continue

            dist.append(new_dis)
            relation = CheckMergeoperation(entity_map[ent1], entity_map[ent2])
            response = CheckMergeoperation.repair(execute_operator([relation])[0])
            cnt_all += 1
            if response == True:
                jection[idx] = idy
                cnt_success += 1
                not_equal_pairs = {
                    (jection[id1], jection[id2]) for id1, id2 in not_equal_pairs
                }
                print(
                    f"Success:{new_dis} {entity_map[ent1].title} {entity_map[ent2].title}"
                )
            else:
                not_equal_pairs.add((idx, idy))
                not_equal_pairs.add((idy, idx))
                print(
                    f"Fail:{new_dis} {entity_map[ent1].title} {entity_map[ent2].title}"
                )
            print(
                f"Success:Total {cnt_success} : {cnt_all} ratio :{cnt_success/cnt_all}"
            )
            if cnt_all == len(entities):
                break
            exists_rel.add((ent1, ent2))
    id_to_identica = {}
    for ent in entities:
        id = get_parent(jection, ent.id)
        if id_to_identica.get(id) == None:
            id_to_identica[id] = []
            id_to_identica[id].append(ent)
        else:
            id_to_identica[id].append(ent)
    merged_entities = []
    for id, ents in id_to_identica.items():
        merged_entity = ents[0]
        for ent in ents[1:]:
            merged_entity.merge(ent)
        merged_entity.id = id
        merged_entities.append(merged_entity)
    for rel in relations_1 + relations_2:
        if rel.source_id in jection.keys():
            rel.source_id = get_parent(jection, rel.source_id)
        if rel.target_id in jection.keys():
            rel.target_id = get_parent(jection, rel.target_id)
    print(f"Success:{cnt_success}")
    print(f"Total:{cnt_all}")
    print(f"ratio:{cnt_success/cnt_all}")
    save_json(os.path.join(graph_structure_path, "entity_related.json"), relations_1)
    save_json(os.path.join(graph_structure_path, "has_entity.json"), relations_2)
    save_json(os.path.join(graph_structure_path, "entity_nodes.json"), merged_entities)
    node_id_map, _ = realloc_id()
    engine.table = {node_id_map.get(k, k): v for k, v in engine.table.items()}
    engine.reverse_table = {v: k for k, v in engine.table.items()}
    engine.save_state(folder_path=folder_path)
