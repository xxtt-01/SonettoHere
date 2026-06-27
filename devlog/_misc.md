## 2026-06-27 22:27: .gitignore 添加 SQLite 数据库忽略规则
- **文件:**
  - `.gitignore`
- **原因:** Task 2.1.1 — SQLite 数据库文件不应提交到 git
- **决策:** 添加 `api/data/*.db`、`api/data/*.db-wal`、`api/data/*.db-shm` 模式
- **影响范围:** .gitignore

## 2026-06-27: ruff 自动修复 — N806 变量重命名
- **文件:**
  - `setup.py`
- **原因:** ruff N806 规则要求变量名小写，Task 1.2.1
- **决策:** PERSONAS → personas, TEMPLATES → templates，更新全部引用
- **影响范围:** setup.py 构建脚本

## 2026-06-27 20:29: 项目初始化
- **文件:**
  - `CONTEXT.md`
  - `docs/superpowers/plans/2026-06-27-sonettohere-comprehensive-improvement.md`
  - `devlog/`
- **原因:** 项目分析和新用户第一次进入项目，执行标准化初始化流程
- **决策:** 按照 CLAUDE.md 项目规则初始化 devlog、CONTEXT.md、docs/adr 目录
- **影响范围:** 项目基础设施

## 2026-06-27 22:11: 测试配置增强 — pyproject.toml
- **文件:**
  - `pyproject.toml`
- **原因:** 添加 ruff 代码检查配置和 pytest 异步测试配置，设置统一的 lint 规则和测试发现路径
- **决策:** 按任务 1.1.1 要求追加 ruff 配置段和 pytest 配置段到 pyproject.toml 末尾
- **影响范围:** 项目构建配置

## 2026-06-27: [2.2.1] feat: Docker 多阶段构建支持
- **文件:**
  - `Dockerfile`
  - `.dockerignore`
  - `docker-compose.yml`
  - `main.py`
- **原因:** Task 2.2.1 — 为项目创建 Docker 多阶段构建支持，便于容器化部署
- **决策:**
  - 双阶段构建：node:20-alpine 构建前端，python:3.11-slim 运行后端
  - 修改 main.py 的 host 为 0.0.0.0（生产环境），解决 Docker 容器内绑定 127.0.0.1 无法外部访问的问题
  - 数据持久化使用 Docker volumes 挂载 api/data 和 config/personas
- **影响范围:** 项目根目录（Dockerfile、.dockerignore、docker-compose.yml）、主入口（main.py host 绑定逻辑）
