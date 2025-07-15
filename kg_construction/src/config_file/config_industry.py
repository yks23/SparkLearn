import os

# Default configuration for the project

# Model provider
model_provider = "chatglm"  # options: "chatglm", "openai", or "silicon"

# Model name
model_name = "glm-4-air"  # e.g., "glm-4-air" or "flash"

# API keys loaded from environment variables
glm_api_key = os.getenv("chatglm_api_key")
openai_api_key = os.getenv("openai_api_key")
silicon_api_key = os.getenv("silicon_api_key")

# Cache path for graph structures (if any)
# Path to the standard prompt files
standard_prompt_path = "./prompt/prompt"
# Path to custom prompt files
target_prompt_path = "./prompt/prompt"
# Path to the prompt files currently used
final_prompt_path = "./prompt/prompt"

# Custom domain or field
target_field = "Industrial Engineering"

# Path to the raw text folder
raw_path = "./raw/industrial_engineering"

# Regex splitting rules for raw text (adjust according to the book structure)
re_expression = [
    r"(# 第\d+部分 .*\n)",
    r"(## 第\d+章 .*\n)",
    r"(## \d+\.\d+ .*\n)",
    r"(## \d+\.\d+\.\d+ .*\n)",
]

max_level = 4

# Unified user input template, usually does not need modification
user_input = r"Please complete the task according to the above requirements\n # User Input:{text}\n Your response:"

# Whether to generate community reports
need_community_report = True

# How to process sections: summarize or split into chunks
section_processing_type = "summary"  # or "split_into_chunks"

# Maximum chunk length
chunk_length = 1000

# How to process chunks: extract entities first then relations, or vice versa
extraction_type = "entity->relation"  # or "relation->entity"

# Whether extraction is done stepwise
is_async = True

# Neo4j connection info (replace with your own credentials or set via environment variables)
NEO4j_URI = "neo4j+s://your-neo4j-uri"
NEO4j_USER = "neo4j"
NEO4j_PASSWORD = "your_password_here"  # Replace with your actual password or use environment variable

# Metadata or results path
metadata_path = "./results/industry"
