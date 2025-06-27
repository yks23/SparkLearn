from .tree_visualize import tree_visualization
from src.utils.asset import save_to_excel
from src.config import graph_structure_path
import asyncio,os
def visualize():
    asyncio.run(tree_visualization())
    save_to_excel(graph_structure_path,os.path.join(graph_structure_path,'graph.xlsx'),0)