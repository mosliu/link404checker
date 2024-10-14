# 使用官方Python运行时作为父镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件到容器中
COPY . /app/

# 安装项目依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 依赖
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0

# 安装 Playwright 浏览器
RUN playwright install chromium

# 确保脚本有执行权限
RUN chmod +x /app/app.py

# 暴露端口5000供外部访问
EXPOSE 5000

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 运行app.py
CMD ["python", "/app/app.py"]