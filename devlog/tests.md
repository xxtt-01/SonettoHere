## 2026-06-27 22:11: 测试配置增强 — conftest
- **文件:**
  - `tests/conftest.py`
  - `tests/test_api/conftest.py`
- **原因:** 新增 full_app 和 async_client fixture，创建 API 测试共享 fixtures，为后续单元测试奠定基础
- **决策:**
  - tests/conftest.py 保持向后兼容，新增 full_app（完整应用工厂，Mock LLM）和 async_client（异步 HTTP 客户端，支持 LifespanManager）
  - tests/test_api/conftest.py 使用懒导入避免依赖缺失导致收集失败
- **影响范围:** 测试基础设施

## 2026-06-27 22:11: fix: 代码审查问题修复
- **文件:**
  - `tests/conftest.py`
  - `tests/test_api/conftest.py`
  - `pyproject.toml`
- **原因:** 修复代码质量审查发现的 5 个问题
- **决策:**
  - full_app fixture 改为手动创建 FastAPI app 并 Mock 所有外部依赖，不再触发真实 lifespan
  - async_client 移除 LifespanManager 依赖（因 full_app 不再走 lifespan）
  - test_api/conftest.py 添加类型注解，使用顶层导入
  - pyproject.toml 移除 dev 中重复的 httpx
- **影响范围:** 测试基础设施

## 2026-06-27 22:22: SessionManager 单元测试
- **文件:**
  - `tests/test_api/test_session_manager.py`
- **原因:** 覆盖 SessionManager 全部方法（create、get、delete、list_sessions、cleanup_expired），14 个测试全部通过
- **决策:**
  - 使用独立的 SessionManager 实例隔离测试
  - 使用 pytest.mark.asyncio 测试异步任务跟踪
  - TTL=-1 模拟立即过期场景
- **影响范围:** 测试 — tests 模块

## 2026-06-27 官方时间: ConstSessionStore 单元测试
- **文件:**
  - `tests/test_api/test_const_session_store.py`
- **原因:** 覆盖消息序列化/反序列化（7 个纯函数测试）和 YAML 文件 I/O（4 个 mock 测试），11 个测试全部通过
- **决策:**
  - TestMessageSerialization 测试纯函数，无需 mock
  - TestConstSessionFileIO 使用 `@patch` 将 _CONST_DIR 替换为临时目录的 Path 对象，避免 MagicMock __truediv__ 复杂性
  - fixture 化 patched_const_dir 复用临时目录
- **影响范围:** 测试 — tests 模块

## 2026-06-27: ruff 自动修复 — E741/ARG005 变量重命名
- **文件:**
  - `tests/test_api/test_health_routes.py`
  - `tests/test_api/test_session_manager.py`
  - `tests/test_api/test_sessions_routes.py`
  - `tests/test_memory/test_memory_manager.py`
  - `tests/test_memory/test_narrative.py`
  - `tests/test_memory/test_narrative_integration.py`
  - `tests/test_todo/conftest.py`
  - `tests/test_todo/test_complete_uncomplete_delete.py`
  - `tests/test_todo/test_tool_list_labels.py`
- **原因:** ruff lint 修复，Task 1.2.1
- **决策:**
  - E741: `l` → `label`
  - ARG005: lambda 未使用参数加 `_` 前缀
- **影响范围:** 测试模块

## 2026-06-27 22:11: API 路由基础测试（会话/健康检查）
- **文件:**
  - `tests/test_api/test_sessions_routes.py`
  - `tests/test_api/test_health_routes.py`
- **原因:** 覆盖会话 CRUD REST API 和健康检查端点，验证路由正确性
- **决策:**
  - 使用 FastAPI + ASGITransport + AsyncClient 隔离测试路由层
  - sessions 路由使用真实 SessionManager 验证 CRUD 流程
  - health 路由 mock 所有外部依赖（provider_manager、ltm、memory_path）
  - 添加 autouse fixture 屏蔽 tiktoken SSL 错误和 memory.yaml 缺失问题
- **影响范围:** 测试 — tests 模块，10 个测试全部通过
