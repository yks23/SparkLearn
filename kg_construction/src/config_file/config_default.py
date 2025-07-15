import os

# Model provider
model_provider = "silicon"  # options: "chatglm", "openai", or "silicon"
# Model name
model_name = "Pro/deepseek-ai/DeepSeek-V3"  # e.g., "glm-4-air" or "flash"

# Your API keys (set as environment variables)
glm_api_key = os.getenv("chatglm_api_key")
openai_api_key = os.getenv("openai_api_key")
silicon_api_key = os.getenv("silicon_api_key")

# Cache path for graph structures (if any)
# Path for standard prompt files
standard_prompt_path = "./prompt/prompt"
# Path for customized prompt files
target_prompt_path = "./prompt/prompt"
# Path for the final prompt used
final_prompt_path = "./prompt/prompt"

# Custom domain or field
target_field = "Physics"

# Path to the source text folder
raw_path = "./raw/university_physics"

# Splitting rules for the source text, which can be adjusted based on the original book structure
re_expression = [r"(# 第\d+部分.*\n)", r"(## 第\d+章.*\n)", r"(## \d+\.\d+.*\n)"]

max_level = 3

# Unified user input template, usually does not need to be changed
user_input = r"Please complete the task according to the above requirements\n # User Input:{text}\n Your response:"

# Whether a community report is needed
need_community_report = True

# Determines how to process sections: either split into chunks or summarize
section_processing_type = "summary"  # or "split_into_chunks"

# Maximum length of a chunk
chunk_length = 1000

# Determines how to process chunks: extract entities first then relations, or vice versa
extraction_type = "entity->relation"  # or "relation->entity"

# Whether the extraction is done stepwise
is_async = True

# Connection details for Neo4j graph database (credentials removed)
NEO4j_URI = "neo4j+s://your-neo4j-uri"  # Replace with your Neo4j URI
NEO4j_USER = "neo4j"                      # Replace with your Neo4j username
NEO4j_PASSWORD = os.getenv("NEO4j_password")  # Set your Neo4j password as environment variable
# Path to metadata or results directory
metadata_path = "./results/physics"
