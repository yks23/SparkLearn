import json

from ...src.model import Section, Relation, Entity
import os
from ...src.config import final_prompt_path
from ...src.utils.id_operation import get_adjacency_matrix

Max_len = 800


class KGoperator:
    prompt_path: str = ""
    # Systemprompt
    user_input: str = ""
    # Userinput
    return_type: str = ""
    # raw or json
    default: str = ""

    # default response
    def __init__(self):
        pass

    def default_response(self):
        return self.default


class Summaryoperator(KGoperator):
    def __init__(
        self,
        section: Section,
        subsections: list[Section] = [],
        system_prompt_path: str = "",
    ):

        self.prompt_path = system_prompt_path
        self.default = section.raw_content
        if section.is_elemental == True:
            self.user_input = (
                "这是用户输入的章节内容的原文，请你根据提示词完成章节总结的任务：\n"
                + section.raw_content
            )
            self.return_type = "json"
            if system_prompt_path == "":
                self.prompt_path = os.path.join(
                    final_prompt_path, "community_report_2.txt"
                )
            else:
                self.prompt_path = system_prompt_path
        else:
            self.user_input = (
                "这是章节的名字：\n" + section.title + "\n以下是它的子章节:\n"
            )
            for subsection in subsections:
                self.user_input += (
                    "子章节名字:\n"
                    + subsection.title
                    + "\n子章节的总结:\n"
                    + subsection.summary
                    + "\n"
                )
            self.user_input += "请你根据提示词完成章节总结的任务"
            if system_prompt_path == "":
                self.prompt_path = os.path.join(
                    final_prompt_path, "community_report_1.txt"
                )
            else:
                self.prompt_path = system_prompt_path
            self.return_type = "raw"


class CheckInOperation(KGoperator):
    def __init__(self, tasks: list[tuple[str, list]], type_: int = 0):
        if type_ == 0:
            self.prompt_path = os.path.join(final_prompt_path, "check_in_prompt.txt")
        elif type_ == 1:
            self.prompt_path = os.path.join(final_prompt_path, "check_in_prompt_1.txt")
        else:
            self.prompt_path = os.path.join(final_prompt_path, "check_in_prompt_2.txt")
        self.default = False
        self.user_input = f"以下是用户的输入：\n"
        for i, (task_name, task_list) in enumerate(tasks):
            self.user_input += f"指定实体{i}:\n{task_name}\n"
            if type_ != 2:
                self.user_input += f"候选实体集合："
                self.user_input += "\n".join(str(task_list))
            else:
                self.user_input += f"候选实体集合："
                for j, task in enumerate(task_list):
                    self.user_input += f"\n{j}:{task}"
        self.return_type = "json"
        self.user_input += "请你根据提示词完成实体等价判断的任务:\n"

    def repair(response: list[bool]):
        for b in response:
            if isinstance(b, bool) == False:
                b = False
        return response


class EntityMessagePassoperator(KGoperator):
    def __init__(
        self,
        core_entity: Entity,
        around_relations: list[Relation],
        around_entitys: list[Entity],
        system_prompt_path: str = "",
    ):
        self.default = core_entity.descriptions[-1]
        self.prompt_path = system_prompt_path
        self.user_input = "这是用户输入的实体和实体之间的关系，请你根据提示词完成实体消息增强的任务：\n"
        self.user_input += f"核心实体：{core_entity.title}\n"
        for relation, entity in zip(around_relations, around_entitys):
            self.user_input += (
                f"相连的实体：\n名称和描述:{entity.title}\n{entity.descriptions[-1]}\n"
            )
        self.return_type = "raw"
        if system_prompt_path == "":
            system_prompt_path = os.path.join(
                final_prompt_path, "inc_entity_augmented_generation.txt"
            )

    def default_response(self):
        return self.default


