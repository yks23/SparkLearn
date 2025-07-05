import os
from typing import Dict
import logging
from dataclasses import dataclass

from src.config import (
    standard_prompt_path,
    target_prompt_path,
    user_input,
    target_field,
    raw_content
)
from src.utils import communicate_with_agent

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PromptFile:
    """提示文件的数据类"""
    name: str
    content: str
    needs_example: bool = False
    input_dependency: str = None  # 依赖的输入文件

class PromptGenerator:
    """提示生成器类"""
    def __init__(self):
        # 定义需要处理的文件列表及其依赖关系
        self.files = [
            PromptFile("async_extraction_from_raw_1.txt", "", True, raw_content),
            PromptFile("async_extraction_from_raw_2.txt", "", True, "async_extraction_from_raw_1.txt"),
            PromptFile("community_report_2.txt", "", True, raw_content),
            PromptFile("async_extraction_from_report_1.txt", "", True, "community_report_2.txt"),
            PromptFile("async_extraction_from_report_2.txt", "", True, "async_extraction_from_report_1.txt"),
            PromptFile("sync_extraction_from_raw.txt", "", True, raw_content),
            PromptFile("community_report_1.txt", ""),
            PromptFile("entity_augmented_generation.txt", ""),
            PromptFile("inc_entity_augmented_generation.txt", ""),
            PromptFile("inc_relation_augmented_generation.txt", ""),
            PromptFile("relation_augmented_generation.txt", ""),
            PromptFile("aggreation_prompt.txt", ""),
            PromptFile("relation_detection_prompt.txt", "")
            
        ]
        self.output: Dict[str, str] = {}

    def _read_file(self, filepath: str) -> str:
        """读取文件内容"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            raise

    def _write_file(self, filepath: str, content: str):
        """写入文件内容"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Error writing file {filepath}: {e}")
            raise

    def _process_content(self, content: str) -> str:
        """处理文件内容：移除示例部分并替换目标字段"""
        return content.split("# Example")[0].replace("物理", target_field)

    def _generate_example(self, prompt_file: PromptFile) -> str:
        """为提示生成示例"""
        # 确定输入内容
        input_content = (
            self.output.get(prompt_file.input_dependency)
            if prompt_file.input_dependency in self.output
            else prompt_file.input_dependency
        )

        # 生成响应
        try:
            response = communicate_with_agent(
                system_prompt=prompt_file.content,
                user_input=user_input.replace("{text}", input_content),
                need_json=False,
                need_batch=False
            )
            logger.info(f"Generated example for {prompt_file.name}")
            return response
        except Exception as e:
            logger.error(f"Error generating example for {prompt_file.name}: {e}")
            raise

    def generate(self, need_example: bool = False):
        """生成提示文件"""
        logger.info("Starting prompt generation process")

        try:
            # 读取并处理所有文件
            for prompt_file in self.files:
                # 读取文件内容
                filepath = os.path.join(standard_prompt_path, prompt_file.name)
                content = self._read_file(filepath)
                processed_content = self._process_content(content)
                prompt_file.content = processed_content

                # 写入处理后的内容
                target_filepath = os.path.join(target_prompt_path, prompt_file.name)
                self._write_file(target_filepath, processed_content)

                # 如果需要示例且文件需要示例
                if need_example and prompt_file.needs_example:
                    # 生成示例
                    example_response = self._generate_example(prompt_file)
                    
                    # 更新输出字典
                    self.output[prompt_file.name] = example_response
                    
                    # 添加示例到内容中
                    content_with_example = (
                        f"{processed_content}\n# Example\n"
                        f"## UserInput{prompt_file.input_dependency}\n"
                        f"## YourOutput {example_response}"
                    )
                    
                    # 写入包含示例的内容
                    self._write_file(target_filepath, content_with_example)

            logger.info("Prompt generation completed successfully")

        except Exception as e:
            logger.error(f"Error in prompt generation: {e}")
            raise

def generate_prompt(need_example: bool = False):
    """主函数"""
    generator = PromptGenerator()
    generator.generate(need_example)

if __name__ == "__main__":
    generate_prompt()
