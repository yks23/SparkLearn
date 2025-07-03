import re
import json
import yaml
import multiprocessing as mp
import os
from typing import List, Dict, Union, Optional
from utils.api import single_conversation
from tqdm import tqdm 

class Annotator:
    def __init__(self, use_llm_for_structure: bool = True):
        """
        初始化智能Markdown文档批注器
        :param use_llm_for_structure: 是否使用大模型处理文档结构
        """
        self.annotation_cache = {}
        self.section_cache = {} 
        self.use_llm_for_structure = use_llm_for_structure

    def parse_markdown(self, markdown_content: str) -> Dict:
        """
        解析Markdown文档为结构化数据
        :param markdown_content: Markdown格式的文本
        :return: 结构化文档字典
        """
        if self.use_llm_for_structure:
            # 使用大模型辅助解析文档结构
            return self._parse_with_llm(markdown_content)
        else:
            # 使用本地方法解析文档结构
            return self._parse_locally(markdown_content)
    
    def _parse_with_llm(self, markdown_content: str) -> Dict:
        """
        使用大模型解析文档结构
        :param markdown_content: Markdown内容
        :return: 结构化文档字典
        """
        # 使用大模型辅助解析文档结构
        structure = self._get_document_structure(markdown_content)
        
        # 初始化文档结构
        structured_doc = {
            'title': structure.get("title", "未命名文档"),
            'metadata': structure.get("metadata", {}),
            'sections': []
        }

        # 如果有明确的章节结构
        if structure.get("sections"):
            for section in structure["sections"]:
                # 创建章节内容
                section_content = self._extract_section_content(
                    markdown_content, section["start"], section["end"])
                
                # 添加到文档结构
                structured_doc['sections'].append({
                    'title': section["title"],
                    'paragraphs': self._create_section_paragraphs(section_content),
                    'annotations': []
                })
        else:
            # 如果大模型没有识别出结构，则按传统方式处理
            structured_doc = self._fallback_parsing(markdown_content)
        
        return structured_doc
    
    def _parse_locally(self, markdown_content: str) -> Dict:
        """
        使用本地方法解析文档结构
        :param markdown_content: Markdown内容
        :return: 结构化文档字典
        """
        return self._fallback_parsing(markdown_content)

    def _get_document_structure(self, markdown_content: str) -> Dict:
        """
        使用大模型分析文档结构
        :param markdown_content: Markdown内容
        :return: 文档结构分析结果
        """
        prompt = f"""
        分析以下Markdown文档的结构，识别标题、章节和元数据：
        {markdown_content[:2000]}  # 只取前2000字符避免超长
        
        要求：
        1. 识别文档标题（如果有）
        2. 识别元数据（YAML front matter）
        3. 识别所有章节，包括标题级别和位置
        4. 按JSON格式返回：
        {{"title": "文档标题",
          "metadata": {{}},
          "sections": [
            {{"level": "标题级别（如h1、h2）",
              "title": "章节标题",
              "start": "起始位置",
              "end": "结束位置"
            }}
          ]}}
        """
        response = self.call_llm(prompt, need_json=True)
        try:
            # 清理响应字符串
            cleaned_response = response.strip()
            cleaned_response = re.sub(r'(```json|json)', '', cleaned_response).strip()
            cleaned_response = re.sub(r'`', '', cleaned_response).strip()
            
            # 加载为JSON
            structure = json.loads(cleaned_response)
            
            # 验证和转换start和end为整数
            if structure.get("sections"):
                for section in structure["sections"]:
                    if "start" in section and isinstance(section["start"], (float, int)):
                        section["start"] = int(section["start"])
                    else:
                        section["start"] = 0  # 默认值
                    
                    if "end" in section and isinstance(section["end"], (float, int)):
                        section["end"] = int(section["end"])
                    else:
                        section["end"] = len(markdown_content)  # 默认值
            
            return structure
        except:
            # 如果解析失败，返回空结构
            return {
                "title": "",
                "metadata": {},
                "sections": []
            }

    def _extract_section_content(self, full_content: str, start: int, end: int) -> str:
        """
        提取章节内容
        :param full_content: 完整文档内容
        :param start: 章节起始位置
        :param end: 章节结束位置
        :return: 提取的章节内容
        """
        # 确保start和end是整数
        start = max(0, min(start, len(full_content)))
        end = max(start, min(end, len(full_content)))
        return full_content[start:end].strip()

    def _fallback_parsing(self, markdown_content: str) -> Dict:
        """
        传统方式解析Markdown文档（备用方案）
        :param markdown_content: Markdown内容
        :return: 结构化文档字典
        """
        structured_doc = {
            'title': "未命名文档",
            'metadata': {},
            'sections': []
        }

        # 提取文档元数据（YAML front matter）
        front_matter_match = re.search(r'^---\s*\n(.+?)\n---', markdown_content, re.DOTALL)
        if front_matter_match:
            try:
                structured_doc['metadata'] = yaml.safe_load(front_matter_match.group(1))
            except:
                pass
        
        # 分割所有标题（支持h1-h6）
        sections = re.split(r'\n(?=[#]{1,6}\s)', markdown_content)
        
        # 处理每个部分
        for section in sections:
            # 匹配标题
            title_match = re.match(r'^[#]{1,6}\s+(.+)', section)
            if title_match:
                title = title_match.group(1).strip()
                content = section[len(title_match.group(0)):].strip()
                
                # 确定标题级别
                level = len(title_match.group(0).split()[0])
                
                # 创建章节
                structured_doc['sections'].append({
                    'title': title,
                    'level': level,
                    'paragraphs': self._create_section_paragraphs(content),
                    'annotations': []
                })
            else:
                # 无标题部分作为内容
                if sections.index(section) == 0:
                    # 第一个无标题部分可能是文档介绍
                    structured_doc['sections'].append({
                        'title': "介绍",
                        'level': 1,
                        'paragraphs': self._create_section_paragraphs(section),
                        'annotations': []
                    })
                else:
                    # 后续无标题部分作为独立章节
                    structured_doc['sections'].append({
                        'title': f"未命名章节 {len(structured_doc['sections'])+1}",
                        'level': 2,
                        'paragraphs': self._create_section_paragraphs(section),
                        'annotations': []
                    })
        
        # 如果没有识别到任何章节，创建一个默认章节
        if not structured_doc['sections']:
            structured_doc['sections'].append({
                'title': "内容",
                'level': 1,
                'paragraphs': self._create_section_paragraphs(markdown_content),
                'annotations': []
            })
        return structured_doc

    def _create_section_paragraphs(self, content: str) -> List[Dict]:
        """
        创建章节段落列表（使用大模型辅助）
        :param content: 章节内容
        :return: 段落对象列表
        """
        # 使用大模型分析段落结构
        paragraphs = self._get_paragraphs_from_llm(content)
        
        if paragraphs:
            # 创建段落对象
            paragraph_objects = []
            for para in paragraphs:
                # 提取纯文本用于分析（去除Markdown格式）
                plain_text = self._markdown_to_plaintext(para)
                paragraph_objects.append({
                    'raw': para,
                    'text': plain_text
                })
            
            return paragraph_objects
        else:
            # 如果大模型解析失败，回退到传统方式处理
            return self._fallback_paragraph_parsing(content)

    def _get_paragraphs_from_llm(self, content: str) -> List[str]:
        """
        使用大模型提取段落列表
        :param content: 章节内容
        :return: 段落列表
        """
        prompt = f"""
        分析以下Markdown章节内容，提取段落列表：
        {content[:2000]}  # 只取前2000字符避免超长
        
        要求：
        1. 识别并提取所有段落内容
        2. 排除标题、列表标记、代码块等非段落内容
        3. 按顺序返回段落列表
        4. 按JSON格式返回：{{"paragraphs": ["段落1", "段落2", ...]}}
        """
        response = self.call_llm(prompt, need_json=True)
        try:
            # 清理响应字符串
            cleaned_response = response.strip()
            cleaned_response = re.sub(r'(```json|json)', '', cleaned_response).strip()
            cleaned_response = re.sub(r'`', '', cleaned_response).strip()
            
            # 加载为JSON
            result = json.loads(cleaned_response)
            if "paragraphs" in result:
                return result["paragraphs"]
            else:
                return []
        except:
            return []

    def _fallback_paragraph_parsing(self, content: str) -> List[Dict]:
        """
        传统方式提取段落（备用方案）
        :param content: 章节内容
        :return: 段落对象列表
        """
        paragraphs = []
        current_paragraph = []
        in_code_block = False
        in_list = False
        in_header = False  # 添加标题状态标记

        for line in content.split('\n'):
            # 处理代码块
            if line.startswith('```'):
                in_code_block = not in_code_block
            
            # 处理列表
            list_item = re.match(r'^(\s*[-*+]\s+|\s*\d+\.\s+)', line)
            if list_item and not in_code_block:
                if not in_list:
                    # 列表开始
                    if current_paragraph:
                        paragraphs.append('\n'.join(current_paragraph))
                        current_paragraph = []
                    in_list = True
            elif in_list and not in_code_block:
                # 列表结束
                in_list = False
            
            # 检测标题行
            header_match = re.match(r'^#+\s+', line)
            if header_match and not in_code_block:
                if current_paragraph:
                    paragraphs.append('\n'.join(current_paragraph))
                    current_paragraph = []
                in_header = True
            elif in_header:
                # 标题结束
                in_header = False
            
            # 空行分割段落（不在代码块、列表或标题中）
            if not line.strip() and not in_code_block and not in_list and not in_header:
                if current_paragraph:
                    paragraphs.append('\n'.join(current_paragraph))
                    current_paragraph = []
            else:
                current_paragraph.append(line)
        
        # 添加最后一个段落
        if current_paragraph:
            paragraphs.append('\n'.join(current_paragraph))
        
        # 创建段落对象
        paragraph_objects = []
        for para in paragraphs:
            # 提取纯文本用于分析（去除Markdown格式）
            plain_text = self._markdown_to_plaintext(para)
            paragraph_objects.append({
                'raw': para,
                'text': plain_text
            })
        
        return paragraph_objects

    def _markdown_to_plaintext(self, markdown: str) -> str:
        """
        将Markdown转换为纯文本（用于分析）
        :param markdown: Markdown文本
        :return: 纯文本
        """
        # 移除代码块
        text = re.sub(r'```.*?```', '', markdown, flags=re.DOTALL)
        # 移除内联代码
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # 移除图片
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
        # 移除链接
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # 移除粗体和斜体
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        # 移除引用
        text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 移除多余的空白
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def call_llm(self, prompt: str, need_json: bool = False) -> Union[str, Dict]:
        """
        调用大模型API
        :param prompt: 提示词
        :param need_json: 是否返回JSON格式
        :return: 模型响应内容
        """
        # 使用统一的系统提示
        system_prompt = "你是一个文档智能批注助手，负责分析文档内容并提供批注和解释。"
        
        try:
            response = single_conversation(
                system_prompt=system_prompt,
                user_input=prompt,
                need_json=need_json,
                show_progress=False
            )
            return response
        except Exception as e:
            print(f"API调用失败: {e}")
            return None

    def assess_difficulty(self, text: str) -> float:
        """评估文本难度 (0-1分)"""
        if not text.strip():
            return 0.0
            
        prompt = f"""
        请评估以下文本的阅读难度，给出0-1之间的分数（1为最难）：
        {text[:1000]}
        
        评分标准：
        1. 0.0-0.3: 小学生水平
        2. 0.4-0.6: 中学生水平
        3. 0.7-0.9: 大学生水平
        4. 1.0: 专业研究人员水平
        
        只需返回分数数字，不要包含其他内容。例如：0.75
        """
        response = self.call_llm(prompt)
        try:
            return min(max(float(response.strip()), 0.0), 1.0)
        except:
            return 0.5  # 默认值

    def identify_concepts(self, text: str) -> List[str]:
        """识别关键概念和专业术语"""
        if not text.strip():
            return []
            
        # 使用缓存
        cache_key = hash(text[:500])
        if cache_key in self.section_cache:
            return self.section_cache[cache_key]
        
        prompt = f"""
        从以下文本中提取关键概念和专业术语（最多5个）：
        {text[:1000]}
        
        要求：
        1. 只提取核心概念，排除常见词汇
        2. 按重要性排序
        3. 按JSON格式返回：{{"concepts": ["概念1", "概念2", ...]}}
        """
        response = self.call_llm(prompt, need_json=True)
        # print("原始返回值：", response)
        
        try:
            # 清理响应字符串（移除多余的标记）
            cleaned_response = response.strip()
            # 移除多余的 ```json 和 json 单词
            cleaned_response = re.sub(r'(```json|json)', '', cleaned_response).strip()
            # 移除多余的反引号
            cleaned_response = re.sub(r'`', '', cleaned_response).strip()
            # print("清理后的格式为：", cleaned_response)
            
            # 尝试加载为JSON
            concepts = []
            if isinstance(cleaned_response, dict):
                concepts = cleaned_response.get("concepts", [])
            else:
                concepts = json.loads(cleaned_response).get("concepts", [])
            
            # 过滤无效概念
            concepts = [c for c in concepts if len(c) > 2 and not c.isdigit() and not c.isspace()]
            
            self.section_cache[cache_key] = concepts
            return concepts
        except json.JSONDecodeError as e:
            print("错误：返回值不是有效的 JSON 格式")
            print(f"JSON 解码错误：{e}")
            return []
        except Exception as e:
            print(f"处理返回值时出错: {e}")
            return []

    def generate_annotation(self, concept: str, context: str, difficulty: float) -> Dict:
        """生成概念批注（使用缓存）"""
        # 检查缓存
        cache_key = f"{concept}-{difficulty:.1f}"
        if cache_key in self.annotation_cache:
            return self.annotation_cache[cache_key]
            
        prompt = f"""
        基于以下上下文，为概念'{concept}'创建中文知识卡片：
        {context[:500]}
        
        要求：
        1. 用1-2句话解释（根据难度{difficulty:.1f}调整专业深度）
        2. 提供1个与上下文相关的简单示例
        3. 添加1个有趣事实
        4. 使用Markdown格式（粗体、列表等）
        
        按JSON格式返回：
        {{"concept": "概念名称",
          "explanation": "解释内容",
          "example": "示例内容",
          "fact": "有趣事实"}}
        """
        response = self.call_llm(prompt, need_json=True)
        # print("知识卡片返回",response)
        try:
            # 清理响应字符串（移除多余的标记）
            cleaned_response = response.strip()
            # 移除多余的 ```json 和 json 单词
            cleaned_response = re.sub(r'(```json|json)', '', cleaned_response).strip()
            # 移除多余的反引号
            cleaned_response = re.sub(r'`', '', cleaned_response).strip()

            # print("清理后的格式为：", cleaned_response)
            if isinstance(cleaned_response, dict):
                annotation = cleaned_response
            else:
                annotation = json.loads(cleaned_response)
            # 验证结构
            if all(key in annotation for key in ['concept', 'explanation', 'example', 'fact']):
                self.annotation_cache[cache_key] = annotation
                return annotation
        except:
            pass
            
        # 默认返回格式
        return {
            "concept": concept,
            "explanation": f"未取得解释",
            "example": f"未取得示例",
            "fact": f"💡 未取得有趣事实"
        }

    def analyze_content(self, structured_doc: Dict, difficulty_threshold: float = 0.7) -> Dict:
        """
        分析Markdown文档内容并生成批注（顺序处理段落）
        :param structured_doc: 结构化文档
        :param difficulty_threshold: 触发简化的难度阈值
        :return: 带批注的文档
        """
        annotated_doc = json.loads(json.dumps(structured_doc))  # 深拷贝
        
        # 处理章节级别的分析
        for section in annotated_doc['sections']:
            # 章节级分析
            section_text = ' '.join(p['text'] for p in section['paragraphs'])
            section_diff = self.assess_difficulty(section_text)
            
            # 打印章节分析信息
            print(f"📦 章节: {section['title']}")
            print(f"   - 段落数量: {len(section['paragraphs'])}")
            print(f"   - 难度评估: {section_diff:.2f}")
            print(f"   - 章节内容: {section_text[:100]}...")  # 打印每段内容的前100个字符
            
            # 识别章节级概念
            concepts = self.identify_concepts(section_text)
            print(f"   - 识别关键概念: {concepts}")
            
            for concept in concepts:
                # 使用章节上下文生成批注
                annotation = self.generate_annotation(concept, section_text, section_diff)
                if annotation:
                    section['annotations'].append(annotation)
        
        # 批量处理所有段落
        all_paragraphs = []
        for section in annotated_doc['sections']:
            for para in section['paragraphs']:
                all_paragraphs.append(para)
        
        # 批量评估段落难度
        difficulties = self.batch_assess_difficulty([p['text'] for p in all_paragraphs])
        
        # 更新难度评分
        for i, para in enumerate(all_paragraphs):
            para['difficulty'] = difficulties[i]
        
        # 批量处理高难度段落
        high_difficulty_paragraphs = []
        for para in all_paragraphs:
            if para['difficulty'] > difficulty_threshold:
                high_difficulty_paragraphs.append(para)
        
        # 批量生成扩展内容
        expanded_contents = self.batch_expand_content(
            [p['raw'] for p in high_difficulty_paragraphs],
            [p['difficulty'] for p in high_difficulty_paragraphs]
        )
        
        # 批量生成易化内容
        explained_contents = self.batch_explain_content(
            [p['raw'] for p in high_difficulty_paragraphs],
            [p['difficulty'] for p in high_difficulty_paragraphs]
        )
        
        # 更新高难度段落
        for i, para in enumerate(high_difficulty_paragraphs):
            para['expanded'] = expanded_contents[i]
            para['explained'] = explained_contents[i]
            para['high_difficulty'] = True
        
        return annotated_doc

    def batch_assess_difficulty(self, texts: List[str]) -> List[float]:
        """批量评估文本难度（顺序处理）"""
        if not texts:
            return []
        
        difficulties = []
        print("评估段落难度……")
        
        # 创建进度条
        progress_bar = tqdm(total=len(texts), desc="评估难度")
        
        for text in texts:
            if not text.strip():
                difficulties.append(0.0)
            else:
                prompt = f"""
                请评估以下文本的阅读难度，给出0-1之间的分数（1为最难）：
                {text[:1000]}
                
                评分标准：
                1. 0.0-0.3: 小学生水平
                2. 0.4-0.6: 中学生水平
                3. 0.7-0.9: 大学生水平
                4. 1.0: 专业研究人员水平
                
                只需返回分数数字，不要包含其他内容。例如：0.75
                """
                
                response = self.call_llm(prompt)
                
                try:
                    score = min(max(float(response.strip()), 0.0), 1.0)
                    difficulties.append(score)
                except:
                    difficulties.append(0.5)  # 默认值
            
            # 更新进度条
            progress_bar.update(1)
        
        progress_bar.close()
        return difficulties

    def batch_expand_content(self, markdowns: List[str], difficulties: List[float]) -> List[str]:
        """批量生成扩展内容（顺序处理）"""
        if not markdowns:
            return []
        
        expanded_contents = []
        print("针对高难度段落进行知识扩展……")
        
        # 创建进度条
        progress_bar = tqdm(total=len(markdowns), desc="知识扩展")
        
        for md, diff in zip(markdowns, difficulties):
            prompt = f"""
            基于以下内容进行联想扩展，搜索相关信息并补齐知识：
            {md[:1500]}
            
            要求：
            1. 基于已有信息进行联想，扩展搜索相关信息（如背景知识、相关概念、应用场景等）
            2. 根据难度{diff:.1f}调整扩展深度和广度
            3. 生成纯文本，不要markdown格式
            """
            
            response = self.call_llm(prompt)
            
            expanded_contents.append(response or "未获取到扩展内容")
            
            # 更新进度条
            progress_bar.update(1)
        
        progress_bar.close()
        return expanded_contents

    def batch_explain_content(self, markdowns: List[str], difficulties: List[float]) -> List[str]:
        """批量生成易化内容（顺序处理）"""
        if not markdowns:
            return []
        
        explained_contents = []
        print("针对高难度段落进行易化学习……")
        
        # 创建进度条
        progress_bar = tqdm(total=len(markdowns), desc="易化学习")
        
        for md, diff in zip(markdowns, difficulties):
            prompt = f"""
            对以下复杂内容进行易化学习处理：
            {md[:1500]}
            
            要求：
            1. 将专业概念转化为易于理解的表述
            2. 添加必要的背景知识和解释
            3. 使用类比、示例等教学技巧
            4. 根据难度{diff:.1f}调整解释深度
            5. 生成纯文本，不要markdown格式
            """
            
            response = self.call_llm(prompt)
            
            explained_contents.append(response or "未生成易化内容")
            
            # 更新进度条
            progress_bar.update(1)
        
        progress_bar.close()
        return explained_contents

    def generate_markdown(self, annotated_doc: Dict) -> str:
        """生成带批注的Markdown文档"""
        # 文档标题和元数据
        md_content = ""
        
        # 如果有明确标题
        if annotated_doc['title'] != "未命名文档":
            md_content += f"# {annotated_doc['title']}\n\n"
        
        # 添加元数据
        if annotated_doc.get('metadata'):
            md_content += "---\n"
            for key, value in annotated_doc['metadata'].items():
                md_content += f"{key}: {value}\n"
            md_content += "---\n\n"
        
        # 添加文档描述
        md_content += "> 本文档已添加AI智能批注，帮助理解关键概念\n\n"
        
        # 生成各章节内容
        for section in annotated_doc['sections']:
            # 根据标题级别生成相应的标题标记
            heading_level = section.get('level', 2)
            heading_marker = '#' * heading_level
            md_content += f"{heading_marker} {section['title']}\n\n"
            
            # 添加章节概念标签
            if section['annotations']:
                concepts = ", ".join(f"**{ann['concept']}**" for ann in section['annotations'])
                md_content += f"**关键概念:** {concepts}\n\n"
            
            # 添加知识卡片
            if section['annotations']:
                md_content += "### 🔖 知识卡片\n\n"
                for annotation in section['annotations']:
                    md_content += f"#### {annotation['concept']}\n"
                    md_content += f"**解释**: {annotation['explanation']}\n\n"
                    md_content += f"**示例**: {annotation['example']}\n\n"
                    md_content += f"**有趣事实**: {annotation['fact']}\n\n"
                    md_content += "---\n"
                md_content += "\n"
            
            # 添加段落
            for para in section['paragraphs']:
                # 添加原段落标识
                md_content += "#### 📄 原始段落\n\n"
                
                # 输出原始段落（使用缩进块）
                md_content += "```markdown\n"
                md_content += f"{para['raw']}\n"
                md_content += "```\n\n"
                
                # 添加难度信息
                md_content += f"**难度评估:** {para.get('difficulty', 0.5):.2f}\n\n"
                
                # 如果是高难度段落，添加扩展内容和易化学习
                if para.get('high_difficulty'):
                    # 知识扩展部分（可展开块）
                    md_content += "<details>\n"
                    md_content += "<summary>📚 知识扩展（点击展开）</summary>\n\n"
                    # 使用纯文本段落形式展示
                    md_content += f"{para.get('expanded', '')}\n\n"
                    md_content += "</details>\n\n"
                    
                    # 易化学习部分（可展开块）
                    md_content += "<details>\n"
                    md_content += "<summary>🎓 易化学习（点击展开）</summary>\n\n"
                    # 使用纯文本段落形式展示
                    md_content += f"{para.get('explained', '')}\n\n"
                    md_content += "</details>\n\n"
                    
                    md_content += "---\n\n"
                else:
                    # 低难度段落添加分隔线
                    md_content += "---\n\n"
    
        # 添加页脚
        md_content += "---\n"
        md_content += "*智能批注由AI生成，旨在辅助理解核心概念*\n"
        md_content += "*新增内容标记为「知识卡片」、「知识扩展」和「易化学习」部分*"
        
        return md_content

    def process(self, markdown_content: str, output_file: str = "annotated_document.md") -> str:
        """
        处理Markdown文档并生成带批注的版本
        :param markdown_content: Markdown格式的文本
        :param output_file: 输出Markdown文件路径
        :return: 生成的Markdown内容
        """
        print("📑 正在解析Markdown结构...")
        structured_doc = self.parse_markdown(markdown_content)
        print(f"✅ 文档解析完成: 共 {len(structured_doc['sections'])} 个章节")
        
        print("🧠 正在分析内容并生成批注...")
        annotated_doc = self.analyze_content(structured_doc)
        concept_count = sum(len(s['annotations']) for s in annotated_doc['sections'])
        print(f"✨ 生成 {concept_count} 个知识卡片批注")
        
        print("📝 正在生成Markdown文档...")
        markdown_content = self.generate_markdown(annotated_doc)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        print(f"🎉 智能批注文档已生成: {output_file}")
        return markdown_content