class RelationMessagePassoperator(KGoperator):
    def __init__(
        self,
        system_prompt_path: str,
        core_relation: Relation,
        source_entity: Entity,
        target_entity: Entity,
    ):
        self.prompt_path = system_prompt_path
        self.default = core_relation.descriptions[-1]
        self.user_input = (
            "这是用户输入的实体和实体之间的关系，请你根据提示词完关系消息增强的任务：\n"
        )
        self.user_input += f"核心关系：\n名称和描述:{core_relation.type}\n{core_relation.descriptions[-1]}\n"
        self.user_input += f"源实体：\n名称和描述:{source_entity.title}\n{source_entity.descriptions[-1]}\n"
        self.user_input += f"目标实体：\n名称和描述:{target_entity.title}\n{target_entity.descriptions[-1]}\n"
        self.return_type = "raw"
        if system_prompt_path == "":
            system_prompt_path = os.path.join(
                final_prompt_path, "relation_augmented_generation.txt"
            )


def get_node_info(node_id, node_dict):
    """获取节点信息"""
    if node_id not in node_dict:
        return f"错误：未找到ID为{node_id}的节点"

    node = node_dict[node_id]
    node_info = ""

    # 使用.get()方法安全地获取字典值
    if node.get("level") is None:
        node_info += f"名称：{node.get('title', '未知')}\n"
        node_info += f"ID：{node_id}\n"
        descriptions = node.get("descriptions", [])
        node_info += f"描述：{descriptions[-1] if descriptions else '无描述'}\n"
    else:
        node_info += f"名称：{node.get('title', '未知')}\n"
        node_info += f"描述：{node.get('summary', '无描述')}\n"
    return node_info


def get_node(node):
    """获取节点信息"""
    node_info = ""
    # 使用.get()方法安全地获取字典值
    node_info += f"名称:{node.title}\n"
    node_info += f"ID:{node.id}\n"
    descriptions = node.descriptions
    node_info += f"描述：{descriptions[-1] if descriptions else '无描述'}\n"
    return node_info


def get_aggreation_input(node_id, near_leaves_ids, node_dict, edge_dict):
    """获取聚合输入"""
    user_input = "中心实体的信息是：" + get_node_info(node_id, node_dict)
    for relation_id in node_dict[node_id]["from_relation"]:
        if edge_dict[relation_id]["source_id"] in near_leaves_ids:
            user_input += (
                "\n"
                + "相邻叶子节点的信息是：\n"
                + get_node_info(edge_dict[relation_id]["source_id"], node_dict)
                + "\n"
                + "两者的关系是:\n"
                + edge_dict[relation_id]["descriptions"][-1]
            )
    for relation_id in node_dict[node_id]["to_relation"]:
        print(edge_dict[relation_id]["type"], relation_id)
        if edge_dict[relation_id]["target_id"] in near_leaves_ids:
            user_input += (
                "\n"
                + "相邻叶子节点的信息是：\n"
                + get_node_info(edge_dict[relation_id]["target_id"], node_dict)
                + "\n"
                + "两者的关系是:\n"
                + edge_dict[relation_id]["descriptions"][-1]
            )
    section_id = 0
    for relation_id in node_dict[node_id]["from_relation"]:
        if edge_dict[relation_id]["type"] == "has_entity":
            section_id = edge_dict[relation_id]["source_id"]
            break
    user_input += (
        "\n"
        + "章节的信息是：\n"
        + get_node_info(section_id, node_dict)
        + "\n请根据以上信息和提示词要求，完成实体聚合的任务"
    )
    return user_input


