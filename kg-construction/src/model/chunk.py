from dataclasses import dataclass,field
@dataclass
class Chunk:
    id: int=0
    raw_content: str=""
    to_relation:list[int] = field(default_factory=list)# 指向其它节点的relation
    from_relation:list[int] = field(default_factory=list)# 从其它节点指向该节点的relation
    def to_dict(self):
        return {
            "id": self.id,
            "raw_content": self.raw_content,
            "to_relation": self.to_relation,
            "from_relation": self.from_relation,
        }
