# Memory Layer - AI对话记忆系统 v2.0

基于 mem0 的高性能智能AI对话记忆管理系统，支持长期记忆存储、检索和上下文感知对话。

## ✨ 核心特性

- 🧠 **智能记忆管理** - 基于mem0的向量化记忆存储和检索
- 💬 **上下文感知对话** - AI能够记住用户偏好和历史对话
- 🔍 **语义搜索** - 支持自然语言搜索相关记忆
- 👥 **多用户支持** - 独立的用户记忆空间
- 📊 **图数据库支持** - 使用Neo4j存储复杂关系
- 🚀 **高性能异步API** - 基于FastAPI的RESTful接口
- 📈 **性能监控** - 内置请求监控和限流保护
- 🔒 **安全防护** - CORS、限流、可信主机等安全中间件
- 📖 **自动文档** - FastAPI自动生成的交互式API文档

## 🏗️ 系统架构

```
memory_layer/
├── api/                    # API层
│   ├── dependencies.py     # 依赖注入和实例管理
│   ├── models.py          # Pydantic数据模型
│   └── router/            # 路由模块
│       ├── chat.py        # 聊天对话API
│       └── memory.py      # 记忆管理API
├── config/                # 配置层
│   ├── embedding.py       # 嵌入模型配置
│   ├── llm.py            # 大语言模型配置
│   ├── mem0_setting.py   # mem0配置
│   └── neo4j_config.py   # Neo4j图数据库配置
├── core/                  # 核心业务层
│   ├── agent.py          # AI对话代理
│   ├── memory_service.py # 记忆管理服务
│   ├── memory/           # 记忆模块
│   └── storage/          # 存储模块
├── utils/                 # 工具模块
├── main.py               # 应用入口
└── pyproject.toml        # 项目配置
```

## 🚀 快速开始

### 环境要求

- **Python** >= 3.13
- **Neo4j** 数据库 (可选，用于图关系存储)
- **Azure OpenAI API Key** (用于LLM)
- **Azure OpenAI API Key** (用于嵌入模型)

### 1. 安装依赖

```bash
# 使用uv安装依赖（推荐）
uv sync

# 或使用pip
pip install -e .
```

### 2. 环境配置

创建 `.env` 文件并配置以下环境变量：

```env
# Azure OpenAI API配置 (用于LLM)
AZURE_OPENAI_ENDPOINT=https://aoai00001.openai.azure.com
AZURE_OPENAI_API_KEY=your_azure_api_key
AZURE_OPENAI_DEPLOYMENT=o4-mini

# Azure OpenAI配置（用于嵌入）
AZURE_OPENAI_API_KEY=your_azure_api_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_EMBEDDING_DEPLOYMENT=your_embedding_deployment
AZURE_EMBEDDING_MODEL=text-embedding-3-small

# Neo4j配置（可选）
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password

# Redis配置（可选，用于分布式缓存）
REDIS_URL=redis://localhost:6379
```

### 3. 启动服务

#### 开发模式

```bash
# 方式1：使用uv运行（推荐）
uv run python main.py

# 方式2：直接运行
python main.py

# 方式3：使用uvicorn
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 生产模式

```bash
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 单进程模式（推荐，因为使用了全局状态）
uv run uvicorn main:app --host 0.0.0.0 --port 8000

# 多进程模式（需要配置外部状态存储）
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# 使用Gunicorn + Uvicorn workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Docker部署

```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .

RUN pip install uv && uv sync

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  memory-layer:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_DEPLOYMENT=${AZURE_OPENAI_DEPLOYMENT}
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
    volumes:
      - ./chroma_db:/app/chroma_db
```

### 4. 验证安装

服务启动后访问：

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **性能指标**: http://localhost:8000/metrics
- **服务信息**: http://localhost:8000/

## 📚 完整API文档

### 基础信息

- **Base URL**: `http://localhost:8000`
- **API前缀**: `/api`
- **Content-Type**: `application/json`

### 1. 聊天对话API

#### 发送消息 `POST /api/chat/message`