class Aggregationoperation(KGoperator):
    def __init__(
        self,
        core_entity: Entity,
        around_relations: list[Relation],
        around_entitys: list[Entity],
        system_prompt_path: str = "",
    ):
        self.prompt_path = system_prompt_path
        default_dict = {}
        default_dict["aggregation"] = {
            "id": core_entity.id,
            "name": core_entity.title,
            "alias": core_entity.alias,
            "type": core_entity.type,
            "raw_content": core_entity.descriptions[-1],
            "desciption": core_entity.descriptions[-1],
        }
        default_dict["near_leaves"] = [ent.id for ent in around_entitys]
        self.default = json.dumps(default_dict)
        self.user_input = "以下是用户的输入：\n中心实体的信息是：" + get_node_info(
            core_entity, around_entitys
        )
        for relation, entity in zip(around_relations, around_entitys):
            self.user_input += (
                "\n"
                + "相邻叶子节点的信息是：\n"
                + get_node_info(core_entity)
                + "\n"
                + "两者的关系是:\n"
                + relation.type
            )
        self.user_input += "请根据提示词，完成实体聚合的任务"
        self.return_type = "json"
        if system_prompt_path == "":
            system_prompt_path = os.path.join(
                final_prompt_path, "aggreation_prompt.txt"
            )


class RelationUpdateoperation(KGoperator):
    def __init__(
        self, src_entity: Entity, tar_entity: Entity, system_prompt_path: str = ""
    ):
        self.default = ""
        if system_prompt_path == "":
            self.prompt_path = os.path.join(
                final_prompt_path, "relation_detection_prompt.txt"
            )
        else:
            self.prompt_path = system_prompt_path
        self.src_entity = src_entity
        self.tar_entity = tar_entity
        self.user_input = (
            "以下是用户的输入：\n源实体的信息是:\n"
            + get_node(src_entity)
            + "目标实体的信息是：\n"
            + get_node(tar_entity)
            + "请你根据提示词，完成关系的提取"
        )
        self.return_type = "raw"


class AugmentationOperation(KGoperator):
    def __init__(
        self,
        core_entity: Entity,
        near_relations: list[Relation],
        near_entities: list[Entity],
        system_prompt_path: str = "",
    ):
        self.default = core_entity.descriptions[-1]
        self.prompt_path = system_prompt_path
        self.user_input = "以下是用户的输入：\n"
        self.user_input += "实体的名称是：\n"
        self.user_input += core_entity.title
        self.core_id = core_entity.id
        for relation, entity in zip(near_relations, near_entities):
            self.user_input += "相邻实体名称：\n"
            self.user_input += entity.title
            self.user_input += "联系\n"
            self.user_input += relation.descriptions[-1]
        self.user_input += "请根据提示词，完成实体增强的任务"
        self.return_type = "raw"
        if system_prompt_path == "":
            self.prompt_path = os.path.join(
                final_prompt_path, "inc_entity_augmented_generation.txt"
            )


class RelationPredictoperation(KGoperator):
    def __init__(
        self, src_entity: Entity, tar_entity: Entity, system_prompt_path: str = ""
    ):
        self.default = r"{\"is_relevant\": false}"
        self.src_entity = src_entity
        self.tar_entity = tar_entity
        if system_prompt_path == "":
            self.prompt_path = os.path.join(
                final_prompt_path, "relation_predict_prompt.txt"
            )
        else:
            self.prompt_path = system_prompt_path
        self.user_input = (
            "以下是用户的输入：\n源实体的信息是:\n"
            + get_node(src_entity)
            + "目标实体的信息是：\n"
            + get_node(tar_entity)
            + "请你根据提示词，完成关系的预测"
        )
        self.return_type = "json"

    def get_strength(response: dict):
        if response.get("is_relevant", False) == False:
            return 0
        return response.get("strength", 0)

    def get_relation(self, id, response: dict):
        try:
            return Relation(
                id,
                summary="",
                descriptions=[response["description"]],
                source_id=self.src_entity.id,
                target_id=self.tar_entity.id,
                type=response["type"],
            )
        except:
            return None


