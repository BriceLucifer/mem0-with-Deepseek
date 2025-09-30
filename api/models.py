from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    stream: Optional[bool] = False  # 是否使用流式输出

class ChatResponse(BaseModel):
    response: str
    user_id: str
    session_id: str
    memories_used: List[str] = []
    timestamp: datetime

class MemorySearchRequest(BaseModel):
    user_id: str
    query: str
    limit: Optional[int] = 10

class MemorySearchResponse(BaseModel):
    memories: List[Dict[str, Any]]
    total_count: int

class ConversationHistoryRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    limit: Optional[int] = 50

# 新增记忆管理相关模型
class AddMemoryRequest(BaseModel):
    user_id: str
    content: str
    note_id: Optional[str] = None  # 关联的笔记ID
    metadata: Optional[Dict[str, Any]] = None

class BatchAddMemoryRequest(BaseModel):
    user_id: str
    memories: List[Dict[str, Any]]

class UpdateMemoryRequest(BaseModel):
    memory_id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class MemoryResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime

class MemoryStatsResponse(BaseModel):
    user_id: str
    total_memories: int
    date_distribution: Dict[str, int]
    category_distribution: Dict[str, int]
    timestamp: datetime