与AI进行对话，自动管理记忆上下文。

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "message": "我喜欢科幻电影，特别是《星际穿越》",
    "session_id": "session_001",
    "metadata": {
      "source": "web",
      "timestamp": "2024-01-01T10:00:00Z"
    }
  }'
```

**响应示例：**
```json
{
  "response": "我记住了你喜欢科幻电影，特别是《星际穿越》。这是一部关于时间和空间的精彩电影。你还喜欢其他类型的电影吗？",
  "user_id": "alice",
  "session_id": "session_001",
  "memories_used": ["mem_id_1", "mem_id_2"],
  "timestamp": "2024-01-01T10:00:01Z"
}
```

#### 搜索记忆 `POST /api/chat/search-memories`

搜索用户的相关记忆。

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/chat/search-memories" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "query": "电影偏好",
    "limit": 5
  }'
```

#### 获取用户记忆 `GET /api/chat/memories/{user_id}`

获取指定用户的所有记忆。

**请求示例：**
```bash
curl -X GET "http://localhost:8000/api/chat/memories/alice"
```

#### 删除记忆 `DELETE /api/chat/memory/{memory_id}`

删除指定的记忆。

**请求示例：**
```bash
curl -X DELETE "http://localhost:8000/api/chat/memory/mem_id_123"
```

#### 清除用户记忆 `DELETE /api/chat/memories/{user_id}`

清除用户的所有记忆。

**请求示例：**
```bash
curl -X DELETE "http://localhost:8000/api/chat/memories/alice"
```

### 2. 记忆管理API

#### 添加记忆 `POST /api/memory/add`

手动添加单个记忆。

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/memory/add" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "content": "用户偏好使用Python进行数据分析",
    "metadata": {
      "category": "preferences",
      "topic": "programming",
      "confidence": 0.9
    }
  }'
```

**响应示例：**
```json
{
  "success": true,
  "message": "记忆添加成功",
  "data": {
    "memory_id": "mem_id_456",
    "user_id": "alice",
    "content": "用户偏好使用Python进行数据分析"
  },
  "timestamp": "2024-01-01T10:05:00Z"
}
```

#### 批量添加记忆 `POST /api/memory/batch-add`

批量添加多个记忆。

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/memory/batch-add" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "memories": [
      {
        "content": "喜欢早上喝咖啡",
        "metadata": {"category": "habits"}
      },
      {
        "content": "工作时间是9-17点",
        "metadata": {"category": "schedule"}
      }
    ]
  }'
```

#### 搜索记忆 `POST /api/memory/search`

基于语义搜索记忆。

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/memory/search" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "query": "编程语言偏好",
    "limit": 10
  }'
```

#### 获取用户记忆 `GET /api/memory/user/{user_id}`

获取用户的所有记忆。

**请求示例：**
```bash
curl -X GET "http://localhost:8000/api/memory/user/alice"
```

#### 更新记忆 `PUT /api/memory/update`

更新现有记忆。

**请求示例：**
```bash
curl -X PUT "http://localhost:8000/api/memory/update" \
  -H "Content-Type: application/json" \
  -d '{
    "memory_id": "mem_id_456",
    "content": "用户偏好使用Python和JavaScript进行开发",
    "metadata": {
      "category": "preferences",
      "topic": "programming",
      "updated": true
    }
  }'
