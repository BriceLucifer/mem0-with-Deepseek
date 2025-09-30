from fastapi import APIRouter, Depends, HTTPException
from typing import List
from core.memory_service import MemoryService
from api.dependencies import get_memory_service
from api.models import (
    AddMemoryRequest, BatchAddMemoryRequest, UpdateMemoryRequest,
    MemorySearchRequest, MemoryResponse, MemoryStatsResponse
)
from datetime import datetime

router = APIRouter(prefix="/memory", tags=["memory"])

@router.post("/add", response_model=MemoryResponse)
async def add_memory(request: AddMemoryRequest, service: MemoryService = Depends(get_memory_service)):
    """添加单个记忆"""
    result = service.add_memory(request.content, request.user_id, request.metadata)
    
    return MemoryResponse(
        success=result["success"],
        message=result["message"],
        data=result,
        timestamp=datetime.now()
    )

@router.post("/batch-add", response_model=MemoryResponse)
async def batch_add_memories(request: BatchAddMemoryRequest, service: MemoryService = Depends(get_memory_service)):
    """批量添加记忆"""
    result = service.batch_add_memories(request.memories, request.user_id)
    
    return MemoryResponse(
        success=result["success"],
        message=result["message"],
        data=result,
        timestamp=datetime.now()
    )

@router.post("/search", response_model=MemoryResponse)
async def search_memories(request: MemorySearchRequest, service: MemoryService = Depends(get_memory_service)):
    """搜索记忆"""
    result = service.search_memories(request.query, request.user_id, request.limit)
    
    return MemoryResponse(
        success=result["success"],
        message=result["message"],
        data=result,
        timestamp=datetime.now()
    )

@router.get("/user/{user_id}", response_model=MemoryResponse)
async def get_user_memories(user_id: str, service: MemoryService = Depends(get_memory_service)):
    """获取用户所有记忆"""
    result = service.get_all_memories(user_id)
    
    return MemoryResponse(
        success=result["success"],
        message=result["message"],
        data=result,
        timestamp=datetime.now()
    )

@router.delete("/memory/{memory_id}", response_model=MemoryResponse)
async def delete_memory(memory_id: str, service: MemoryService = Depends(get_memory_service)):
    """删除指定记忆"""
    result = service.delete_memory(memory_id)
    
    return MemoryResponse(
        success=result["success"],
        message=result["message"],
        data=result,
        timestamp=datetime.now()
    )

@router.delete("/user/{user_id}", response_model=MemoryResponse)
async def delete_user_memories(user_id: str, service: MemoryService = Depends(get_memory_service)):
    """删除用户所有记忆"""
    result = service.delete_user_memories(user_id)
    
    return MemoryResponse(
        success=result["success"],
        message=result["message"],
        data=result,
        timestamp=datetime.now()
    )

@router.put("/update", response_model=MemoryResponse)
async def update_memory(request: UpdateMemoryRequest, service: MemoryService = Depends(get_memory_service)):
    """更新记忆"""
    result = service.update_memory(request.memory_id, request.content, request.metadata)
    
    return MemoryResponse(
        success=result["success"],
        message=result["message"],
        data=result,
        timestamp=datetime.now()
    )

@router.get("/stats/{user_id}", response_model=MemoryResponse)
async def get_memory_stats(user_id: str, service: MemoryService = Depends(get_memory_service)):
    """获取用户记忆统计信息"""
    result = service.get_memory_stats(user_id)
    
    return MemoryResponse(
        success=result["success"],
        message="统计信息获取成功" if result["success"] else result.get("message", "获取失败"),
        data=result,
        timestamp=datetime.now()
    )

@router.get("/health")
async def memory_health_check():
    """记忆服务健康检查"""
    return {"status": "healthy", "service": "memory", "timestamp": datetime.now()}