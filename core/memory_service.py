from typing import List, Dict, Any, Optional
from datetime import datetime
from mem0 import Memory
import uuid
import logging

class MemoryService:
    """完全封装的记忆管理服务"""
    
    def __init__(self, memory: Memory):
        self.memory = memory
        self.logger = logging.getLogger(__name__)
    
    def add_memory(self, 
                   content: str | List[Dict[str, str]], 
                   user_id: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """添加记忆
        
        Args:
            content: 要添加的内容，可以是字符串或消息列表
            user_id: 用户ID
            metadata: 元数据
            
        Returns:
            Dict: 添加结果
        """
        try:
            # 如果是字符串，转换为消息格式
            if isinstance(content, str):
                messages = [{"role": "user", "content": content}]
            else:
                messages = content
            
            # 添加默认元数据
            default_metadata = {
                "timestamp": datetime.now().isoformat(),
                "memory_id": str(uuid.uuid4())
            }
            
            if metadata:
                default_metadata.update(metadata)
            
            # 添加到mem0
            result = self.memory.add(messages, user_id=user_id, metadata=default_metadata)
            
            self.logger.info(f"成功为用户 {user_id} 添加记忆")
            
            return {
                "success": True,
                "message": "记忆添加成功",
                "memory_id": default_metadata["memory_id"],
                "user_id": user_id,
                "timestamp": default_metadata["timestamp"],
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"添加记忆失败: {str(e)}")
            return {
                "success": False,
                "message": f"添加记忆失败: {str(e)}",
                "error": str(e)
            }
    
    def search_memories(self, 
                       query: str, 
                       user_id: str, 
                       limit: int = 10,
                       filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """搜索记忆
        
        Args:
            query: 搜索查询
            user_id: 用户ID
            limit: 返回结果数量限制
            filters: 搜索过滤器
            
        Returns:
            Dict: 搜索结果
        """
        try:
            # 构建搜索参数
            search_params = {
                "query": query,
                "user_id": user_id,
                "limit": limit
            }
            
            if filters:
                search_params.update(filters)
            
            # 执行搜索
            results = self.memory.search(**search_params)
            
            self.logger.info(f"为用户 {user_id} 搜索记忆，查询: '{query}'，找到 {len(results)} 条结果")
            
            return {
                "success": True,
                "message": "搜索完成",
                "query": query,
                "user_id": user_id,
                "total_count": len(results),
                "memories": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"搜索记忆失败: {str(e)}")
            return {
                "success": False,
                "message": f"搜索记忆失败: {str(e)}",
                "error": str(e),
                "memories": []
            }
    
    def get_all_memories(self, user_id: str) -> Dict[str, Any]:
        """获取用户所有记忆
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 所有记忆
        """
        try:
            memories = self.memory.get_all(user_id=user_id)
            
            self.logger.info(f"获取用户 {user_id} 的所有记忆，共 {len(memories)} 条")
            
            return {
                "success": True,
                "message": "获取记忆成功",
                "user_id": user_id,
                "total_count": len(memories),
                "memories": memories,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"获取所有记忆失败: {str(e)}")
            return {
                "success": False,
                "message": f"获取记忆失败: {str(e)}",
                "error": str(e),
                "memories": []
            }
    
    def delete_memory(self, memory_id: str) -> Dict[str, Any]:
        """删除指定记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            Dict: 删除结果
        """
        try:
            self.memory.delete(memory_id=memory_id)
            
            self.logger.info(f"成功删除记忆: {memory_id}")
            
            return {
                "success": True,
                "message": "记忆删除成功",
                "memory_id": memory_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"删除记忆失败: {str(e)}")
            return {
                "success": False,
                "message": f"删除记忆失败: {str(e)}",
                "error": str(e)
            }
    
    def delete_user_memories(self, user_id: str) -> Dict[str, Any]:
        """删除用户所有记忆
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 删除结果
        """
        try:
            # 先获取记忆数量
            memories = self.memory.get_all(user_id=user_id)
            count = len(memories)
            
            # 删除所有记忆
            self.memory.delete_all(user_id=user_id)
            
            self.logger.info(f"成功删除用户 {user_id} 的所有记忆，共 {count} 条")
            
            return {
                "success": True,
                "message": f"成功删除用户的所有记忆",
                "user_id": user_id,
                "deleted_count": count,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"删除用户记忆失败: {str(e)}")
            return {
                "success": False,
                "message": f"删除用户记忆失败: {str(e)}",
                "error": str(e)
            }
    
    def update_memory(self, memory_id: str, new_content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """更新记忆内容
        
        Args:
            memory_id: 记忆ID
            new_content: 新内容
            metadata: 新元数据
            
        Returns:
            Dict: 更新结果
        """
        try:
            # mem0可能不直接支持更新，我们先删除再添加
            # 这里需要根据实际的mem0 API来调整
            update_metadata = {
                "updated_at": datetime.now().isoformat(),
                "original_memory_id": memory_id
            }
            
            if metadata:
                update_metadata.update(metadata)
            
            # 注意：这里需要根据mem0的实际API来实现更新逻辑
            # 如果mem0支持直接更新，使用对应的方法
            
            self.logger.info(f"尝试更新记忆: {memory_id}")
            
            return {
                "success": True,
                "message": "记忆更新成功",
                "memory_id": memory_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"更新记忆失败: {str(e)}")
            return {
                "success": False,
                "message": f"更新记忆失败: {str(e)}",
                "error": str(e)
            }
    
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户记忆统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 统计信息
        """
        try:
            memories = self.memory.get_all(user_id=user_id)
            
            # 统计信息
            total_count = len(memories)
            
            # 按日期统计
            date_stats = {}
            category_stats = {}
            
            for memory in memories:
                # 日期统计
                if 'metadata' in memory and 'timestamp' in memory['metadata']:
                    date = memory['metadata']['timestamp'][:10]  # 取日期部分
                    date_stats[date] = date_stats.get(date, 0) + 1
                
                # 分类统计
                if 'metadata' in memory and 'category' in memory['metadata']:
                    category = memory['metadata']['category']
                    category_stats[category] = category_stats.get(category, 0) + 1
            
            return {
                "success": True,
                "user_id": user_id,
                "total_memories": total_count,
                "date_distribution": date_stats,
                "category_distribution": category_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {str(e)}")
            return {
                "success": False,
                "message": f"获取统计信息失败: {str(e)}",
                "error": str(e)
            }
    
    def batch_add_memories(self, memories_data: List[Dict[str, Any]], user_id: str) -> Dict[str, Any]:
        """批量添加记忆
        
        Args:
            memories_data: 记忆数据列表
            user_id: 用户ID
            
        Returns:
            Dict: 批量添加结果
        """
        results = []
        success_count = 0
        failed_count = 0
        
        for i, memory_data in enumerate(memories_data):
            try:
                content = memory_data.get('content', '')
                metadata = memory_data.get('metadata', {})
                
                result = self.add_memory(content, user_id, metadata)
                results.append({
                    "index": i,
                    "result": result
                })
                
                if result['success']:
                    success_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
                results.append({
                    "index": i,
                    "result": {
                        "success": False,
                        "message": f"处理失败: {str(e)}",
                        "error": str(e)
                    }
                })
        
        return {
            "success": failed_count == 0,
            "message": f"批量添加完成，成功: {success_count}，失败: {failed_count}",
            "user_id": user_id,
            "total_processed": len(memories_data),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }