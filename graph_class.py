import networkx as nx
from typing import Dict, List, Tuple
import json
import websocket
from websocket import WebSocketApp
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

# import sys
# from pathlib import Path

# # 获取当前文件的绝对路径，然后找到项目根目录（假设项目根目录是 "EduSpark"）
# current_dir = Path(__file__).parent
# project_root = current_dir.parent.parent  # 根据实际情况调整层级

# # 将项目根目录添加到 Python 路径
# sys.path.append(str(project_root))

from utils.api import (
    single_conversation,
    multi_conservation,
    single_embedding,
    multi_embedding,
    multiroundConversation,
)

import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor


class ConcurrentRequestHandler:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers

    def generate_questions_concurrently(self, prompts: List[str]) -> List[str]:
        """并发生成多个问题"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(tqdm.tqdm(
                executor.map(self._generate_single_question, prompts),
                total=len(prompts),
                desc="并发生成问题"
            ))
        return results

    def _generate_single_question(self, prompt: str) -> str:
        """单个问题生成（适配你的API）"""
        # 这里替换为你的实际生成逻辑
        return single_conversation(
            system_prompt="你是一个问题生成助手",
            user_input=prompt,
            need_json=False,
            show_progress=False
        )
    

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
        
        nodes_path = graph_file_path + "/all_node.json"
        edges_path = graph_file_path + "/all_relations.json"
        
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
            rel_type = edge['type'] + edge['descriptions'][-1] if edge['descriptions'] else edge['type']
            self.graph.add_edge(source, target, type=rel_type, weight=edge.get('weight', 1.0))
        
        print(f"\n🎉 知识图谱加载完成! 共 {len(nodes)} 节点, {len(edges)} 边, 耗时 {time.time()-start_time:.2f} 秒")


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

    def generate_questions(self, text):
        """生成问题的主方法"""
        self.question = f"请基于以下文本生成3-5个单项选择题：\n{text}"
        self.answer = ""  # 重置回答
        
        ws_url = self.create_url()
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        # 格式化返回的问题列表
        questions = [q.strip() for q in self.answer.split("\n") if q.strip()]
        return questions
    
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

    def generate_by_concept(self, concept: str, q_type: str = 'mcq') -> List[str]:
        """基于特定知识点生成问题（适配当前数据结构）"""
        if concept not in self.kg.graph:
            raise ValueError(f"未知知识点: {concept}")
        
        node_data = self.kg.graph.nodes[concept]
        print("-------before------")
        print("node_data: ",node_data)
        params = {
            'concept': concept,
            'level': self._infer_difficulty(concept),  # 基于连接数推断难度
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
        print("222222222222222222222")
        return self.generate_questions(prompt)

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
                        concept: str = None, relation_type: str = None):
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
                    ("选择题", self._generate_with_progress(concept, 'mcq')),
                    ("简答题", self._generate_with_progress(concept, 'short_answer'))
                ]
            }
        elif relation_type:
            print(f"  专注生成关系类型: {relation_type}")
            questions = {"relation_questions": self.generate_relation_questions(relation_type)}
        else:
            print("  生成全部知识点和关系的问题")
            questions = {
                "all_concepts": self._generate_all_concept_questions(),
                "all_relations": self.generate_relation_questions()
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

    def _generate_with_progress(self, concept: str, q_type: str) -> List[str]:
        """带进度显示的问题生成"""
        try:
            print(f"  正在生成 {q_type} 问题: {concept[:20]}...")
            start_time = time.time()
            result = self.generate_by_concept(concept, q_type)
            print(f"  ✅ 生成完成 ({len(result)} 个问题, 耗时 {time.time()-start_time:.2f} 秒)")
            return result
        except Exception as e:
            print(f"  ❌ 生成失败: {str(e)}")
            return []

    def _generate_all_concept_questions(self) -> Dict[str, List[str]]:
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
                        "mcq": self.generate_by_concept(concept, 'mcq'),
                        "short_answer": self.generate_by_concept(concept, 'short_answer')
                    }
                except Exception as e:
                    print(f"\n⚠️ 生成失败 [{concept}]: {str(e)}")
                    continue
                
        return results

    def generate_relation_questions(self, relation_type: str = None) -> Dict[str, List[str]]:
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
            if cnt<2:
                try:
                    prompt = (
                        f"请生成考察以下关系的题目：\n"
                        f"- 知识点1：{src}\n"
                        f"- 知识点2：{dst}\n"
                        f"- 关系类型：{data['type']}\n"
                        f"要求：\n"
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
    
    def generate_by_concepts_batch(self, concepts: List[str], q_type: str = 'mcq') -> Dict[str, List[str]]:
        """批量生成多个知识点的问题（并发优化）"""
        print(f"\n🚀 开始批量生成 {len(concepts)} 个知识点的问题")
        results = {}
        
        # 准备所有prompt
        prompts = []
        for concept in concepts:
            if concept not in self.kg.graph:
                print(f"⚠️ 跳过未知知识点: {concept}")
                continue
                
            params = {
                'concept': concept,
                'level': self._infer_difficulty(concept),
                'description': self.kg.get_node_description(concept)
            }
            
            if q_type == 'mcq':
                prompt = self.question_types['mcq']['template'].format(**params)
            else:
                prompt = self.question_types['short_answer']['template'].format(
                    concept=concept,
                    aspect=self._infer_aspect(concept),
                    length='3-5句话',
                    description=params['description']
                )
            prompts.append(prompt)
        
        # 并发执行
        questions_list = self.concurrent_handler.generate_questions_concurrently(prompts)
        
        # 整理结果
        for concept, questions in zip(concepts, questions_list):
            results[concept] = [q.strip() for q in questions.split("\n") if q.strip()]
        
        return results

    def generate_relation_questions_concurrent(self, relation_type: str = None) -> Dict[str, List[str]]:
        """并发生成关系类问题"""
        edges = [e for e in self.kg.graph.edges(data=True) 
                if relation_type is None or e[2]['type'] == relation_type]
        
        if not edges:
            print("⚠️ 未找到匹配的关系")
            return {}
            
        print(f"\n🚀 开始并发生成 {len(edges)} 条关系问题")
        results = {}
        
        # 准备所有prompt
        prompts = []
        relations = []
        for src, dst, data in edges:
            prompt = (
                f"请生成考察以下关系的题目：\n"
                f"- 知识点1：{src}\n"
                f"- 知识点2：{dst}\n"
                f"- 关系类型：{data['type']}\n"
                f"要求：\n"
                f"- 选择题需包含反映该关系特征的选项\n"
                f"- 简答题需评估对该关系的理解深度"
            )
            prompts.append(prompt)
            relations.append(f"{src}→{dst}({data['type']})")
        
        # 并发执行
        questions_list = self.concurrent_handler.generate_questions_concurrently(prompts)
        
        # 整理结果
        for rel, questions in zip(relations, questions_list):
            results[rel] = [q.strip() for q in questions.split("\n") if q.strip()]
        
        return results
    def _save_as_markdown(self, questions: Dict, filepath: str):
        """保存为Markdown格式"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for category, content in questions.items():
                f.write(f"## {category.replace('_', ' ').title()}\n\n")
                if isinstance(content, dict):
                    for key, value in content.items():
                        f.write(f"### {key}\n")
                        if isinstance(value, list):
                            for q in value:
                                f.write(f"- {q}\n")
                        elif isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                f.write(f"#### {sub_key}\n")
                                for q in sub_value:
                                    f.write(f"- {q}\n")
                        f.write("\n")
                else:
                    for q in content:
                        f.write(f"- {q}\n")
                f.write("\n")

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
        

if __name__ == "__main__":
    mp.freeze_support()

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

    # 3. 并发生成测试
    concepts = list(kg.graph.nodes)[:5]  # 取前5个概念测试
    batch_results = generator.generate_by_concepts_batch(concepts, 'mcq')
    
    # 4. 并发关系问题生成
    rel_results = generator.generate_relation_questions_concurrent()
    
    # 5. 保存结果
    generator.generate_and_save(
        output_path="./output",
        formats=["md", "txt"],
        concept=None,
        relation_type=None
    )

    # # 生成所有关系问题
    # all_relation_questions = generator.generate_relation_questions()

    # # 生成特定类型关系问题
    # causal_questions = generator.generate_relation_questions("因果关系")

    # generator.generate_and_save()
