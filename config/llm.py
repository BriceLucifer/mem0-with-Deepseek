from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# Azure LLM类 获取到可能用到的api
class LLM:
    def __init__(self):
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT")  # 添加model属性
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")