class RelationStrengthoperation(KGoperator):
    def __init__(
        self, src_entity: Entity, tar_entity: Entity, system_prompt_path: str = ""
    ):
        self.default = r"{\"is_relevant\": false}"
        self.src_entity = src_entity
        self.tar_entity = tar_entity
        if system_prompt_path == "":
            self.prompt_path = os.path.join(
                final_prompt_path, "strength_eval_prompt.txt"
            )
        else:
            self.prompt_path = system_prompt_path
        self.user_input = (
            "以下是用户的输入：\n源实体的信息是:\n"
            + get_node(src_entity)
            + "目标实体的信息是：\n"
            + get_node(tar_entity)
            + "请你根据提示词，完成关系的强度的判断"
        )
        self.return_type = "json"

    def get_strength(response: dict):
        try:
            return response["strength"] / 10.0
        except:
            return 0.2


class CheckMergeoperation(KGoperator):
    """用户输入一些实体，判断是否需要合并。返回一个json列表，包含这些实体中需要合并的实体id列表"""

    def __init__(
        self, entity_1: Entity, entity_2: Entity, system_prompt_path: str = ""
    ):
        self.prompt_path = system_prompt_path
        if system_prompt_path == "":
            self.prompt_path = os.path.join(
                final_prompt_path, "check_identical_prompt.txt"
            )
        self.id1 = entity_1.id
        self.id2 = entity_2.id
        self.user_input = "以下是用户的输入：\n"
        self.user_input += "- 实体1名称：\n" + entity_1.title + "\n"
        self.user_input += "  实体1描述：\n" + entity_1.descriptions[-1] + "\n"
        self.user_input += "  实体2名称：\n" + entity_2.title + "\n"
        self.user_input += "- 实体2描述：\n" + entity_2.descriptions[-1] + "\n"
        self.user_input += "请你根据提示词，完成合并的判断"
        self.return_type = "json"

    def repair(response: dict):
        try:
            return response["is_identical"]
        except:
            return False


class EmbeddingEntityoperation(KGoperator):
    """将实体的名称和描述进行向量化，返回一个向量"""

    def __init__(self, entities: list[Entity], level: int = 0):
        self.prompt_path = None
        self.user_input = [
            entity.title
            + "\n"
            + (
                entity.descriptions[level]
                if level < len(entity.descriptions)
                else entity.descriptions[-1]
            )
            for entity in entities
        ]

        for i in range(len(self.user_input)):
            if len(self.user_input[i]) > Max_len:
                self.user_input[i] = self.user_input[i][:Max_len]
        self.return_type = "raw"
        self.default = [0.0] * 2048


class Embeddingstroperation(KGoperator):
    """将实体的名称和描述进行向量化，返回一个向量"""

    def __init__(self, input: list[str]):
        self.prompt_path = None
        self.user_input = input
        for i in range(len(self.user_input)):
            if len(self.user_input[i]) > Max_len:
                self.user_input[i] = self.user_input[i][:Max_len]
        self.return_type = "raw"
        self.default = [0.0] * 2048


class EmbeddingSectionoperation(KGoperator):
    """将章节的名称和描述进行向量化，返回一个向量"""

    def __init__(self, sections: list[Section]):
        self.prompt_path = None
        self.user_input = [
            section.title + "\n" + section.summary for section in sections
        ]
        for i in range(len(self.user_input)):
            if len(self.user_input[i]) > Max_len:
                self.user_input[i] = self.user_input[i][:Max_len]
        self.return_type = "raw"
        self.default = [0.0] * 2048


