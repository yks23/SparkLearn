from dataclasses import dataclass,field

@dataclass
class Relation:
    id: int=0
    summary: str=""
    descriptions: list[str]= field(default_factory=list)
    type: str=""
    source_id: int=0
    target_id: int=0
    is_tree:bool=False
    finish_augment:bool=False
    def to_dict(self):
        return {
            "id": self.id,
            "summary": self.summary,
            "descriptions": self.descriptions,
            "type": self.type,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "is_tree": self.is_tree
        }