import os

def get_project_root():
    """
    获取项目根目录，兼容WebUI和独立运行场景
    
    Returns:
        str: 项目根目录的绝对路径
    """
    current_file = os.path.abspath(__file__)
    
    # 检查是否在WebUI环境中运行
    if 'SparkLearn-WebUI' in current_file:
        # 在WebUI环境中，需要找到SparkLearn子模块的根目录
        parts = current_file.split(os.sep)
        try:
            # 找到SparkLearn-WebUI的位置
            webui_index = parts.index('SparkLearn-WebUI')
            # 构建SparkLearn子模块的根路径
            sparklearn_root = os.sep.join(parts[:webui_index + 1] + ['submodule', 'SparkLearn'])
            return sparklearn_root
        except ValueError:
            pass
    
    # 独立运行场景，使用当前文件的相对路径
    # 从 utils/path_resolver.py 向上三级到 kg_construction
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))

def get_prompt_path():
    """
    获取prompt文件的路径
    
    Returns:
        str: prompt目录的绝对路径
    """
    project_root = get_project_root()
    return os.path.join(project_root, "kg_construction", "prompt", "prompt")

def resolve_path(relative_path):
    """
    解析相对路径为绝对路径
    
    Args:
        relative_path (str): 相对于项目根目录的路径
        
    Returns:
        str: 绝对路径
    """
    project_root = get_project_root()
    return os.path.join(project_root, relative_path)
