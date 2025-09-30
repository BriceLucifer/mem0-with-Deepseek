#!/usr/bin/env python3
"""
流式对话测试脚本
用于测试 mem0 长记忆对话系统的流式输出功能
"""

import requests
import json
import time
import sys
from typing import Optional

class StreamChatClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def stream_chat(self, user_id: str, message: str, session_id: Optional[str] = None):
        """发送流式对话请求并实时打印结果"""
        
        url = f"{self.base_url}/api/chat/message"
        data = {
            "user_id": user_id,
            "message": message,
            "stream": True
        }
        
        if session_id:
            data["session_id"] = session_id
        
        print(f"🤖 发送消息: {message}")
        print(f"👤 用户ID: {user_id}")
        if session_id:
            print(f"💬 会话ID: {session_id}")
        print("-" * 50)
        
        try:
            # 发送流式请求
            response = self.session.post(
                url, 
                json=data, 
                headers={"Content-Type": "application/json"},
                stream=True,
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"❌ 请求失败: {response.status_code} - {response.text}")
                return
            
            print("📡 开始接收流式数据...\n")
            
            # 解析流式响应
            metadata = None
            content_buffer = []
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    data_str = line[6:]  # 移除 "data: " 前缀
                    
                    try:
                        data = json.loads(data_str)
                        
                        if data["type"] == "metadata":
                            metadata = data
                            print(f"📋 元数据信息:")
                            print(f"   用户ID: {data['user_id']}")
                            print(f"   会话ID: {data['session_id']}")
                            print(f"   使用记忆: {data['memories_used']}")
                            print(f"   时间戳: {data['timestamp']}")
                            print("\n🤖 AI回复:")
                            
                        elif data["type"] == "content":
                            content = data["content"]
                            content_buffer.append(content)
                            # 实时打印内容，不换行，模拟打字机效果
                            for char in content:
                                print(char, end='', flush=True)
                                time.sleep(0.02)  # 添加微小延迟，增强视觉效果
                            
                        elif data["type"] == "done":
                            print("\n")
                            print("-" * 50)
                            print(f"✅ 流式输出完成!")
                            print(f"📝 完整回复: {''.join(content_buffer)}")
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON解析错误: {e}")
                        continue
                        
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求错误: {e}")
        except KeyboardInterrupt:
            print(f"\n\n⏹️ 用户中断")
    
    def normal_chat(self, user_id: str, message: str, session_id: Optional[str] = None):
        """发送普通对话请求"""
        
        url = f"{self.base_url}/api/chat/message"
        data = {
            "user_id": user_id,
            "message": message,
            "stream": False
        }
        
        if session_id:
            data["session_id"] = session_id
        
        print(f"🤖 发送消息: {message}")
        print(f"👤 用户ID: {user_id}")
        if session_id:
            print(f"💬 会话ID: {session_id}")
        print("-" * 50)
        
        try:
            response = self.session.post(
                url, 
                json=data, 
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 普通模式回复:")
                print(f"📝 内容: {result['response']}")
                print(f"📋 使用记忆: {result['memories_used']}")
                print(f"⏰ 时间: {result['timestamp']}")
            else:
                print(f"❌ 请求失败: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求错误: {e}")

def main():
    client = StreamChatClient()
    
    print("=" * 60)
    print("🚀 Mem0 长记忆对话流式测试脚本")
    print("=" * 60)
    
    # 测试1: 建立记忆
    print("\n📝 测试1: 建立用户记忆")
    client.stream_chat(
        user_id="demo_user", 
        message="你好，我是张三，我住在上海，喜欢编程和旅游",
        session_id="demo_session_001"
    )
    
    time.sleep(2)
    
    # 测试2: 记忆检索
    print("\n\n🧠 测试2: 记忆检索测试")
    client.stream_chat(
        user_id="demo_user", 
        message="你还记得我叫什么名字吗？我住在哪里？有什么爱好？",
        session_id="demo_session_002"
    )
    
    time.sleep(2)
    
    # 测试3: 普通模式对比
    print("\n\n📊 测试3: 普通模式对比")
    client.normal_chat(
        user_id="demo_user", 
        message="请简单介绍一下Python编程语言",
        session_id="demo_session_003"
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n👋 再见!")
        sys.exit(0)