from enum import Enum
class GraphStructureType(Enum):
    section_belong_connection:int = 1
    section_related_connection:int = 2
    section_all_relation:int = 3
    has_entity_relation:int = 4
    entity_related_relation:int = 5
    section_node:int = 6
    entity_node:int = 7
    all_node:int = 8
    all_relation:int = 9
    adjacency_matrix:int = 10
    