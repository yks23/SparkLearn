import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from sider.annotator_simple import SimplifiedAnnotator
from sider.annotator import Annotator
if __name__ == "__main__":
    # 读入一个md文档，用的是pre-process里面的一个md文件
    with open("pre-process/text_recognize/example_output/wangyuan_output.md", "r", encoding="utf-8") as f:
        content = f.read()
    # annotator_simple.py使用示例
    print("===============annotator_simple.py使用示例===============")
    annotator = SimplifiedAnnotator()
    annotator.process(content, "./sider/annotated_document_simp.md")
    
    # annotator.py 使用示例
    print("===============annotator.py 使用示例===============")
    annotator = Annotator(use_llm_for_structure=True)  #这里可以选择用大模型/本地算法对文章进行分段，但是本地算法效果非常不好
    annotator.process(content, "./sider/annotated_document.md")
