from .llm import LLM
from .embedding import Embedding
from .neo4j_config import Neo4jConfig
from langchain_openai import AzureChatOpenAI

class Mem0Setting:
    """Mem0 配置类，整合 LLM、嵌入器、向量存储和图存储配置"""
    
    def __init__(self, llm: LLM, embedding: Embedding, enable_graph: bool = False, neo4j_config: Neo4jConfig = None):
        """初始化配置
        
        Args:
            llm: LLM 配置对象
            embedding: 嵌入器配置对象
            enable_graph: 是否启用图记忆功能
            neo4j_config: Neo4j 连接配置
        """
        # 创建 LangChain Azure OpenAI 实例
        azure_llm = AzureChatOpenAI(
            azure_deployment=llm.deployment,
            azure_endpoint=llm.endpoint,
            api_key=llm.api_key,
            api_version=llm.api_version,
            temperature=1.0,
            max_completion_tokens=2000
        )
        
        self.mem0_config = {
            "llm": {
                "provider": "langchain",
                "config": {
                    "model": azure_llm
                }
            },
            "embedder": {
                "provider": "azure_openai",
                "config": {
                    "model": embedding.deployment_name,
                    "azure_kwargs": {
                        "azure_deployment": embedding.deployment_name,
                        "api_version": embedding.api_version,
                        "azure_endpoint": embedding.endpoint,
                        "api_key": embedding.api_key
                    }
                }
            },
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "memory_collection",
                    "path": "./chroma_db"
                }
            }
        }
        
        # 如果启用图记忆，添加图存储配置
        if enable_graph :
            self.mem0_config["graph_store"] = neo4j_config.get_connection_params()
    
    def get_mem0_config(self) -> dict:
        """返回适用于 Mem0 的完整配置
        
        Returns:
            dict: Mem0 配置字典
        """
        return self.mem0_config
    
    def get_llm_config(self) -> dict:
        """获取 LLM 配置
        
        Returns:
            dict: LLM 配置字典
        """
        return self.mem0_config["llm"]
    
    def get_embedder_config(self) -> dict:
        """获取嵌入器配置
        
        Returns:
            dict: 嵌入器配置字典
        """
        return self.mem0_config["embedder"]
    
    def get_vector_store_config(self) -> dict:
        """获取向量存储配置
        
        Returns:
            dict: 向量存储配置字典
        """
        return self.mem0_config["vector_store"]
    
    def get_graph_store_config(self) -> dict:
        """获取图存储配置
        
        Returns:
            dict: 图存储配置字典
        """
        return self.mem0_config.get("graph_store", {})
    
    def is_graph_enabled(self) -> bool:
        """检查是否启用了图记忆
        
        Returns:
            bool: 是否启用图记忆
        """
        return "graph_store" in self.mem0_config
    
    def get_config(self) -> dict:
        """获取所有的配置结构提

        Returns:
            dict: 向量存储配置字典
        """
        return self.mem0_config