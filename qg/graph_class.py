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
import ssl

class KnowledgeGraph:
    def __init__(self):
        """初始化带知识点属性的图结构"""
        self.graph = nx.DiGraph()  # 使用有向图表示知识点依赖关系
        self.question_templates = {
            'definition': "请解释{concept}的核心概念",
            'relation': "{source}和{target}之间的关系主要体现在哪些方面？",
            'application': "如何运用{concept}解决实际问题？"
        }

    def add_knowledge_node(self, concept: str, metadata: Dict):
        """添加知识点节点"""
        self.graph.add_node(concept, **metadata)
        
    def add_relation(self, source: str, target: str, rel_type: str, weight: float = 1.0):
        """添加知识点关系边"""
        self.graph.add_edge(source, target, relation=rel_type, weight=weight)
    
    def generate_question_prompts(self) -> List[Tuple[str, str]]:
        """生成基于知识结构的提示词对(问题提示, 参考答案提示)"""
        prompts = []
        
        # 1. 概念定义类问题
        for concept in self.graph.nodes:
            meta = self.graph.nodes[concept]
            prompt = f"作为{meta.get('domain', '某领域')}专家，请用{meta.get('difficulty', '简单')}语言解释：{concept}"
            answer_hint = f"{concept}是指{meta.get('definition', '暂无标准定义')}"
            prompts.append((prompt, answer_hint))
        
        # 2. 关系类问题
        for src, dst, data in self.graph.edges(data=True):
            prompt = (f"在{self.graph.nodes[src].get('domain', '该领域')}中，"
                    f"{src}如何通过{data['relation']}影响{dst}？")
            answer_hint = f"典型影响包括：{data.get('evidence', '文献[1]证明...')}"
            prompts.append((prompt, answer_hint))
        
        # 3. 综合应用题
        for concept in nx.center(self.graph):
            linked = list(self.graph.neighbors(concept))
            prompt = (f"给定场景：{self.graph.nodes[concept].get('scenario', '常规场景')}，"
                    f"请分析{concept}与{'、'.join(linked[:3])}的协同作用")
            prompts.append((prompt, "需考虑多因素耦合效应"))
        
        return prompts
    
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
                          "- 考察重点：{focus}",
                'focus_map': {
                    'definition': '概念理解',
                    'relation': '关联分析'
                }
            },
            'short_answer': {
                'template': "请生成关于{concept}的简答题，要求：\n"
                          "- 问题聚焦{aspect}\n"
                          "- 期望答案长度{length}\n"
                          "- 包含评分要点"
            }
        }

    def generate_by_concept(self, concept: str, q_type: str = 'mcq') -> List[str]:
        """基于特定知识点生成问题"""
        if concept not in self.kg.graph:
            raise ValueError(f"未知知识点: {concept}")
        
        node_data = self.kg.graph.nodes[concept]
        params = {
            'concept': concept,
            'level': node_data.get('difficulty', '中等'),
            'domain': node_data.get('domain', '通用领域')
        }
        
        if q_type == 'mcq':
            # 自动确定考察重点
            neighbors = list(self.kg.graph.neighbors(concept))
            focus = 'relation' if neighbors else 'definition'
            params.update({
                'focus': self.question_types['mcq']['focus_map'].get(focus, '基础认知')
            })
            prompt = self.question_types['mcq']['template'].format(**params)
        else:
            prompt = self.question_types['short_answer']['template'].format(
                aspect=node_data.get('key_aspect', '核心特征'),
                length='3-5句话'
            )
        
        return self.generate_questions(prompt)

    def generate_relation_questions(self, relation_type: str) -> Dict[str, List[str]]:
        """生成特定关系类型的问题集"""
        results = {}
        for src, dst, data in self.kg.graph.edges(data=True):
            if data['relation'] == relation_type:
                prompt = (f"请以选择题形式考察{src}与{dst}的{relation_type}关系：\n"
                         f"- 正确选项应体现{data.get('evidence', '权威文献')}结论\n"
                         f"- 干扰项包含常见误解")
                questions = self.generate_questions(prompt)
                results[f"{src}→{dst}"] = questions
        return results
    
# 1. 构建知识图谱
kg = KnowledgeGraph()
kg.add_knowledge_node("气候变化", {
    'domain': '环境科学',
    'difficulty': '中等',
    'definition': '全球气候系统的长期变化过程',
    'key_aspects': ['温室效应', '极端天气']
})
kg.add_knowledge_node("碳中和", {
    'domain': '能源政策',
    'difficulty': '进阶'
})
kg.add_relation("气候变化", "碳中和", "解决方案", weight=0.8)

# 2. 初始化生成器
generator = KnowledgeQuestionGenerator(
    kg,
    appid="2d1bc910",
    api_key="a1df9334fd048ded0c9304ccf12c20d1",
    api_secret="YzZjODMwNmNjNmRiMDVjOGI4MjcxZDVi"
)

# 3. 生成两类问题
print("=== 概念测试题 ===")
for q in generator.generate_by_concept("气候变化"):
    print(q)

print("\n=== 关系测试题 ===")
for rel, questions in generator.generate_relation_questions("解决方案").items():
    print(f"\n关系 {rel}:")
    for q in questions:
        print(f"- {q}")