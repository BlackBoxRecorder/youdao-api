# 使用官方Python运行时作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装uv包管理器
RUN pip install uv

# 复制项目依赖文件
COPY pyproject.toml uv.lock ./

# 安装项目依赖
RUN uv sync --frozen

# 复制项目代码
COPY . .

# 创建音频目录（如果不存在）
RUN mkdir -p audio

# 暴露端口
EXPOSE 5088

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# 启动应用
CMD ["uv", "run", "python", "main.py"]