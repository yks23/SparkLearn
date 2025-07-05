from dataclasses import dataclass, field

@dataclass
class Entity:
    id: int = 0
    title: str = ""
    summary: str = ""
    descriptions: list[str] = field(default_factory=list)
    to_relation: list[int] = field(default_factory=list)  # 指向其它节点的relation
    from_relation: list[int] = field(
        default_factory=list
    )  # 从其它节点指向该节点的relation
    type: str = ""
    section: str = ""
    alias: list[str] = field(default_factory=list)
    is_core_entity: bool = True
    finish_augment: bool = False
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "descriptions": self.descriptions,
            "to_relation": self.to_relation,
            "from_relation": self.from_relation,
            "type": self.type,
            "section": self.section,
            "alias": self.alias,
            "is_core_entity": self.is_core_entity
        }

    @staticmethod
    def split_description(description: str):
        dic = {}
        split = description.split("##")
        dic["title"] = split[1]
        dic["infomation"] = split[2]
        dic["local"] = split[3]
        return dic

    def merge(self, newentity):
        self.descriptions.extend(newentity.descriptions)
        # 将description中最长的部分保留下来，升序排列
        self.descriptions.sort(key=lambda x: len(x))
        # 将to_relation和from_relation合并
        self.to_relation.extend(newentity.to_relation)
        self.from_relation.extend(newentity.from_relation)
        self.alias.extend(list(set(newentity.alias + [newentity.title])))
        self.is_core_entity = self.is_core_entity or newentity.is_core_entity
