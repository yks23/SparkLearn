import os
from utils.api import single_conversation

class SimplifiedAnnotator:
    def __init__(self):
        self.annotation_cache = {}
    
    def process(self, markdown_content: str, output_file: str = "simplified_annotated_document.md") -> str:
        """
        处理Markdown文档并生成带批注的版本
        :param markdown_content: Markdown格式的文本
        :param output_file: 输出Markdown文件路径
        :return: 生成的Markdown内容
        """
        print("📑 正在处理Markdown文档...")

        prompt = f"""
        你是一个文档智能批注助手，请为以下Markdown文档添加智能批注：
        
        {markdown_content[:15000]}  # 截取部分内容避免超长
        
        要求：
        1. 识别重要概念和专业术语（最多10个），为每个概念生成一个可展开的知识卡片
        2. 先对文章结构进行识别，使用markdown格式进行分层，最大的段落用“#”，往后依次递减。所以你的返回一定是从“#”开始的。
        3. 对各个段落难度进行评分
        4. 对高难度内容（复杂概念或专业术语密集部分）添加知识扩展
        5. 对高难度内容进行易化学习（转化为易于理解的语言）
        6. 返回的开头和结尾不要用"```markdown"包裹
        7. 所有新增内容使用Markdown的可展开块格式：
           <details>
           <summary>标题（点击展开）</summary>
           内容
           </details>
        
        具体格式：
        - 知识卡片：
          <details>
          <summary>📚 知识卡片: 概念名称</summary>
          
          **解释**: 1-2句简洁解释
          
          **示例**: 相关示例
          
          **有趣事实**: 相关有趣事实
          </details>
        
        - 知识扩展：
          <details>
          <summary>📚 知识扩展</summary>
          
          补充背景知识、相关概念和应用场景
          </details>
        
        - 易化学习：
          <details>
          <summary>🎓 易化学习</summary>
          
          使用简单语言、类比和示例解释复杂内容
          </details>
        
        插入位置：
        - 知识卡片插入在概念首次出现的位置之后
        - 知识扩展和易化学习插入在高难度段落之后
        
        你需要返回的只有：分过层的原文内容，添加的批注和知识扩展内容，以及易化学习内容。千万不要添加其他任何内容，比如“以上是……”之类的。
        返回完整的Markdown文档。
        """
        
        print("🤖 正在批注...")
        annotated_content = self.call_llm(prompt)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(annotated_content)
        
        print(f"🎉 智能批注文档已生成: {output_file}")
        return annotated_content
    
    def call_llm(self, prompt: str) -> str:
        """
        调用大模型API
        :param prompt: 提示词
        :return: 模型响应内容
        """
        # 使用统一的系统提示
        system_prompt = "你是一个文档智能批注助手，负责为Markdown文档添加批注、知识扩展和易化学习内容。"
        
        try:
            response = single_conversation(
                system_prompt=system_prompt,
                user_input=prompt,
                need_json=False,
                show_progress=True
            )
            return response
        except Exception as e:
            print(f"API调用失败: {e}")
            return "智能批注生成失败，请重试。"

