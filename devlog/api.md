## 2026-06-27: DatabaseSessionStore + SessionManager 双模式支持
- **文件:**
  - `api/database/session_store.py` (new)
  - `api/session_manager.py`
  - `tests/test_api/test_session_manager_sqlite.py` (new)
- **原因:** Task 2.1.2 — 基于 SQLite 的 SessionStore，为 SessionManager 添加 sqlite 持久化模式
- **决策:**
  - 新增 `DatabaseSessionStore` 类，封装 sessions 表的 CRUD 操作
  - SessionManager 新增 `mode` 参数 (`"memory"` | `"sqlite"`)，默认 `"memory"` 保证向后兼容
  - sqlite 模式下，每次 create/delete 同步写入数据库
  - 初始化时从 DB 加载已有会话到内存
  - 注意：`get_or_create` 目前只操作内存，不写入 DB（保持原有行为）
- **影响范围:** api/database/, api/session_manager.py, tests/

## 2026-06-27 22:27: SQLite 基础设施 — 连接管理 + 迁移系统 + 会话表
- **文件:**
  - `api/database/__init__.py` (new)
  - `api/database/migrations/__init__.py` (new)
  - `api/database/migrations/001_create_sessions.py` (new)
  - `api/server.py`
- **原因:** Task 2.1.1 — 创建 SQLite 数据库基础设施，替换 SessionManager 的内存存储为持久化方案
- **决策:**
  - 使用 `threading.local()` 实现线程安全的 SQLite 连接单例
  - 迁移系统基于数字前缀文件名自动发现 + `_migrations` 表追踪
  - 001 迁移创建 `sessions` 表和 `session_messages` 表
  - 在 `lifespan` 启动时运行迁移，非致命错误不阻断启动
- **影响范围:** api/database/, api/server.py

## 2026-06-27: ruff 自动修复 + 手动修复 — B904/SIM/PTH/N806
- **文件:**
  - `api/callbacks/tool_extractors.py`
  - `api/callbacks/websocket_callback.py`
  - `api/const_session_store.py`
  - `api/context_usage.py`
  - `api/providers/__init__.py`
  - `api/providers/store.py`
  - `api/routes/balance.py`
  - `api/routes/chat.py`
  - `api/routes/env_vars.py`
  - `api/routes/files.py`
  - `api/routes/mcp.py`
  - `api/routes/news.py`
  - `api/routes/path_whitelist.py`
  - `api/routes/providers.py`
  - `api/routes/sessions.py`
  - `api/routes/skills.py`
  - `api/routes/sonetto_blocker.py`
  - `api/server.py`
- **原因:** 全项目 ruff lint 修复，Task 1.2.1
- **决策:**
  - B904: 所有 `raise ... from` 链补全（`from e` / `from None`）
  - SIM105: 静默异常处理改用 `contextlib.suppress`
  - SIM108: if-else 简化为三元表达式
  - PTH: `open()` → `Path.open()`，`os.path` → `pathlib`
  - N806/N802: 变量/函数名驼峰→小写下划线
  - ARG001/ARG002: 未使用参数加 `_` 前缀
  - F841: 删除未使用变量
- **影响范围:** api 模块全部子包

## 2026-06-27: 统一错误处理中间件 + 类型注解完善
- **文件:**
  - `api/middleware/error_handler.py` (new)
  - `api/server.py`
  - `api/session_manager.py`
- **原因:** Task 1.2.2 + 1.2.3 代码质量改进
- **决策:**
  - 新增 `unified_error_handler` 全局异常处理中间件，统一 JSON 错误响应格式
  - HTTPException 和未捕获异常分别处理，生产环境不暴露内部细节
  - 为 `session_manager.py` 补充 `__init__` 的 `-> None` 返回类型注解
- **影响范围:** api/middleware/, api/server.py, api/session_manager.py