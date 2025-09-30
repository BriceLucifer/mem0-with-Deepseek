from config.neo4j_config import Neo4jConfig
from config.mem0_setting import Mem0Setting
from config.embedding import Embedding
from config.llm import LLM
from mem0 import Memory
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from api.router.chat import router as chat_router
from api.router.memory import router as memory_router
from api.dependencies import cleanup_instances
import time
import logging
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("应用启动中...")
    yield
    logger.info("应用关闭中...")
    await cleanup_instances()

# 创建FastAPI应用
app = FastAPI(
    title="Memory Layer API",
    description="基于mem0的AI对话记忆功能API - 高性能版本",
    version="2.0.0",
    lifespan=lifespan
)

# 性能监控中间件
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    start_time = time.time()
    
    # 添加请求ID
    request_id = f"{int(time.time() * 1000)}-{hash(str(request.url)) % 10000}"
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # 添加性能头
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        # 记录慢请求
        if process_time > 2.0:
            logger.warning(f"慢请求检测: {request.method} {request.url} - {process_time:.2f}s")
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"请求处理失败: {request.method} {request.url} - {process_time:.2f}s - {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "内部服务器错误", "request_id": request_id},
            headers={"X-Request-ID": request_id}
        )

# 限流中间件
request_counts = {}
# 从环境变量读取配置，提供默认值
RATE_LIMIT = int(os.getenv("RATE_LIMIT", 100))

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    current_time = int(time.time() / 60)  # 按分钟计算
    
    key = f"{client_ip}:{current_time}"
    
    if key in request_counts:
        request_counts[key] += 1
        if request_counts[key] > RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后重试"}
            )
    else:
        request_counts[key] = 1
    
    # 清理旧的计数
    old_keys = [k for k in request_counts.keys() if int(k.split(':')[1]) < current_time - 5]
    for old_key in old_keys:
        del request_counts[old_key]
    
    return await call_next(request)

# 安全中间件
allowed_hosts_str = os.getenv("ALLOWED_HOSTS", "*")
allowed_hosts = [h.strip() for h in allowed_hosts_str.split(',')]
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=allowed_hosts
)

# CORS中间件
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in allowed_origins_str.split(',')]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time", "X-Request-ID"]
)

# 注册路由
app.include_router(chat_router, prefix="/api")
app.include_router(memory_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Memory Layer API v2.0 - 高性能版本", 
        "docs": "/docs",
        "services": {
            "chat": "/api/chat",
            "memory": "/api/memory"
        },
        "features": [
            "异步处理",
            "连接池优化",
            "智能缓存",
            "性能监控",
            "限流保护"
        ]
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "2.0.0"
    }

@app.get("/metrics")
async def get_metrics():
    """获取性能指标"""
    return {
        "active_connections": len(request_counts),
        "total_requests": sum(request_counts.values()),
        "timestamp": time.time()
    }



@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception for {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "error": str(exc)},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        workers=1,  # 单进程，因为我们使用了全局状态
        loop="asyncio",
        access_log=True
    )
