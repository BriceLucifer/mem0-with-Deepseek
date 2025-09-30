import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from mem0 import Memory
from config.llm import LLM
import aiohttp
import asyncio
import json
import time
from functools import wraps
import logging
from contextlib import asynccontextmanager

# 添加缓存装饰器
def async_cache(ttl_seconds=300):
    """异步缓存装饰器"""
    cache = {}
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            current_time = time.time()
            
            # 检查缓存
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if current_time - timestamp < ttl_seconds:
                    return result
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            cache[cache_key] = (result, current_time)
            
            # 清理过期缓存
            expired_keys = [
                key for key, (_, timestamp) in cache.items()
                if current_time - timestamp >= ttl_seconds
            ]
            for key in expired_keys:
                del cache[key]
            
            return result
        return wrapper
    return decorator

class MemoryAgent:
    """高性能异步记忆Agent"""
    
    def __init__(self, memory: Memory, llm: LLM):
        self.memory = memory
        self.llm = llm
        self.conversation_history: Dict[str, List[Dict]] = {}
        self._session = None
        self._session_lock = asyncio.Lock()
        self.logger = logging.getLogger(__name__)
        
        # 连接池配置
        self._connector = aiohttp.TCPConnector(
            limit=100,  # 总连接池大小
            limit_per_host=30,  # 每个主机的连接数
            ttl_dns_cache=300,  # DNS缓存时间
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        # 超时配置
        self._timeout = aiohttp.ClientTimeout(
            total=30,  # 总超时时间
            connect=5,  # 连接超时
            sock_read=10  # 读取超时
        )
        self._pending_requests = {}  # 添加请求去重
    
    @asynccontextmanager
    async def get_session(self):
        """获取HTTP会话的上下文管理器"""
        async with self._session_lock:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession(
                    connector=self._connector,
                    timeout=self._timeout,
                    headers={
                        "User-Agent": "MemoryAgent/1.0",
                        "Connection": "keep-alive"
                    }
                )
        
        try:
            yield self._session
        except Exception as e:
            self.logger.error(f"HTTP会话错误: {e}")
            raise
    
    async def _call_llm_with_retry(self, messages: List[Dict[str, str]], max_retries: int = 3) -> str:
        """带重试机制的LLM调用"""
        headers = {
            "api-key": self.llm.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000,
            "stream": False
        }
        
        # 构建Azure OpenAI的URL
        azure_url = f"{self.llm.endpoint}/openai/deployments/{self.llm.deployment}/chat/completions?api-version={self.llm.api_version}"
        
        for attempt in range(max_retries):
            try:
                async with self.get_session() as session:
                    async with session.post(
                        azure_url,
                        headers=headers,
                        json=payload
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result["choices"][0]["message"]["content"]
                        elif response.status == 429:  # 速率限制
                            wait_time = 2 ** attempt
                            self.logger.warning(f"速率限制，等待 {wait_time} 秒后重试")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            response.raise_for_status()
                            
            except asyncio.TimeoutError:
                self.logger.warning(f"LLM调用超时，第 {attempt + 1} 次重试")
                if attempt == max_retries - 1:
                    return "抱歉，服务暂时不可用，请稍后重试。"
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"LLM调用失败 (尝试 {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return f"抱歉，我现在无法回复。错误：{str(e)}"
                await asyncio.sleep(1)
        
        return "抱歉，服务暂时不可用。"
    
    @async_cache(ttl_seconds=600)  # 增加缓存时间到10分钟
    async def _get_relevant_memories_cached(self, user_id: str, query: str, limit: int = 5) -> List[str]:
        """带缓存的记忆检索"""
        return await self._get_relevant_memories_raw(user_id, query, limit)
    
    async def _get_relevant_memories_raw(self, user_id: str, query: str, limit: int = 5) -> List[str]:
        """原始记忆检索方法"""
        try:
            loop = asyncio.get_event_loop()
            search_results = await loop.run_in_executor(
                None, 
                lambda: self.memory.search(query, user_id=user_id, limit=limit)
            )
            
            memories = []
            
            if isinstance(search_results, dict) and "results" in search_results:
                results = search_results["results"]
                for result in results:
                    if isinstance(result, dict):
                        memory_text = result.get("memory") or result.get("text") or result.get("content")
                        if memory_text:
                            memories.append(memory_text)
            elif isinstance(search_results, list):
                for result in search_results:
                    if isinstance(result, dict):
                        memory_text = result.get("memory") or result.get("text") or result.get("content")
                        if memory_text:
                            memories.append(memory_text)
                    elif isinstance(result, str):
                        memories.append(result)
                    else:
                        memories.append(str(result))
            
            return memories
            
        except Exception as e:
            self.logger.error(f"获取记忆时出错: {e}")
            return []
    
    async def _build_context_messages_optimized(self, user_message: str, user_id: str, session_id: str) -> List[Dict[str, str]]:
        """优化的上下文构建"""
        # 并发获取记忆和会话历史
        memories_task = self._get_relevant_memories_cached(user_id, user_message)
        
        # 获取会话历史（本地操作，无需异步）
        session_key = f"{user_id}_{session_id}"
        recent_history = self.conversation_history.get(session_key, [])[-10:]
        
        # 等待记忆检索完成
        relevant_memories = await memories_task
        
        # 构建系统提示
        system_prompt = "你是一个智能助手，能够记住用户的偏好和历史对话。"
        if relevant_memories:
            memory_context = "\n".join([f"- {memory}" for memory in relevant_memories])
            system_prompt += f"\n\n以下是用户的相关记忆信息：\n{memory_context}\n\n请基于这些记忆信息来回复用户，特别要考虑用户的偏好和兴趣。"
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(recent_history)
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    async def chat(self, user_id: str, message: str, session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """高性能异步对话处理 - 使用正确的mem0模式"""
        start_time = time.time()
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        session_key = f"{user_id}_{session_id}"
        
        # 初始化会话历史
        if session_key not in self.conversation_history:
            self.conversation_history[session_key] = []
        
        try:
            loop = asyncio.get_event_loop()
            
            # 1. 检索相关记忆
            relevant_memories = await loop.run_in_executor(
                None,
                lambda: self.memory.search(query=message, user_id=user_id, limit=5)
            )
            
            # 处理记忆格式
            memories_text = []
            if isinstance(relevant_memories, dict) and "results" in relevant_memories:
                for memory in relevant_memories["results"]:
                    if isinstance(memory, dict) and "memory" in memory:
                        memories_text.append(memory["memory"])
            elif isinstance(relevant_memories, list):
                for memory in relevant_memories:
                    if isinstance(memory, dict):
                        memory_content = memory.get("memory") or memory.get("text") or memory.get("content")
                        if memory_content:
                            memories_text.append(memory_content)
            
            # 2. 构建带记忆上下文的对话
            memories_context = "\n".join([f"- {memory}" for memory in memories_text]) if memories_text else ""
            system_prompt = f"你是一个智能助手，能够记住用户的偏好和历史对话。"
            if memories_context:
                system_prompt += f"\n\n用户相关记忆信息：\n{memories_context}\n\n请基于这些记忆信息来回复用户。"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            # 3. 使用langchain调用LLM (通过mem0的配置)
            from config.mem0_setting import Mem0Setting
            from config.llm import LLM
            from config.embedding import Embedding
            
            llm_config = LLM()
            embedding_config = Embedding()
            mem0_setting = Mem0Setting(llm_config, embedding_config)
            llm_client = mem0_setting.mem0_config["llm"]["config"]["model"]
            
            # 检查是否支持流式输出
            stream_mode = metadata.get('stream', False) if metadata else False
            
            if stream_mode:
                # 流式输出模式
                response_stream = await loop.run_in_executor(
                    None,
                    lambda: llm_client.stream(messages)
                )
                
                # 收集流式输出内容
                response_chunks = []
                async def collect_stream():
                    for chunk in response_stream:
                        if hasattr(chunk, 'content'):
                            response_chunks.append(chunk.content)
                            yield chunk.content
                
                response = ''.join(response_chunks)
                return {
                    "stream": True,
                    "response_generator": collect_stream(),
                    "user_id": user_id,
                    "session_id": session_id,
                    "memories_used": memories_text,
                    "timestamp": datetime.now()
                }
            else:
                # 普通模式
                response_obj = await loop.run_in_executor(
                    None,
                    lambda: llm_client.invoke(messages)
                )
                response = response_obj.content
            
            # 4. 异步保存记忆到后台任务 (不阻塞响应)
            conversation_messages = [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response}
            ]
            
            # 后台异步保存，不等待完成
            asyncio.create_task(self._save_memory_background(
                conversation_messages, user_id, session_id, metadata
            ))
            
            # 更新会话历史
            self.conversation_history[session_key].extend(conversation_messages)
            
            processing_time = time.time() - start_time
            self.logger.info(f"对话处理完成，耗时: {processing_time:.2f}秒")
            
            return {
                "response": response,
                "user_id": user_id,
                "session_id": session_id,
                "memories_used": memories_text,
                "timestamp": datetime.now(),
                "processing_time": processing_time
            }
            
        except Exception as e:
            self.logger.error(f"对话处理失败: {e}")
            return {
                "response": "抱歉，处理您的请求时出现了问题。",
                "user_id": user_id,
                "session_id": session_id,
                "memories_used": [],
                "timestamp": datetime.now(),
                "error": str(e)
            }
    
    async def _save_memory_background(self, conversation_messages: List[Dict], user_id: str, session_id: str, metadata: Optional[Dict[str, Any]]):
        """后台异步保存记忆任务"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.memory.add(
                    conversation_messages, 
                    user_id=user_id, 
                    metadata={
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        **(metadata or {})
                    }
                )
            )
            self.logger.info(f"后台记忆保存成功: user_id={user_id}")
        except Exception as e:
            self.logger.error(f"后台记忆保存失败: {e}")
    
    async def _save_memory_async(self, user_id: str, session_id: str, user_message: str, response: str, metadata: Optional[Dict[str, Any]]):
        """异步保存记忆（后台任务）"""
        try:
            conversation_messages = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": response}
            ]
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.memory.add(
                    conversation_messages, 
                    user_id=user_id, 
                    metadata={
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        **(metadata or {})
                    }
                )
            )
        except Exception as e:
            self.logger.error(f"后台保存记忆失败: {e}")
    
    async def search_memories(self, user_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """异步搜索用户记忆"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self.memory.search(query, user_id=user_id, limit=limit)
            )
        except Exception as e:
            print(f"搜索记忆时出错: {e}")
            return []
    
    async def get_all_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """异步获取用户所有记忆"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self.memory.get_all(user_id=user_id)
            )
        except Exception as e:
            print(f"获取所有记忆时出错: {e}")
            return []
    
    async def delete_memory(self, memory_id: str) -> bool:
        """异步删除指定记忆"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.memory.delete(memory_id=memory_id)
            )
            return True
        except Exception as e:
            print(f"删除记忆时出错: {e}")
            return False
    
    async def clear_user_memories(self, user_id: str) -> bool:
        """异步清除用户所有记忆"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.memory.delete_all(user_id=user_id)
            )
            # 同时清除会话历史
            keys_to_remove = [key for key in self.conversation_history.keys() if key.startswith(f"{user_id}_")]
            for key in keys_to_remove:
                del self.conversation_history[key]
            return True
        except Exception as e:
            print(f"清除用户记忆时出错: {e}")
            return False
    
    async def close(self):
        """清理资源"""
        if self._session and not self._session.closed:
            await self._session.close()
        if self._connector:
            await self._connector.close()
    
    
    class CircuitBreaker:
        def __init__(self, failure_threshold=5, timeout=60):
            self.failure_threshold = failure_threshold
            self.timeout = timeout
            self.failure_count = 0
            self.last_failure_time = None
            self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        
        async def call(self, func, *args, **kwargs):
            if self.state == 'OPEN':
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = 'HALF_OPEN'
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                if self.state == 'HALF_OPEN':
                    self.state = 'CLOSED'
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = 'OPEN'
                    
                raise e
    
    async def _get_relevant_memories_with_dedup(self, user_id: str, query: str, limit: int = 5):
        """带去重的记忆检索"""
        request_key = f"{user_id}:{hash(query)}:{limit}"
        
        if request_key in self._pending_requests:
            return await self._pending_requests[request_key]
        
        # 创建新的请求任务
        task = asyncio.create_task(self._get_relevant_memories_cached(user_id, query, limit))
        self._pending_requests[request_key] = task
        
        try:
            result = await task
            return result
        finally:
            # 清理完成的请求
            self._pending_requests.pop(request_key, None)