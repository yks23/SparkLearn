import os
from multiprocessing import freeze_support
import logging

logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    datefmt="%Y-%m-%d %H:%M:%S",  # 设置时间格式
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("faiss").setLevel(logging.WARNING)
if __name__ == "__main__":
    freeze_support()
    os.environ["textbook"] = "psychology"
    from src.utils.process_manager import ProcessManager
    manager = ProcessManager(state_path = './state.json')
    manager.execute()