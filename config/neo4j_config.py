import os
from dotenv import load_dotenv

load_dotenv()


class Neo4jConfig:
    """Neo4j 数据库连接配置类"""
    
    def __init__(self):
        self.url =  os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.database = os.getenv("NEO4J_DATABASE")
    
    def get_connection_params(self):
        return {
            "provider": "neo4j",
            "config": {
                "url": self.url,
                "username": self.username,
                "password": self.password,
            }
        }