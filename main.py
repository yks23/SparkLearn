import argparse
import os
import multiprocessing
from  pre_process.text_recognize.processtext import process_input
from sider.annotator_simple import SimplifiedAnnotator
from qg.graph_class import KnowledgeGraph,KnowledgeQuestionGenerator
import json
def parse_args():
    parser = argparse.ArgumentParser(description="EduSpark CLI Tool")
    parser.add_argument('--file_path', type=str, required=True, help='Input file or directory path')
    parser.add_argument('--output_path', type=str, default='./outputs', help='Output directory path')
    parser.add_argument('--state_path', type=str, default='./state.json', help='Path to save the state file')
    return parser.parse_args()

def process_folder(input_path, output_path):
    if not os.path.isdir(input_path):
        process_input(input_path, output_path)
    else:
        sub_folders = os.listdir(input_path)
        new_output_path = os.path.join(output_path, os.path.basename(input_path))
        os.makedirs(new_output_path, exist_ok=True)
        for sub_folder in sub_folders:
            sub_folder_path = os.path.join(input_path, sub_folder)
            process_folder(sub_folder_path, new_output_path)


def augment_folder(input_path):
    if not os.path.isdir(input_path):
        # 只处理后缀为 .md 的文件
        if input_path.lower().endswith(".md"):
            try:
                annotator = SimplifiedAnnotator()
                with open(input_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                annotator.process(content, input_path)  # 覆盖原文件
            except Exception as e:
                print(f"⚠️ 处理文件失败：{input_path}，错误：{e}")
        else:
            print(f"⏩ 跳过非 .md 文件：{input_path}")
    else:
        for sub_name in os.listdir(input_path):
            sub_path = os.path.join(input_path, sub_name)
            augment_folder(sub_path)


def tree_folder(input_path,output_path):
    os.environ['meta_path'] = output_path  # 设置环境变量
    os.environ['raw_path'] = input_path  # 设置原始数据路径
    from kg_construction.main import main
    main()

def generate_QA(input_path, output_path):
    """
    生成问答对
    """
    kg = KnowledgeGraph()
    kg.load_knowledge_graph(input_path)
    print(f"加载知识图谱: {input_path}")
    kg.visualize(os.path.join(input_path,'graph.png'))
    generator = KnowledgeQuestionGenerator(
        kg,
        appid="2d1bc910",
        api_key="a1df9334fd048ded0c9304ccf12c20d1",
        api_secret="YzZjODMwNmNjNmRiMDVjOGI4MjcxZDVi"
    )
    generator.interactive_question_generation()
    
def main(args):
    # 首先处理原始文件
    # 复制目录结构
    file_path = args.file_path
    output_path = args.output_path
    processed_path  = os.path.join(output_path, os.path.basename(file_path))
    
    
    if os.path.exists(os.path.join(output_path, args.state_path)):
        with open(os.path.join(output_path, args.state_path), 'r') as f:
            print(f"初始化状态文件: {os.path.join(output_path, args.state_path)}")
            try:
                state_file = json.load(f) 
            except:
                state_file = {}
    else:
        state_file = {}
    if state_file.get('preprocess',False):
        print("已处理过，跳过预处理")
    else:
        process_folder(file_path,output_path) # 处理之后，形成了目录结构，然后最下面的叶节点就是.md格式
        state_file['preprocess'] = True
        with open(os.path.join(output_path, args.state_path), 'w') as f:
            json.dump(state_file, f, indent=4)
    
    if state_file.get('augment',False):
        print("已增广过，跳过增广")
    else:
        augment_folder(processed_path)  # 假设处理后的文件在processed目录下,逐个文件增广
        state_file['augment'] = True
        with open(os.path.join(output_path, args.state_path), 'w') as f:
            json.dump(state_file, f, indent=4)
            
    if state_file.get('tree',False):
        print("已生成树形结构，跳过")
    else:
        tree_folder(processed_path,os.path.join(output_path,'tree'))  # 假设增广后的文件在processed目录下,生成树形结构到tree目录下
        state_file['tree'] = True
        with open(os.path.join(output_path, args.state_path), 'w') as f:
            json.dump(state_file, f, indent=4)
            
    if state_file.get('qa',False):
        print("已生成问答对，跳过")
    else:
        generate_QA(os.path.join(output_path,'tree','graph'),os.path.join(output_path,'qa'))  # 假设树形结构在tree目录下,生成问答对到qa目录下
        state_file['qa'] = True
        with open(os.path.join(output_path, args.state_path), 'w') as f:
            json.dump(state_file, f, indent=4)
    
    
if __name__ == "__main__":
    
    multiprocessing.freeze_support()  # 支持Windows下的多进程
    args = parse_args()
    main(args)
    
"""
命令行运行：
python main.py --file_path ./网原 --output_path ./outputs --state_path state.json
即可
现有结果在./outputs目录下
- /outputs/网原:preprocess处理后的目录结构
- /outputs/网原/tree: 生成的树形结构
    - /outputs/网原/tree/graph/graph.png: 生成的知识图谱可视化
- /outputs/网原/qa: 生成的问答对


支持断点恢复。
file_path可以是单个文件，也可以是目录，目录下的所有文件都会被处理。
output_path是输出目录，处理后的文件会保存在该目录下。
state_path是状态文件路径，用于记录处理状态，支持断点续传。保留在output_path/state_path下
"""