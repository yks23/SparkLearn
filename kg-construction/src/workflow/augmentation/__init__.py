from .augmented_generation import augmented_generation
from .transportation import get_local_role

from .relation_predict import identical_predict,connection_predict
from .continue_iteration import continue_iteration
import os
from src.config import engine_cache_path
from src.utils.id_operation import realloc_id
def augmentation():
    augmented_generation(True,False,True) # 增强实体
    augmented_generation(False,True,True) # 增强边
    get_local_role(need_ask=False)# 默认不使用LLM进行判断
    identical_predict(0.55,engine_path=os.path.join(engine_cache_path,"engine.ann"),table_path=os.path.join(engine_cache_path,"table.json"),folder_path=engine_cache_path)
    # realloc_id()
    connection_predict(5)
    # realloc_id()
    # continue_iteration()
    # realloc_id()