# 在导入matplotlib之前设置后端，避免GUI线程问题
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
# 设置环境变量，避免Qt冲突
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

import networkx as nx
from typing import Dict, List, Tuple
import json
import _thread as thread
import base64
import hashlib
import hmac
from urllib.parse import urlparse, urlencode
from datetime import datetime
from time import mktime
from wsgiref.handlers import format_date_time
import os
import ssl
from tqdm import tqdm
import time
import matplotlib.pyplot as plt
import websocket
import random

import matplotlib.font_manager as fm

import sys
from pathlib import Path

# 获取当前脚本的绝对路径，并找到 utils 所在的目录（假设和当前脚本的父目录平级）
current_dir = Path(__file__).parent  # 当前脚本所在目录
project_root = current_dir.parent    # 上级目录（和 utils 平级）
utils_path = project_root / "utils"  # utils 的绝对路径

# 添加到 Python 路径
sys.path.append(str(utils_path))

# 现在可以直接导入
from utils.api import (
    single_conversation,
    multi_conservation,
    single_embedding,
    multi_embedding,
    multiroundConversation,
)
import multiprocessing as mp

class KnowledgeGraph:
    def __init__(self):
        """初始化知识图谱结构"""
        self.graph = nx.DiGraph()  # 使用有向图
        self.question_templates = {
            'definition': "请解释{concept}的核心概念",
            'relation': "{source}和{target}之间的关系主要体现在哪些方面？",
            'application': "如何运用{concept}解决实际问题？"
        }

    def load_knowledge_graph(self, graph_file_path: str = './demo_kg/graph'):
        """加载知识图谱（带进度显示）"""
        print("🔍 开始加载知识图谱...")
        start_time = time.time()
        
        nodes_path = os.path.join(graph_file_path ,"all_node.json")
        edges_path = os.path.join(graph_file_path , "all_relations.json")
        
        # 加载节点
        print(f"📂 正在加载节点文件: {nodes_path}")
        with open(nodes_path, 'r', encoding='utf-8') as f:
            nodes = json.load(f)
        print(f"✅ 已加载 {len(nodes)} 个节点")
        
        # 加载边
        print(f"📂 正在加载边文件: {edges_path}")
        with open(edges_path, 'r', encoding='utf-8') as f:
            edges = json.load(f)
        print(f"✅ 已加载 {len(edges)} 条边")
        
        # 处理节点（带进度条）
        print("\n🛠️ 正在构建知识节点...")
        id_to_name = {}
        for node in tqdm(nodes, desc="处理节点"):
            id_to_name[node['id']] = node['title']
            description = node['summary'] if 'summary' in node else node['descriptions'][-1]
            self.graph.add_node(node['title'], description=description)
        
        # 处理边（带进度条）
        print("\n🛠️ 正在构建知识关系...")
        for edge in tqdm(edges, desc="处理边"):
            source = id_to_name[edge['source_id']]
            target = id_to_name[edge['target_id']]
            if 'has' in edge['type']:
                edge['type'] = '关联' 
            rel_type = edge['type'] + edge['descriptions'][-1] if edge['descriptions'] else edge['type']
            
            self.graph.add_edge(source, target, short=edge['type'], type=rel_type,weight=edge.get('weight', 1.0))
        
        print(f"\n🎉 知识图谱加载完成! 共 {len(nodes)} 节点, {len(edges)} 边, 耗时 {time.time()-start_time:.2f} 秒")



    def visualize(self, output_path: str = "knowledge_graph.png", max_nodes: int = 200):
        """
        可视化当前知识图谱，并导出为 PNG 图片（支持中文）。
        :param output_path: 输出图片路径
        :param max_nodes: 最多可视化的节点数，避免大图过于拥挤
        """
        print(f"\n🖼️ 开始可视化知识图谱（最多显示 {max_nodes} 个节点）...")

        # 设置支持中文的字体
        import platform
        try:
            if platform.system() == 'Windows':
                font_path = 'C:/Windows/Fonts/simhei.ttf'
            elif platform.system() == 'Darwin':  # macOS
                font_path = '/System/Library/Fonts/STHeiti Medium.ttc'
            else:  # Linux
                font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            
            zh_font = fm.FontProperties(fname=font_path)
            print(f"✅ 找到中文字体: {font_path}")
            font_name = zh_font.get_name()
        except Exception as e:
            print(f"⚠️ 未找到中文字体: {e}")
            zh_font = None
            font_name = 'sans-serif'

        # 限制可视化规模
        subgraph = self.graph.copy()
        if len(subgraph.nodes) > max_nodes:
            nodes_subset = list(subgraph.nodes)[:max_nodes]
            subgraph = subgraph.subgraph(nodes_subset)

        try:
            # 直接使用matplotlib生成图片
            plt.figure(figsize=(12, 8))
            pos = nx.kamada_kawai_layout(subgraph)
            
            # 绘制节点和边
            nx.draw(subgraph, pos, with_labels=True, 
                   node_color="skyblue", edge_color="gray",
                   node_size=2000, font_size=10, 
                   font_family=font_name, arrows=True)
            
            plt.axis('off')
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close('all')
            
            print(f"✅ 可视化完成，图片已保存至: {output_path}")
                
        except Exception as e:
            print(f"⚠️ 可视化失败: {str(e)}")
            # 尝试生成文本文件
            try:
                with open(output_path.replace('.png', '.txt'), 'w', encoding='utf-8') as f:
                    f.write("知识图谱节点列表:\n")
                    for node in self.graph.nodes:
                        f.write(f"- {node}\n")
                    f.write("\n知识图谱关系列表:\n")
                    for edge in self.graph.edges(data=True):
                        f.write(f"- {edge[0]} -> {edge[1]} ({edge[2].get('type', 'unknown')})\n")
                print(f"✅ 已生成文本格式的知识图谱: {output_path.replace('.png', '.txt')}")
            except:
                print("⚠️ 无法生成任何输出文件")


    def generate_questions(self) -> List[Dict[str, str]]:
        """生成三类问题（适配当前数据结构）"""
        questions = []
        
        # 1. 概念定义问题（使用节点描述）
        for concept in self.graph.nodes:
            desc = self.graph.nodes[concept]['descriptions']
            questions.append({
                'type': 'definition',
                'question': f"请解释'{concept}'的概念",
                'reference': f"{concept}是指：{desc}",
                'concept': concept
            })
        
        # 2. 关系问题（使用边信息）
        for src, dst, data in self.graph.edges(data=True):
            questions.append({
                'type': 'relation',
                'question': f"描述'{src}'和'{dst}'之间的{data['type']}关系",
                'reference': f"关系类型：{data['type']}\n关系强度：{data['weight']}",
                'source': src,
                'target': dst
            })
        
        # 3. 应用问题（基于连接性）
        for concept in self.graph.nodes:
            neighbors = list(self.graph.neighbors(concept))
            if neighbors:
                questions.append({
                    'type': 'application',
                    'question': f"举例说明'{concept}'如何影响'{neighbors[0]}'",
                    'reference': f"通过{self.graph.edges[concept, neighbors[0]]['type']}关系产生影响",
                    'concept': concept,
                    'related': neighbors[0]
                })
        
        return questions

    def get_node_description(self, concept: str) -> str:
        """获取节点描述"""
        return self.graph.nodes.get(concept, {}).get('description', '无描述')

    def get_relation_info(self, source: str, target: str) -> Dict:
        """获取关系信息"""
        return self.graph.edges.get((source, target), {})
    
