## 2026-06-27 22:07: 生产环境前端静态文件服务
- **文件:**
  - `api/server.py`
- **原因:** Phase 3 Task 1 — Docker 镜像包含 web/dist/ 但服务器未挂载，导致生产环境无法访问前端
- **决策:** 在 create_app() 末尾添加条件性 StaticFiles 挂载，仅 SONETTO_ENV=production 生效，不影响 Vite 开发模式
- **影响范围:** api/server.py

## 2026-06-27: 默认启用 SQLite 会话存储模式
- **文件:**
  - `api/server.py`
- **原因:** Task 2.1.3 — 将生产环境 SessionManager 默认模式从 memory 切换为 sqlite，实现会话持久化
- **决策:** 仅修改 server.py 传入 `mode="sqlite"`，不修改 SessionManager 默认值以保持测试不受影响
- **影响范围:** api/server.py

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

## 2026-06-28: 添加 SQLite 连接验证函数
- **文件:**
  - `api/database/__init__.py`
- **原因:** Risk 1 — 在 SQLite 多线程场景下，提供连接有效性检查手段，增强健壮性
- **决策:** 新增 `verify_connection()` 函数，内部执行 `SELECT 1` 探活，使用 try/except 包裹确保不抛异常
- **影响范围:** api/database/__init__.py（新增函数，不改变现有行为）

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

## 2026-06-28: Provider SQLite 迁移 — 配置表 + 双模式存储 + YAML 导入
- **文件:**
  - `api/database/migrations/002_create_providers.py` (new)
  - `api/database/provider_store.py` (new)
  - `api/providers/store.py`
  - `api/server.py`
  - `tests/test_api/test_provider_store.py` (new)
- **原因:** Task 2.1.4 — 将 ProviderConfigStore 从 YAML 文件存储迁移到 SQLite，沿用 SessionManager 双模式模式
- **决策:**
  - 新增 migration 002 创建 `providers` 表
  - 新增 `DatabaseProviderStore` 类封装 providers 表 CRUD
  - `ProviderConfigStore` 添加 `mode` 参数（`"yaml"` | `"sqlite"` | `"memory"`），默认 `"yaml"` 向后兼容
  - `server.py` 切换为 `mode="sqlite"`，启动时尝试从 YAML 导入再 fallback 到 .env
  - 新增 `import_from_yaml` 静态方法支持一键迁移
  - 9 个测试覆盖三种模式 + YAML 导入，全量 214 测试无回归
- **影响范围:** api/database/, api/providers/store.py, api/server.py, tests/

## 2026-06-28: 修复 PR #194 审查发现的三个隐藏问题
- **文件:**
  - `api/server.py`
  - `api/database/migrations/001_create_sessions.py`
  - `api/session_manager.py`
- **原因:** PR #194 深度审查发现 lifespan 中迁移在 SQLite 初始化之后运行（新部署会崩溃）、迁移 001 使用 julianday 而非 Unix 时间戳、get_or_create 不持久化到 SQLite
- **根因:**
  1. `lifespan()` 中 `run_migrations()` 放在 `SessionManager(mode="sqlite")` 之后，表未创建就查表
  2. `session_messages.created_at DEFAULT (julianday('now'))` 返回儒略日而非 Unix 时间戳，与项目不一致
  3. `get_or_create()` 创建 session 时只写内存不写 SQLite
- **决策:**
  1. 将 `run_migrations()` 移到 `lifespan()` 的绝对开头（#0）
  2. `julianday('now')` 改为 `strftime('%s', 'now')` 与迁移 002 一致
  3. `get_or_create()` 新建 session 时同步写入 `_db_store.save_session()`
- **影响范围:** api/server.py, api/database/migrations/, api/session_manager.py
## 2026-07-03: 添加 sessions 表 cleanup 索引
- **文件:**
  - `api/database/migrations/003_add_sessions_indexes.py`
- **原因:** `DELETE FROM sessions WHERE last_active < ? AND is_const = 0` 触发全表扫描
- **决策:** 新增 migration 003，添加 `idx_sessions_cleanup(last_active, is_const)` 复合索引
- **影响范围:** api/database/
