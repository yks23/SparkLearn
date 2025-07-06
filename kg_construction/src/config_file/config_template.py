import os

standard_prompt_path = "kg_construction/prompt/prompt"
# Path for customized prompt files
target_prompt_path = "kg_construction/prompt/prompt"
# Path for the final prompt used
final_prompt_path = "kg_construction/prompt/prompt"

# Custom domain or field
target_field = ""

# Path to the source text folder
raw_path = ""
glm_api_key = os.getenv("chatglm_api_key")
openai_api_key = os.getenv("openai_api_key")
silicon_api_key = os.getenv("silicon_api_key")

# Splitting rules for the source text, which can be adjusted based on the original book structure
re_expression = [r"(# .*\n)", r"(## .*\n)", r"(### .*\n)"]

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
metadata_path = "./outputs"