class RelationExtractionoperation(KGoperator):
    """从用户输入的Section之间的关系中提取关系"""

    def __init__(
        self, section_summary: str, entities: list[Section], system_prompt_path: str
    ):
        self.prompt_path = system_prompt_path
        self.return_type = "json"
        if len(section_summary):
            self.user_input = "章节的概括是：\n" + section_summary + "\n"
        self.user_input += "以下是用户输入的子章节：\n"
        self.default = json.dumps({"relations": []})
        if isinstance(entities[0], str):
            self.user_input += entities[0]
        else:
            for ent in entities:
                self.user_input += (
                    "实体名称和id是：\n" + ent.title + "\n" + str(ent.id) + "\n"
                )
                if len(ent.summary):
                    self.user_input += "实体的概括是:\n"
                    self.user_input += ent.summary
                    self.user_input += "\n"
                else:
                    self.user_input += "实体没有描述信息\n"
        self.user_input += "请根据提示词，完成关系的提取"
        if system_prompt_path == "":
            system_prompt_path = os.path.join(
                final_prompt_path, "section_rel_extract.txt"
            )

    @staticmethod
    def get_relation_from_response(response: dict):
        print(response)
        """从response中提取关系 Tuple(source_id,target_id,relation_decription)"""
        try:
            return Relation(
                id=int(response["id"]),
                source_id=int(response["source"]),
                target_id=int(response["target"]),
                type=response["type"],
                descriptions=[response["raw_content"]],
            )
        except:
            return None


class EntityevalOperation(KGoperator):
    """判断实体的质量"""

    def __init__(
        self,
        target_field: str,
        section: Section,
        entitis: list[Entity],
        system_prompt_path: str = "",
        level: int = 0,
    ):
        self.default = r"{\"relevance\": 5,\n\"completency\": 5,\n\"id\": -1}"
        self.entitis = entitis
        if system_prompt_path == "":
            self.prompt_path = os.path.join(final_prompt_path, "evaluate_entity.txt")
        else:
            self.prompt_path = system_prompt_path
        self.user_input = (
            "以下是用户的输入：\n"
            + "知识领域是："
            + target_field
            + "\n"
            + "章节概述是："
            + section.summary
            + "\n"
            + "输入实体和描述：\n"
        )
        for entity in entitis:
            self.user_input += (
                "实体id:"
                + str(entity.id)
                + "\n"
                + "实体名称:"
                + entity.title
                + "\n"
                + "实体描述:"
                + entity.descriptions[level]
                if len(entity.descriptions) > level
                else entity.descriptions[-1] + "\n"
            )
        self.return_type = "json"


class RelevanceOperation(KGoperator):
    """判断实体的质量"""

    def __init__(
        self,
        target_field: str,
        entitis: list[str],
    ):
        self.default = r"[]"
        self.entitis = entitis
        self.prompt_path = os.path.join(
            final_prompt_path, "evaluate_entity_relevance.txt"
        )
        self.user_input = (
            "以下是用户的输入：\n"
            + "知识领域是："
            + target_field
            + "\n"
            + "输入实体描述是：\n"
        )
        for i, entity in enumerate(entitis):
            self.user_input += f"实体{i}描述:" + entity + "\n"
        self.return_type = "json"

    @staticmethod
    def repair(response: list[int]):
        if not isinstance(response, list):
            response = []
        return response


class RelationEvalOperation(KGoperator):
    """判断关系的质量"""

    def __init__(
        self,
        tripples: list[tuple[str, str, str]],
    ):
        self.default = r"[]"
        self.tripples = tripples
        self.prompt_path = os.path.join(final_prompt_path, "evaluate_relation_test.txt")
        self.user_input = "以下是用户的输入：\n"
        for i, rel in enumerate(tripples):
            self.user_input += f"第{i}个输入的关系:\n"
            self.user_input += (
                "源实体:"
                + rel[0]
                + "\n"
                + "关系描述:"
                + rel[1]
                + "\n"
                + "目标实体:"
                + rel[2]
                + "\n"
            )
        self.user_input += "请你根据提示词，完成关系逻辑性和完整度的打分的判断"
        self.return_type = "json"


