import argparse
import os
import multiprocessing
from  pre_process.text_recognize.processtext import process_input
from sider.annotator_simple import SimplifiedAnnotator
from qg.graph_class import KnowledgeGraph,KnowledgeQuestionGenerator
from config import APPID,APISecret,APIKEY
def parse_args():
    parser = argparse.ArgumentParser(description="EduSpark CLI Tool")
    parser.add_argument('--file_path', type=str, required=True, help='Input file or directory path')
    parser.add_argument('--output_path', type=str, default='./outputs', help='Output directory path')
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
        annotator = SimplifiedAnnotator()
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        annotator.process(content, input_path)  # 覆盖原文件 
    else:
        sub_folders = os.listdir(input_path)
        for sub_folder in sub_folders:
            sub_folder_path = os.path.join(input_path, sub_folder)
            augment_folder(sub_folder_path)

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
    generator = KnowledgeQuestionGenerator(
        kg,
        appid=APPID,
        api_key=APIKEY,
        api_secret=APISecret
    )
    generator.generate_and_save(output_path=output_path)
    
def main(args):
    # 首先处理原始文件
    
    # 复制目录结构
    file_path = args.file_path
    output_path = args.output_path
    process_folder(file_path,output_path) # 处理之后，形成了目录结构，然后最下面的叶节点就是.md格式
    
    augment_folder(os.path.join(output_path,'processed'))  # 假设处理后的文件在processed目录下,逐个文件增广
    
    tree_folder(os.path.join(output_path,'processed'),os.path.join(output_path,'tree'))  # 假设增广后的文件在processed目录下,生成树形结构到tree目录下
    
    generate_QA(os.path.join(output_path,'tree','graph'),os.path.join(output_path,'qa'))  # 假设树形结构在tree目录下,生成问答对到qa目录下
    
    
if __name__ == "__main__":
    multiprocessing.freeze_support()  # 支持Windows下的多进程
    args = parse_args()
    main(args)