```

#### 删除记忆 `DELETE /api/memory/memory/{memory_id}`

删除指定记忆。

**请求示例：**
```bash
curl -X DELETE "http://localhost:8000/api/memory/memory/mem_id_456"
```

#### 删除用户记忆 `DELETE /api/memory/user/{user_id}`

删除用户的所有记忆。

**请求示例：**
```bash
curl -X DELETE "http://localhost:8000/api/memory/user/alice"
```

#### 获取记忆统计 `GET /api/memory/stats/{user_id}`

获取用户记忆的统计信息。

**请求示例：**
```bash
curl -X GET "http://localhost:8000/api/memory/stats/alice"
```

**响应示例：**
```json
{
  "success": true,
  "message": "统计信息获取成功",
  "data": {
    "user_id": "alice",
    "total_memories": 25,
    "date_distribution": {
      "2024-01-01": 10,
      "2024-01-02": 15
    },
    "category_distribution": {
      "preferences": 8,
      "habits": 7,
      "schedule": 5,
      "other": 5
    }
  },
  "timestamp": "2024-01-01T10:10:00Z"
}
```

### 3. 系统监控API

#### 健康检查 `GET /health`

检查服务健康状态。

**请求示例：**
```bash
curl -X GET "http://localhost:8000/health"
```

**响应示例：**
```json
{
  "status": "healthy",
  "timestamp": 1704110400.123,
  "version": "2.0.0"
}
```

#### 性能指标 `GET /metrics`

获取系统性能指标。

**请求示例：**
```bash
curl -X GET "http://localhost:8000/metrics"
```

**响应示例：**
```json
{
  "active_connections": 5,
  "total_requests": 1250,
  "timestamp": 1704110400.123
}
```

#### 服务信息 `GET /`

获取服务基本信息。

**请求示例：**
```bash
curl -X GET "http://localhost:8000/"
```

## 🔧 核心组件

### MemoryAgent

核心AI对话代理，负责：
- 管理对话历史和会话状态
- 调用LLM生成智能回复
- 自动存储和检索相关记忆
- 提供上下文感知的对话体验

### MemoryService

记忆管理服务，提供：
- 记忆的CRUD操作
- 批量记忆处理
- 语义搜索和相似度匹配
- 记忆统计和分析

### 配置系统

模块化的配置管理：
- **LLM配置** - Azure OpenAI API集成
- **嵌入模型配置** - Azure OpenAI嵌入服务
- **向量数据库配置** - ChromaDB本地存储
- **图数据库配置** - Neo4j关系存储

## 🎯 使用场景

- **个人AI助手** - 记住用户偏好、习惯和历史对话
- **智能客服系统** - 维护客户历史记录和偏好
- **教育平台** - 跟踪学习进度和个性化推荐
- **内容推荐系统** - 基于历史行为的智能推荐
- **知识管理平台** - 构建个人或企业知识图谱

## 🛠️ 开发指南

### 添加新的API端点

1. 在 `api/models.py` 中定义Pydantic数据模型
2. 在相应的路由文件中添加端点实现
3. 在 `main.py` 中注册新路由
4. 更新API文档

### 扩展记忆功能

1. 在 `core/memory_service.py` 中添加新的业务方法
2. 在 `api/router/memory.py` 中暴露HTTP API
3. 更新数据模型和响应格式
4. 添加相应的测试用例

### 自定义LLM配置

1. 修改 `config/llm.py` 中的模型配置
2. 更新 `core/agent.py` 中的调用逻辑
3. 调整提示词和参数设置

## 📊 性能优化

### 内置优化特性

- **异步处理** - 全异步API设计，支持高并发
- **连接池** - 数据库连接复用和管理
- **智能缓存** - 记忆检索结果缓存
- **限流保护** - 基于IP的请求频率限制
- **性能监控** - 请求时间和资源使用监控

### 生产环境建议

- 使用Redis作为分布式缓存
- 配置负载均衡器
- 启用日志聚合和监控
- 设置合适的worker数量
- 配置数据库连接池大小

## 🔍 故障排除

### 常见问题

1. **构建错误** - 确保 `pyproject.toml` 中包含正确的包配置
2. **API Key错误** - 检查 `.env` 文件中的API密钥配置
3. **数据库连接失败** - 验证Neo4j和Redis连接配置
4. **内存不足** - 调整ChromaDB和向量存储配置

### 日志和调试

```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
uv run python main.py

# 查看性能指标
curl http://localhost:8000/metrics

# 健康检查
curl http://localhost:8000/health
```

## 🤝 贡献指南

1. Fork 项目仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [mem0](https://github.com/mem0ai/mem0) - 强大的记忆管理框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [Neo4j](https://neo4j.com/) - 图数据库支持
- [ChromaDB](https://www.trychroma.com/) - 向量数据库
- [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) - 大语言模型服务

---


        