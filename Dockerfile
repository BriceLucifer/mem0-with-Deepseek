# 使用官方Python 3.13镜像
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量，避免Python写入.pyc文件
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 安装uv（比pip快）和项目依赖
RUN pip install uv
COPY pyproject.toml uv.lock* ./
# 安装依赖
# 使用 --system 将包安装到系统 site-packages
RUN uv pip install --system --no-cache -r pyproject.toml

# 安装 Gunicorn 和 Uvicorn
RUN uv pip install --system gunicorn uvicorn

# 复制所有文件到工作目录
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令，使用Gunicorn管理Uvicorn workers
# --workers: 进程数，通常设置为 2 * CPU核心数 + 1
# --worker-class: 指定使用Uvicorn的worker
# --bind: 监听的地址和端口
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "main:app"]