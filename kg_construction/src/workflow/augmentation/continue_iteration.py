
from .relation_predict import continue_predict as predict

def continue_iteration(
    threshold:float=5,
    dist:int=0,
):
    """
    继续迭代，直到没有新的节点被添加为止。
    :param threshold: 置信度阈值
    :param dist: 距离
    """    
    predict(threshold,dist)

    
    
    
    
