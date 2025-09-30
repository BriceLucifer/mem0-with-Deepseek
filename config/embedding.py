from dotenv import load_dotenv
import os

load_dotenv()

class Embedding:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_EMBEDDING_ENDPOINT", os.getenv("AZURE_OPENAI_ENDPOINT"))
        self.api_key = os.getenv("AZURE_EMBEDDING_API_KEY", os.getenv("AZURE_OPENAI_API_KEY"))
        self.api_version = os.getenv("AZURE_EMBEDDING_API_VERSION", "2023-05-15")
        self.deployment_name = os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
