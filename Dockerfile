# === Stage 1: Build Frontend ===
FROM node:20-alpine AS frontend
WORKDIR /build/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ .
RUN npm run build

# === Stage 2: Python Backend ===
FROM python:3.11-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY agent/ agent/
COPY api/ api/
COPY config/ config/
COPY tools/ tools/
COPY memory/ memory/
COPY macros/ macros/
COPY main.py version.py ./

# 复制前端构建产物
COPY --from=frontend /build/web/dist /app/web/dist

# 数据目录卷
VOLUME ["/app/api/data", "/app/config/personas"]

EXPOSE 8000

ENV SONETTO_ENV=production

CMD ["python", "main.py"]
