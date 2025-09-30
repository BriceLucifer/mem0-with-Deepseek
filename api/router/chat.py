from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
from mem0 import Memory
from config.llm import LLM
from api.dependencies import get_memory_agent  # 使用异步版本
from api.models import (
    ChatRequest, ChatResponse, MemorySearchRequest, MemorySearchResponse,
    ConversationHistoryRequest
)
from core.agent import MemoryAgent
from datetime import datetime
import json
import asyncio

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/message")
async def send_message(request: ChatRequest, agent: MemoryAgent = Depends(get_memory_agent)):
    """发送消息并获取AI回复，支持流式输出"""
    try:
        # 如果请求流式输出
        if request.stream:
            stream_metadata = request.metadata.copy() if request.metadata else {}
            stream_metadata['stream'] = True
            
            result = await agent.chat(
                user_id=request.user_id,
                message=request.message,
                session_id=request.session_id,
                metadata=stream_metadata
            )
            
            if result.get('stream'):
                async def generate():
                    # 首先发送元数据
                    metadata_chunk = {
                        "type": "metadata",
                        "user_id": result["user_id"],
                        "session_id": result["session_id"],
                        "memories_used": result["memories_used"],
                        "timestamp": result["timestamp"].isoformat()
                    }
                    yield f"data: {json.dumps(metadata_chunk)}\n\n"
                    
                    # 然后发送流式内容
                    async for chunk in result["response_generator"]:
                        if chunk:
                            chunk_data = {
                                "type": "content",
                                "content": chunk
                            }
                            yield f"data: {json.dumps(chunk_data)}\n\n"
                    
                    # 发送结束标记
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                
                return StreamingResponse(
                    generate(),
                    media_type="text/plain",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive"
                    }
                )
        
        # 普通模式
        result = await agent.chat(
            user_id=request.user_id,
            message=request.message,
            session_id=request.session_id,
            metadata=request.metadata
        )
        
        return ChatResponse(
            response=result["response"],
            user_id=result["user_id"],
            session_id=result["session_id"],
            memories_used=result["memories_used"],
            timestamp=result["timestamp"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理消息时出错: {str(e)}")

@router.post("/search-memories", response_model=MemorySearchResponse)
async def search_memories(request: MemorySearchRequest, agent: MemoryAgent = Depends(get_memory_agent)):
    """搜索用户记忆"""
    try:
        memories = await agent.search_memories(request.user_id, request.query, request.limit)
        return MemorySearchResponse(
            memories=memories,
            total_count=len(memories)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索记忆时出错: {str(e)}")

@router.get("/memories/{user_id}")
async def get_user_memories(user_id: str, agent: MemoryAgent = Depends(get_memory_agent)):
    """获取用户所有记忆"""
    try:
        memories = await agent.get_all_memories(user_id)
        return {"memories": memories, "total_count": len(memories)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取记忆时出错: {str(e)}")

@router.delete("/memory/{memory_id}")
async def delete_memory(memory_id: str, agent: MemoryAgent = Depends(get_memory_agent)):
    """删除指定记忆"""
    try:
        success = await agent.delete_memory(memory_id)
        if success:
            return {"message": "记忆删除成功"}
        else:
            raise HTTPException(status_code=404, detail="记忆未找到或删除失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除记忆时出错: {str(e)}")

@router.delete("/memories/{user_id}")
async def clear_user_memories(user_id: str, agent: MemoryAgent = Depends(get_memory_agent)):
    """清除用户所有记忆"""
    try:
        success = await agent.clear_user_memories(user_id)
        if success:
            return {"message": f"用户 {user_id} 的所有记忆已清除"}
        else:
            raise HTTPException(status_code=500, detail="清除记忆失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除记忆时出错: {str(e)}")

@router.post("/stream")
async def stream_message(request: ChatRequest, agent: MemoryAgent = Depends(get_memory_agent)):
    """流式输出对话"""
    try:
        # 设置流式模式
        stream_metadata = request.metadata.copy() if request.metadata else {}
        stream_metadata['stream'] = True
        
        result = await agent.chat(
            user_id=request.user_id,
            message=request.message,
            session_id=request.session_id,
            metadata=stream_metadata
        )
        
        if result.get('stream'):
            async def generate():
                # 首先发送元数据
                metadata_chunk = {
                    "type": "metadata",
                    "user_id": result["user_id"],
                    "session_id": result["session_id"],
                    "memories_used": result["memories_used"],
                    "timestamp": result["timestamp"].isoformat()
                }
                yield f"data: {json.dumps(metadata_chunk)}\n\n"
                
                # 然后发送流式内容
                async for chunk in result["response_generator"]:
                    if chunk:
                        chunk_data = {
                            "type": "content",
                            "content": chunk
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # 发送结束标记
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive"
                }
            )
        else:
            # 如果不支持流式，返回普通响应
            return ChatResponse(
                response=result["response"],
                user_id=result["user_id"],
                session_id=result["session_id"],
                memories_used=result["memories_used"],
                timestamp=result["timestamp"]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"流式对话时出错: {str(e)}")

@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now()}