class SparkAPI:
    def __init__(self, appid, api_key, api_secret, spark_url="wss://spark-api.xf-yun.com/v1/x1"):
        """
        初始化星火API参数
        :param appid: 控制台获取的APPID
        :param api_key: 控制台获取的APIKey
        :param api_secret: 控制台获取的APISecret
        :param spark_url: 星火API的WebSocket地址
        """
        self.APPID = appid
        self.APIKey = api_key
        self.APISecret = api_secret
        self.Spark_url = spark_url
        self.host = urlparse(spark_url).netloc
        self.path = urlparse(spark_url).path
        self.answer = ""
        self.question = ""
        self.system_prompt= ""

    def create_url(self):
        """生成带鉴权的WebSocket连接URL"""
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        
        signature_origin = f"host: {self.host}\ndate: {date}\nGET {self.path} HTTP/1.1"
        signature_sha = hmac.new(
            self.APISecret.encode('utf-8'), 
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode()
        
        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode()
        
        v = {"authorization": authorization, "date": date, "host": self.host}
        return self.Spark_url + '?' + urlencode(v)

    def gen_params(self, question):
        """构造请求参数"""
        return {
            "header": {"app_id": self.APPID, "uid": "1234"},
            "parameter": {
                "chat": {
                    "domain": "x1",
                    "temperature": 0.7,  # 控制回复随机性
                    "max_tokens": 2048   # 控制回复长度
                }
            },
            "payload": {"message": {"text": [{"role": "user", "content": question}]}}
        }

    def on_message(self, ws, message):
        """处理API返回的流式数据"""
        data = json.loads(message)
        if data['header']['code'] != 0:
            print(f'请求错误: {data}')
            ws.close()
            return
        
        choices = data["payload"]["choices"]
        status = choices["status"]
        
        # 提取回复内容
        content = choices['text'][0].get("content", "")
        self.answer += content
        
        if status == 2:  # 对话结束
            ws.close()

    def on_error(self, ws, error):
        print("### 连接错误:", error)

    def on_close(self, ws, *args):
        pass

    def on_open(self, ws):
        """连接建立后发送问题"""
        def run(*args):
            data = json.dumps(self.gen_params(self.question))
            ws.send(data)
        thread.start_new_thread(run, ())

    def generate_questions(self, text: str, q_type: str = None) -> List[str]:
        """生成问题的主方法"""

        question_type_map = {
            'mcq': '单项选择题',
            'short_answer': '简答题'
        }

        question_num=random.randint(3,5)
        if q_type != None:
            self.question =[ f"请生成1道{question_type_map[q_type]}，要求：\n{text}"]* question_num
        else:
            self.question =[f"请基于下面要求，生成1道题目，要求：\n{text}"]*question_num
        self.answer = ""  # 重置回答
        self.system_prompt = ["你是一个生成练习题的助手，请把生成的题目以markdown语法提供给我，不要加入与题目无关的回答，例如“好的”"]*question_num
        # print('### 开始生成问题', self.question)
        self.answer = multi_conservation(
            self.system_prompt, self.question, need_json=[False] * question_num, show_progress=True
        )
        # print('### 生成问题完成', self.answer)
        # try:
        #     ws_url = self.create_url()
        #     ws = websocket.WebSocketApp(
        #         ws_url,
        #         on_message=self.on_message,
        #         on_error=self.on_error,
        #         on_close=self.on_close,
        #         on_open=self.on_open
        #     )
        #     ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
            
        # 处理每个回答：按换行拆分并过滤空行
        all_questions = []
        for answer in self.answer:
            # 每个answer是一个字符串，可能包含多道题目（用换行分隔）
            questions = [q.strip() for q in answer.split("\n") if q.strip()]
            all_questions.extend(questions)
        # print('### 生成问题完成', all_questions)
        return all_questions
        # except Exception as e:
        #     raise RuntimeError(f"问题生成失败: {str(e)}")
    
class KnowledgeQuestionGenerator(SparkAPI):
    def __init__(self, kg: KnowledgeGraph, **api_config):
        super().__init__(**api_config)
        self.kg = kg
        self.question_types = {
            'mcq': {
                'template': "请生成关于{concept}的单项选择题，要求：\n"
                          "- 题干清晰明确\n"
                          "- 选项4个，其中1个正确\n"
                          "- 难度{level}\n"
                          "- 考察重点：{focus}\n"
                          "- 知识点描述：{description}",
                'focus_map': {
                    'definition': '概念理解',
                    'relation': '关联分析'
                }
            },
            'short_answer': {
                'template': "请生成关于{concept}的简答题，要求：\n"
                          "- 问题聚焦{aspect}\n"
                          "- 期望答案长度{length}\n"
                          "- 知识点描述：{description}"
            }
        }
        
        # 添加难度级别定义
        self.difficulty_levels = {
            'easy': {
                'description': '基础概念题，直接考察定义',
                'keywords': ['定义', '基本概念', '简单']
            },
            'medium': {
                'description': '中等难度题，考察理解和简单应用',
                'keywords': ['理解', '应用', '关系']
            },
            'hard': {
                'description': '高难度题，考察综合分析能力',
                'keywords': ['分析', '综合', '复杂']
            }
        }
    def generate_for_concept_sequence(
        self,
        concept_sequence: List[str],
        level: str = "easy",
        q_type: str = "mcq",
        include_answer: bool = True,
        save_path: str = None
    ) -> Dict[str, List[Dict[str, str]]]:
        results = {}
        for concept in tqdm(concept_sequence, desc="生成题目"):
            if concept not in self.kg.graph:
                print(f"⚠️ 知识点 '{concept}' 不在图谱中，跳过。")
                continue
            questions = self.generate_by_concept(concept, q_type=q_type, level=level)
            results[concept] = questions

        if save_path:
            qa_dir = Path(save_path) / "QA"
            qa_dir.mkdir(parents=True, exist_ok=True)
            for concept, questions in results.items():
                with open(qa_dir / f"{concept}.md", "w", encoding="utf-8") as f:
                    f.write('\n'.join(questions))

        return results
    
    def generate_difficulty_samples(self, concept: str) -> Dict[str, List[str]]:
        """生成三种难度的样例题目"""
        samples = {}
        for level in ['easy', 'medium', 'hard']:
            try:
                # 每种难度生成2道题
                questions = self._generate_with_difficulty(concept, level, num=2)
                samples[level] = {
                    'description': self.difficulty_levels[level]['description'],
                    'questions': questions
                }
            except Exception as e:
                print(f"生成{level}难度题目失败: {str(e)}")
                samples[level] = {'questions': []}
        return samples

    def _generate_with_difficulty(self, concept: str, level: str, num: int = 2) -> List[str]:
        """按指定难度生成题目"""
        prompt = (
            f"请生成关于'{concept}'的1道{self.difficulty_levels[level]['description']}题目，要求：\n"
            f"- 题目类型：单项选择题\n"
            f"- 难度：{level}\n"
            f"- 重点考察：{', '.join(self.difficulty_levels[level]['keywords'])}\n)"
            f"- 知识点描述：{self.kg.get_node_description(concept)}\n"
            f"- 每道题有4个选项，其中1个正确\n"
            f"- 题目之间用'---'分隔"
        )
        raw_questions = self.generate_questions(prompt)
        # 处理返回的问题列表
        return [q.strip() for q in '\n'.join(raw_questions).split('---') if q.strip()]

    def generate_by_concept(self, concept: str, q_type: str = 'mcq',level: str = 'easy') -> List[str]:
        """基于特定知识点生成问题（适配当前数据结构）"""
        if concept not in self.kg.graph:
            raise ValueError(f"未知知识点: {concept}")
        
        node_data = self.kg.graph.nodes[concept]
        print("-------before------")
        print("node_data: ",node_data)
        params = {
            'concept': concept,
            'level': level,  # 基于连接数推断难度
            'description': node_data['description']  # 使用节点描述
        }
        print("1111111111111111")
        if q_type == 'mcq':
            print("-----mcq----------")
            neighbors = list(self.kg.graph.neighbors(concept))
            focus = 'relation' if neighbors else 'definition'
            params.update({
                'focus': self.question_types['mcq']['focus_map'].get(focus, '基础认知')
            })
            prompt = self.question_types['mcq']['template'].format(**params)
        else:
            print("-----short_answer----------")
            prompt = self.question_types['short_answer']['template'].format(
                concept=concept,  # 添加缺失的关键参数
                aspect=self._infer_aspect(concept),  # 自动推断考察重点
                length='3-5句话',
                description=node_data['description']
            )
        # print("222222222222222222222",prompt)
        output = self.generate_questions(prompt,q_type)
        # print(output)
        return output


    def _infer_difficulty(self, concept: str) -> str:
        """基于连接数推断难度"""
        degree = len(list(self.kg.graph.neighbors(concept)))
        print(f"🔍 推断知识点 '{concept}' 的难度，连接数: {degree}")
        if degree == 0:
            return "简单"
        elif degree <= 3:
            return "中等" 
        else:
            return "困难"

    def _infer_aspect(self, concept: str) -> str:
        """从描述中提取关键考察方面"""
        desc = self.kg.graph.nodes[concept]['description']
        print("desc:",desc)
        if len(desc) < 20:
            return "核心定义"
        elif "应用" in desc or "使用" in desc:
            return "实际应用"
        else:
            return "关键特征"
    
    def generate_and_save(self, output_path: str = "./questions", formats: List[str] = ["md", "txt"], 
                        concept: str = None, relation_type: str = None,level:str=None):
        """生成并保存问题（带进度显示）"""
        print("\n" + "="*50)
        print("🚀 开始生成问题集")
        start_time = time.time()
        
        os.makedirs(output_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 生成问题
        print("\n🔧 正在生成问题...")
        if concept:
            print(f"  专注生成知识点: {concept}")
            questions = {
                "concept_questions": [
                    ("选择题", self._generate_with_progress(concept, 'mcq',level=level)),
                    ("简答题", self._generate_with_progress(concept, 'short_answer',level=level))
                ]
            }
        elif relation_type:
            print(f"  专注生成关系类型: {relation_type}")
            questions = {"relation_questions": self.generate_relation_questions(relation_type,level=level)}
        else:
            print("  生成全部知识点和关系的问题")
            questions = {
                "all_concepts": self._generate_all_concept_questions(level=level),
                "all_relations": self.generate_relation_questions(level=level)
            }
        
        # 保存文件
        print("\n💾 正在保存文件...")
        for fmt in formats:
            if fmt == "md":
                path = f"{output_path}/questions_{timestamp}.md"
                self._save_as_markdown(questions, path)
                print(f"  ✅ Markdown文件已保存: {path}")
            elif fmt == "txt":
                path = f"{output_path}/questions_{timestamp}.txt"
                self._save_as_text(questions, path)
                print(f"  ✅ 文本文件已保存: {path}")
        
        # 预览
        print("\n🔍 生成结果预览:")
        self._print_questions_preview(questions)
        
        print(f"\n🎉 全部完成! 总耗时 {time.time()-start_time:.2f} 秒")
        print("="*50)

    def _generate_with_progress(self, concept: str, q_type: str,level:str="easy") -> List[str]:
        """带进度显示的问题生成"""
        try:
            print(f"  正在生成 {q_type} 问题: {concept[:20]}...")
            start_time = time.time()
            result = self.generate_by_concept(concept, q_type,level)
            print(f"  ✅ 生成完成 ({len(result)} 个问题, 耗时 {time.time()-start_time:.2f} 秒)")
            return result
        except Exception as e:
            print(f"  ❌ 生成失败: {str(e)}")
            return []

    def _generate_all_concept_questions(self,level: str="easy") -> Dict[str, List[str]]:
        """生成所有知识点的问题（带进度条）"""
        results = {}
        concepts = list(self.kg.graph.nodes)
        print(f"  需要处理 {len(concepts)} 个知识点")
        cnt=0
        for concept in tqdm(concepts, desc="生成概念问题"):
            cnt+=1
            if cnt<4:
                try:
                    results[concept] = {
                        "mcq": self.generate_by_concept(concept, 'mcq',level),
                        "short_answer": self.generate_by_concept(concept, 'short_answer',level)
                    }
                except Exception as e:
                    print(f"\n⚠️ 生成失败 [{concept}]: {str(e)}")
                    continue
                
        return results

    def generate_relation_questions(self, relation_type: str = None,level:str="easy") -> Dict[str, List[str]]:
        """生成关系类问题（带进度显示）"""
        results = {}
        edges = [e for e in self.kg.graph.edges(data=True) 
                if relation_type is None or e[2]['type'] == relation_type]
        
        if not edges:
            print("⚠️ 未找到匹配的关系类型" if relation_type else "⚠️ 知识图谱中没有关系数据")
            return {}
        
        print(f"  正在处理 {len(edges)} 条关系...")
        cnt=0
        for src, dst, data in tqdm(edges, desc="生成关系问题"):
            cnt+=1
            if cnt<4:
                try:
                    prompt = (
                        f"请生成考察以下关系的题目：\n"
                        f"- 知识点1：{src}\n"
                        f"- 知识点2：{dst}\n"
                        f"- 关系类型：{data['type']}\n"
                        f"要求：\n"
                        f"- 难度：{level}\n"
                        f"- 选择题需包含反映该关系特征的选项\n"
                        f"- 简答题需评估对该关系的理解深度\n"
                        f"- 不要在题干和选项中出现“第几章”等与知识点无关的冗杂字样"
                    )
                    questions = self.generate_questions(prompt)
                    print(questions)
                    results[f"{src}→{dst}({data['type']})"] = questions
                except Exception as e:
                    print(f"\n⚠️ 生成失败 [{src}→{dst}]: {str(e)}")
                    continue
            else:
                break
                    
        return results
    # def _save_as_markdown(self, questions: Dict, filepath: str):
    #     """保存为Markdown格式"""
    #     with open(filepath, 'w', encoding='utf-8') as f:
    #         for category, content in questions.items():
    #             f.write(f"## {category.replace('_', ' ').title()}\n\n")
    #             if isinstance(content, dict):
    #                 for key, value in content.items():
    #                     f.write(f"### {key}\n")
    #                     if isinstance(value, list):
    #                         for q in value:
    #                             f.write(f"- {q}\n")
    #                     elif isinstance(value, dict):
    #                         for sub_key, sub_value in value.items():
    #                             f.write(f"#### {sub_key}\n")
    #                             for q in sub_value:
    #                                 f.write(f"- {q}\n")
    #                     f.write("\n")
    #             else:
    #                 for q in content:
    #                     f.write(f"- {q}\n")
    #             f.write("\n")

    def _save_as_markdown(self, questions: Dict, filepath: str):
        """保存为格式良好的Markdown文件，优化处理题型元组结构"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for category, content in questions.items():
                # 分类标题
                f.write(f"## {category.replace('_', ' ').title()}\n\n")
                
                if isinstance(content, (list, tuple)):
                    # 处理题型元组结构 [('选择题', [题目列表]), ('简答题', [题目列表])]
                    for question_type, question_list in content:
                        if not isinstance(question_list, (list, tuple)):
                            question_list = [question_list]
                        
                        f.write(f"### {question_type}\n\n")
                        
                        current_question = []
                        for item in question_list:
                            if isinstance(item, str):
                                # 处理题目文本
                                if item.startswith('###'):  # 子标题
                                    if current_question:
                                        f.write("\n".join(current_question) + "\n\n")
                                        current_question = []
                                    f.write(f"{item}\n")
                                elif item.startswith('**') or "：" in item:  # 题目或答案标记
                                    if current_question and not current_question[-1].endswith("\n"):
                                        current_question.append("")  # 添加空行分隔
                                    current_question.append(item)
                                else:  # 普通题目内容
                                    current_question.append(item)
                            elif item is not None:
                                current_question.append(str(item))
                        
                        if current_question:  # 写入最后一个问题
                            f.write("\n".join(current_question) + "\n\n")
                
                f.write("\n")  # 分类间空行

    def _save_as_text(self, questions: Dict, filepath: str):
        """保存为纯文本格式"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for category, content in questions.items():
                f.write(f"【{category.replace('_', ' ').upper()}】\n\n")
                if isinstance(content, dict):
                    for key, value in content.items():
                        f.write(f"*{key}*\n")
                        if isinstance(value, list):
                            for q in value:
                                f.write(f"  - {q}\n")
                        elif isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                f.write(f"  {sub_key}:\n")
                                for q in sub_value:
                                    f.write(f"    - {q}\n")
                        f.write("\n")
                else:
                    for q in content:
                        f.write(f"- {q}\n")
                f.write("\n")

    # def _save_as_markdown(self, questions: Dict, filepath: str):
    #     """保存为格式良好的Markdown文件"""
    #     with open(filepath, 'w', encoding='utf-8') as f:
    #         for category, content in questions.items():
    #             # 分类标题
    #             f.write(f"## {category.replace('_', ' ').title()}\n\n")
                
    #             if isinstance(content, dict):
    #                 # 处理嵌套字典结构
    #                 for key, value in content.items():
    #                     f.write(f"### {key}\n\n")
                        
    #                     if isinstance(value, list):
    #                         # 处理问题列表
    #                         for item in value:
    #                             if isinstance(item, (list, tuple)):
    #                                 # 处理多行问题(如选择题)
    #                                 for line in item:
    #                                     if line.strip():  # 跳过空行
    #                                         f.write(f"{line}\n")
    #                                 f.write("\n")  # 问题间空行
    #                             else:
    #                                 # 处理单行问题
    #                                 if item.strip():  # 跳过空行
    #                                     f.write(f"{item}\n\n")
    #                     elif isinstance(value, dict):
    #                         # 处理更深层级的嵌套
    #                         for sub_key, sub_value in value.items():
    #                             f.write(f"#### {sub_key}\n\n")
    #                             for q in sub_value:
    #                                 f.write(f"{q}\n\n")
    #             else:
    #                 # 处理非嵌套的简单列表
    #                 for q in content:
    #                     if q.strip():  # 跳过空行
    #                         f.write(f"{q}\n\n")
                
    #             f.write("\n")  # 分类间空行
    def _print_questions_preview(self, questions: Dict):
        """控制台打印预览"""
        print("\n=== 问题预览 ===")
        for category, content in questions.items():
            print(f"\n【{category.replace('_', ' ').title()}】")
            if isinstance(content, dict):
                for key, value in content.items():
                    print(f"\n* {key}:")
                    if isinstance(value, list):
                        for i, q in enumerate(value[:2], 1):  # 每类只显示前2个
                            print(f"  {i}. {q[:60]}...")
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            print(f"  - {sub_key}:")
                            for i, q in enumerate(sub_value[:1], 1):  # 每子类只显示1个
                                print(f"    {i}. {q[:60]}...")
            else:
                for i, q in enumerate(content[:3], 1):  # 只显示前3个
                    print(f"{i}. {q[:60]}...")

    def interactive_question_generation(self, parent_widget=None):
        """
        使用Qt对话框替代input/print实现交互
        """
        from PyQt5.QtWidgets import QInputDialog, QMessageBox

        # 选择知识点
        concepts = list(self.kg.graph.nodes)
        concept, ok = QInputDialog.getItem(parent_widget, "选择知识点", "请选择一个知识点：", concepts, 0, False)
        if not ok:
            return

        # 难度样本
        samples = self.generate_difficulty_samples(concept)
        options = [f"{lvl.upper()} - {samples[lvl]['description']}" for lvl in samples]
        level_text, ok = QInputDialog.getItem(parent_widget, "选择难度", "请选择难度：", options, 0, False)
        if not ok:
            return
        selected_level = list(samples.keys())[options.index(level_text)]

        # 生成范围选择
        range_text, ok = QInputDialog.getItem(
            parent_widget,
            "选择生成方式",
            "请选择题目生成范围：",
            ["全部知识点", "仅当前知识点"],
            0, False
        )
        if not ok:
            return

        if range_text == "全部知识点":
            self.generate_and_save(level=selected_level)
        else:
            self.generate_and_save(concept=concept, level=selected_level)

        QMessageBox.information(parent_widget, "完成", f"已生成 '{selected_level}' 难度的题目")


        

    def _select_concept(self) -> str:
        """让用户选择知识点"""
        concepts = list(self.kg.graph.nodes)
        print("\n📖 可选知识点列表:")
        for i, concept in enumerate(concepts[:10], 1):  # 只显示前10个
            print(f"{i}. {concept}")
        while True:
            try:
                choice = int(input("\n请选择知识点编号: ")) - 1
                if 0 <= choice < len(concepts):
                    return concepts[choice]
                print(f"请输入1-{len(concepts)}之间的数字！")
            except ValueError:
                print("请输入有效数字！")

    
if __name__ == "__main__":
    # 1. 构建知识图谱
    kg = KnowledgeGraph()
    kg.load_knowledge_graph()

    # 2. 初始化生成器
    generator = KnowledgeQuestionGenerator(
        kg,
        appid="2d1bc910",
        api_key="a1df9334fd048ded0c9304ccf12c20d1",
        api_secret="YzZjODMwNmNjNmRiMDVjOGI4MjcxZDVi"
    )

    # 启动交互式生成流程
    result = generator.interactive_question_generation()
