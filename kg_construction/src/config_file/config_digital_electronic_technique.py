import os
from ..utils.path_resolver import get_prompt_path

# 使用路径解析工具获取prompt路径
prompt_path = get_prompt_path()
standard_prompt_path = prompt_path
target_prompt_path = prompt_path
final_prompt_path = prompt_path

# Custom domain or field
target_field = "Digital Circuit Technology"

# Path to raw text folder
raw_path = "./raw/digital_electronic_technique"

# Regex rules to split source text; adjust according to the book's structure
re_expression = [
    r"(## 第\d+章.*\n)",
    r"(### \d+\.\d+节.*\n)",
    r"(#### \d+\.\d+\.\d+节.*\n)",
]
max_level = 3

# Unified user input template; usually does not require modification
user_input = r"Please complete the task according to the above requirements\n # User Input:{text}\n Your response:"

# Whether to generate community reports
need_community_report = True

# How to process sections: "summary" or "split_into_chunks"
section_processing_type = "summary"  # or "split_into_chunks"

# Maximum length of each chunk
chunk_length = 1000

# How to process chunks: extract entities first then relations, or the opposite
extraction_type = "entity->relation"  # or "relation->entity"

# Whether extraction is done stepwise
is_async = True

# Neo4j connection info (replace with your actual credentials or use environment variables)
NEO4j_URI = "neo4j+s://your-neo4j-uri"
NEO4j_USER = "neo4j"
NEO4j_PASSWORD = (
    "your_password_here"  # Replace with actual password or load from env var
)

# Output directory for generated files
metadata_path = "./results/ele"
