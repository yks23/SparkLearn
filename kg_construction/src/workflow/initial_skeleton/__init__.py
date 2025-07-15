from .community_report import community_report
from .entity_extraction import entity_extraction
from .documents_to_section import documents_to_sections
from ....src.utils.id_operation import realloc_id
import os
from ....src.config import graph_structure_path,engine_cache_path,request_cache_path
def skeleton_initialization():
    if not os.path.exists(graph_structure_path):
        os.makedirs(graph_structure_path)
    if not os.path.exists(engine_cache_path):
        os.makedirs(engine_cache_path)
    if not os.path.exists(request_cache_path):
        os.makedirs(request_cache_path)
    documents_to_sections()    
    realloc_id()
    community_report()
    realloc_id()
    entity_extraction()
    realloc_id()