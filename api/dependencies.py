from functools import lru_cache
import asyncio
from contextlib import asynccontextmanager
from mem0 import Memory
from config.neo4j_config import Neo4jConfig
from config.mem0_setting import Mem0Setting
from config.embedding import Embedding
from config.llm import LLM
from core.memory_service import MemoryService
from core.agent import MemoryAgent
import logging

# 全局实例缓存
_instances = {}
_locks = {}

@asynccontextmanager
async def get_instance_lock(key: str):
    """获取实例锁"""
    if key not in _locks:
        _locks[key] = asyncio.Lock()
    async with _locks[key]:
        yield

@lru_cache()
def get_memory_instance() -> Memory:
    """获取单例的Memory实例（优化版）"""
    if 'memory' not in _instances:
        try:
            llm = LLM()
            embedding = Embedding()
            # 暂时禁用Neo4j图数据库功能进行测试
            azure_setting = Mem0Setting(llm, embedding, False, None)
            mem0_config = azure_setting.get_mem0_config()
            _instances['memory'] = Memory.from_config(mem0_config)
            logging.info("Memory实例创建成功")
        except Exception as e:
            logging.error(f"创建Memory实例失败: {e}")
            raise
    return _instances['memory']

@lru_cache()
def get_llm_instance() -> LLM:
    """获取LLM实例"""
    if 'llm' not in _instances:
        _instances['llm'] = LLM()
    return _instances['llm']

async def get_memory_agent() -> MemoryAgent:
    """获取记忆Agent实例（异步版本）"""
    async with get_instance_lock('agent'):
        if 'agent' not in _instances:
            memory = get_memory_instance()
            llm = get_llm_instance()
            _instances['agent'] = MemoryAgent(memory, llm)
            logging.info("MemoryAgent实例创建成功")
    return _instances['agent']

@lru_cache()
def get_memory_service() -> MemoryService:
    """获取记忆服务实例"""
    if 'memory_service' not in _instances:
        memory = get_memory_instance()
        _instances['memory_service'] = MemoryService(memory)
    return _instances['memory_service']

# 清理函数
async def cleanup_instances():
    """清理所有实例"""
    if 'agent' in _instances:
        await _instances['agent'].close()
    _instances.clear()
    logging.info("所有实例已清理")