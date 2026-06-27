## 2026-06-27 22:11: 测试配置增强 — conftest
- **文件:**
  - `tests/conftest.py`
  - `tests/test_api/conftest.py`
- **原因:** 新增 full_app 和 async_client fixture，创建 API 测试共享 fixtures，为后续单元测试奠定基础
- **决策:**
  - tests/conftest.py 保持向后兼容，新增 full_app（完整应用工厂，Mock LLM）和 async_client（异步 HTTP 客户端，支持 LifespanManager）
  - tests/test_api/conftest.py 使用懒导入避免依赖缺失导致收集失败
- **影响范围:** 测试基础设施