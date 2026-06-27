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
