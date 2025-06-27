from dataclasses import dataclass,field
@dataclass
class Example:
    id: int=0
    title: str=""
    content: str= ""
    to_relation:list[int] = field(default_factory=list)# 指向其它节点的relation
    from_relation:list[int] = field(default_factory=list)# 从其它节点指向该节点的relation
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "to_relation": self.to_relation,
            "from_relation": self.from_relation,
        }
