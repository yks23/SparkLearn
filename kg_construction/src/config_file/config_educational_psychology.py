import os
from ..utils.path_resolver import get_prompt_path

# 使用路径解析工具获取prompt路径
prompt_path = get_prompt_path()
standard_prompt_path = prompt_path
target_prompt_path = prompt_path
final_prompt_path = prompt_path

# Custom domain
target_field = "Educational Psychology"

# Path to raw text folder
raw_path = "./raw/educational_psychology"

# Regex patterns for splitting source text (adjust according to book structure)
re_expression = [
    r"(## Part \d+.*\n)",
    r"(## Chapter \d+.*\n)",
    r"(## \d+\.\d+.*\n)"
]
max_level = 3

# Unified user input template; generally does not need modification
user_input = r"Please complete the task according to the above requirements\n # User Input:{text}\n Your response:"

# Whether to generate community reports
need_community_report = True

# How to process sections: "summary" or "split_into_chunks"
section_processing_type = "summary"

# Maximum chunk length
chunk_length = 1000

# How to process chunks: "entity->relation" or "relation->entity"
extraction_type = "entity->relation"

# Whether extraction is stepwise
is_async = True

# Neo4j connection info (replace with your own credentials or use env vars)
NEO4j_URI = "neo4j+s://your-neo4j-uri"
NEO4j_USER = "neo4j"
NEO4j_PASSWORD = "your_password_here"  # Replace with your actual password or set as env var

# Output directory path
metadata_path = "./results/educational_psychology"
