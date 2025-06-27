from dataclasses import dataclass,field

@dataclass
class Section:
    # The section class is a dataclass to restore a section according to raw document
    id: int=0
    title: str=""
    summary: str=""
    example: dict= field(default_factory=dict)
    to_relation:list[int] = field(default_factory=list)# 指向其它节点的relation
    from_relation:list[int] = field(default_factory=list)# 从其它节点指向该节点的relation
    level: int=0
    is_elemental:bool=False
    raw_content: str=""
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "example": self.example,
            "to_relation": self.to_relation,
            "from_relation": self.from_relation,
            "level": self.level,
            "raw_content": self.raw_content,
            "is_elemental":self.is_elemental
        }