class RelationevalOperation(KGoperator):
    """判定关系的质量"""

    def __init__(
        self,
        src_entity: Entity,
        relations: list[Relation],
        target_entity: list[Entity],
        system_prompt_path: str = "",
        level: int = 0,
    ):
        self.default = r"{\"logic\": 5,\n\"completency\": 5,\n\"id\": -1}"
        self.relation = relations
        if system_prompt_path == "":
            self.prompt_path = os.path.join(final_prompt_path, "evaluate_relation.txt")
        else:
            self.prompt_path = system_prompt_path
        self.user_input = (
            "以下是用户的输入：\n" + "源实体名称:\n" + src_entity.title + "\n"
        )

        for rel, ent in zip(relations, target_entity):
            self.user_input += (
                "关系id:"
                + str(rel.id)
                + "\n"
                + "目标实体名称:"
                + ent.title
                + "\n"
                + "关系名称:"
                + rel.type
                + "\n"
                + "关系描述:"
                + rel.descriptions[level]
                if len(rel.descriptions) > level
                else rel.descriptions[-1] + "\n"
            )

        self.user_input += "请你根据提示词，完成关系逻辑性和完整度的打分的判断"
        self.return_type = "json"

    @staticmethod
    def repair(response: list[dict]):
        res = []
        for r in response:
            try:
                res.append(
                    (
                        int(r["id"]),
                        int(r["logic"]),
                        int(r["completency"]),
                        int(r["novelty"]),
                    )
                )
            except:
                res.append((-1, 5, 5, 5))
        if len(res) == 0:
            res.append((-1, 5, 5, 5))
        return res


class AggregationOperation(KGoperator):
    """实体聚合"""

    def __init__(
        self,
        core_entity: Entity,
        near_leaves: list[Entity],
        system_prompt_path: str = "",
    ):
        self.default = None
        self.core_entity = core_entity
        self.near_leaves = near_leaves
        self.user_input = (
            "以下是用户的输入：\n"
            + "中心实体名称是："
            + core_entity.title
            + "\n"
            + "中心实体描述是："
            + core_entity.descriptions[-1]
            + "\n"
            + "相邻叶子节点的信息是：\n"
        )
        for near_ent in near_leaves:
            self.user_input += (
                "实体id:"
                + str(near_ent.id)
                + "\n"
                + "实体名称:"
                + near_ent.title
                + "\n"
                + "实体描述:"
                + near_ent.descriptions[0]
                + "\n"
            )
        self.user_input += "请根据提示词，完成实体聚合的任务"

    def repair(self, response: dict):
        try:
            return response["aggregation"], response["reserved"]
        except:
            return self.core_entity, [ent.id for ent in self.near_leaves]


class LocalityRoleOperation(KGoperator):
    """实体局部作用检测"""

    def __init__(
        self,
        core_entity: Entity,
        entities: list[Entity],
        system_prompt_path: str = "",
    ):
        self.default = ""
        self.core_entity = core_entity
        self.user_input = (
            "以下是用户的输入：\n"
            + "待判断实体名称是："
            + core_entity.title
            + "\n"
            + "待判断实体描述是："
            + core_entity.descriptions[-1].split("### 局部作用")[0]
            + "\n"
            + "相邻节点的信息是：\n"
        )
        near_leaves = []
        adj_matrix = get_adjacency_matrix()
        for ent in entities:
            if (core_entity.id, ent.id) in adj_matrix:
                near_leaves.append(ent)
        for near_ent in near_leaves:
            self.user_input += (
                "实体id:"
                + str(near_ent.id)
                + "\n"
                + "实体名称:"
                + near_ent.title
                + "\n"
                + "实体描述:"
                + near_ent.descriptions[-1].split("### 局部作用")[0]
                + "\n"
            )
        self.user_input += "请根据提示词，完成实体局部作用检测的任务"
        self.prompt_path = system_prompt_path
        self.return_type = "json"
        if system_prompt_path == "":
            self.prompt_path = os.path.join(final_prompt_path, "locality_role.txt")

    def repair(self, response: dict):
        try:
            return response["is_core_entity"]
        except:
            return True
