# SonettoHere 全面优化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 对 SonettoHere v2.6.0 进行全面优化，覆盖测试、代码质量、架构、功能、前端、运维、文档、安全 8 个方向。

**Architecture:** 分 4 个阶段递进——先基础加固（测试+代码质量），再架构升级（SQLite+Docker），然后功能增强+前端优化，最后收尾完善（性能+文档+安全）。

**Tech Stack:** Python 3.11+ / FastAPI / LangChain 0.3+ / Vue 3.4+ / TypeScript / SQLite / Docker

**约束：**
- 每次改动必须保证向后兼容，不引入回归
- 无 git 历史，阶段 0 先做 git init
- 当前无 ruff 配置，需补充

---

## 阶段 0：项目初始化

### Task 0.1: Git 初始化 + ruff 配置

**Files:**
- Create: `.gitignore`（已存在，检查完整性）
- Modify: `pyproject.toml`

- [ ] **Step 1: 检查 .gitignore 是否遗漏关键目录**

```bash
cd D:/SonettoHere-main
cat .gitignore
```

确认包含: `__pycache__/`, `*.pyc`, `.env`, `.venv/`, `venv/`, `node_modules/`, `dist/`, `*.egg-info/`, `build/`, `coverage/`, `.pytest_cache/`, `.idea/`, `.vscode/`

- [ ] **Step 2: 添加 ruff 配置到 pyproject.toml**

向 `D:/SonettoHere-main/pyproject.toml` 追加：

```toml
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM", "ARG", "PTH", "PD", "RUF100"]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["ARG001", "ARG002", "S101"]
"__init__.py" = ["F401"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 3: 运行 ruff 检查当前代码**

```bash
cd D:/SonettoHere-main
ruff check .
```

记录当前问题数量，为后续修复做基线。

- [ ] **Step 4: git init 并首次提交**

```bash
cd D:/SonettoHere-main
git init
git add .
git commit -m "chore: 项目初始化"
```

- [ ] **Step 5: 检查 devlog 目录并初始化**

```bash
mkdir -p devlog
ls devlog/
```

如为空，创建 `devlog/_misc.md` 并记录项目初始化。

---

## 阶段 1：基础加固（测试 + 代码质量）

本阶段测试和代码质量并行推进。

### 1.1 测试基础设施

### Task 1.1.1: 测试配置与 conftest 增强

**Files:**
- Modify: `tests/conftest.py`
- Create: `tests/test_api/conftest.py`

- [ ] **Step 1: 增强 tests/conftest.py — 添加异步支持**

```python
"""共享 fixtures — FastAPI TestClient、认证 Token、完整 app 工厂。"""

import pytest
from asgi_lifespan import LifespanManager  # 需要添加依赖
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient

from api.middleware.auth import AuthMiddleware


@pytest.fixture
def auth_token() -> str:
    return "test-token-123"


@pytest.fixture
def minimal_app(auth_token: str) -> FastAPI:
    """创建一个最小化的 FastAPI app 用于测试 AuthMiddleware。"""
    app = FastAPI()

    @app.get("/api/test")
    async def test_endpoint():
        return {"status": "ok"}

    @app.get("/api/health")
    async def health():
        return {"status": "healthy"}

    @app.get("/open")
    async def open_endpoint():
        return {"status": "public"}

    @app.get("/ws/test")
    async def ws_endpoint():
        return {"status": "ws"}

    app.state.auth_token = auth_token
    app.add_middleware(AuthMiddleware)
    return app


@pytest.fixture
def client(minimal_app: FastAPI) -> TestClient:
    return TestClient(minimal_app)


@pytest.fixture
def full_app() -> FastAPI:
    """完整应用实例（使用 create_app），Mock LLM 和文件系统。"""
    from api.server import create_app
    app = create_app()
    # Mock LLM 以避免真实 API 调用
    app.state.llm = None
    return app


@pytest.fixture
async def async_client(full_app: FastAPI) -> AsyncClient:
    """异步 HTTP 客户端。"""
    transport = ASGITransport(app=full_app)
    async with LifespanManager(full_app):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
```

- [ ] **Step 2: 创建 test_api/conftest.py**

```python
"""API 测试共享 fixtures。"""

import pytest
from unittest.mock import MagicMock, patch

from api.session_manager import SessionManager


@pytest.fixture
def session_manager():
    """干净的 SessionManager 实例。"""
    sm = SessionManager(ttl_seconds=3600)
    return sm


@pytest.fixture
def sample_session(session_manager):
    """在 session_manager 中创建一个会话并返回。"""
    return session_manager.create()
```

- [ ] **Step 3: 添加测试依赖到 pyproject.toml**

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-mock>=3.12.0",
    "ruff>=0.11.0",
    "httpx>=0.27.0",       # 用于 AsyncClient
    "asgi-lifespan>=2.0.0", # 用于 LifespanManager
]
```

- [ ] **Step 4: 验证测试基础设施正常**

```bash
cd D:/SonettoHere-main
pip install -e ".[dev]"
pytest tests/ -v --tb=short
```

- [ ] **Step 5: Commit**

```bash
git add tests/ pyproject.toml
git commit -m "[0/1] 增强测试基础设施：异步支持、完整 app fixture"
```

---

### Task 1.1.2: SessionManager 单元测试

**Files:**
- Create: `tests/test_api/test_session_manager.py`

- [ ] **Step 1: 编写 SessionManager 测试**

```python
"""SessionManager 单元测试。"""

import asyncio
import time

import pytest

from api.session_manager import SessionManager, SessionState


class TestSessionManager:
    def test_create(self):
        sm = SessionManager()
        session = sm.create()
        assert session.session_id is not None
        assert len(session.session_id) == 32  # uuid4 hex
        assert session.message_count == 0
        assert not session.is_subagent
        assert not session.is_const

    def test_create_sub_session(self):
        sm = SessionManager()
        parent = sm.create()
        sub = sm.create_sub_session("test task", parent.session_id)
        assert sub.is_subagent
        assert sub.parent_session_id == parent.session_id
        assert sub._sub_agent_task == "test task"
        assert sub._pending_result is not None

    def test_get_existing(self):
        sm = SessionManager()
        created = sm.create()
        retrieved = sm.get(created.session_id)
        assert retrieved is not None
        assert retrieved.session_id == created.session_id

    def test_get_nonexistent(self):
        sm = SessionManager()
        assert sm.get("nonexistent") is None

    def test_get_or_create_existing(self):
        sm = SessionManager()
        created = sm.create()
        result = sm.get_or_create(created.session_id)
        assert result.session_id == created.session_id

    def test_get_or_create_new(self):
        sm = SessionManager()
        result = sm.get_or_create("new-session-id")
        assert result is not None
        assert result.session_id == "new-session-id"

    def test_delete_existing(self):
        sm = SessionManager()
        created = sm.create()
        assert sm.delete(created.session_id) is True
        assert sm.get(created.session_id) is None

    def test_delete_nonexistent(self):
        sm = SessionManager()
        assert sm.delete("nonexistent") is False

    def test_list_sessions_order(self):
        sm = SessionManager()
        s1 = sm.create()
        time.sleep(0.01)
        s2 = sm.create()
        sessions = sm.list_sessions()
        assert len(sessions) == 2
        # 最新的排前面
        assert sessions[0]["session_id"] == s2.session_id
        assert sessions[1]["session_id"] == s1.session_id

    def test_list_sessions_subagent_filter(self):
        sm = SessionManager()
        sm.create()
        sm.create_sub_session("task")
        sessions = sm.list_sessions()
        sub_sessions = [s for s in sessions if s["is_subagent"]]
        assert len(sub_sessions) == 1

    def test_cleanup_expired(self):
        sm = SessionManager(ttl_seconds=0)  # 立即过期
        sm.create()
        time.sleep(0.01)
        cleaned = sm.cleanup_expired()
        assert cleaned >= 1
        assert len(sm._sessions) == 0

    def test_cleanup_active_not_expired(self):
        sm = SessionManager(ttl_seconds=3600)
        sm.create()
        cleaned = sm.cleanup_expired()
        assert cleaned == 0
        assert len(sm._sessions) == 1

    @pytest.mark.asyncio
    async def test_session_active_task_tracking(self):
        sm = SessionManager()
        session = sm.create()

        async def dummy_task():
            await asyncio.sleep(0.1)

        task = asyncio.create_task(dummy_task())
        session._active_task = task
        sessions = sm.list_sessions()
        assert sessions[0]["has_active_agent"] is True
        await task
        # 等待事件循环调度
        await asyncio.sleep(0)
        sessions = sm.list_sessions()
        assert sessions[0]["has_active_agent"] is False
```

- [ ] **Step 2: 运行测试**

```bash
cd D:/SonettoHere-main
pytest tests/test_api/test_session_manager.py -v --tb=short
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_api/test_session_manager.py
git commit -m "[0/2] 添加 SessionManager 单元测试"
```

---

### Task 1.1.3: ConstSessionStore 单元测试

**Files:**
- Create: `tests/test_api/test_const_session_store.py`

- [ ] **Step 1: 编写测试**

```python
"""Const 固定会话存储单元测试。"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from api.const_session_store import (
    save_const_session,
    load_const_session,
    load_all_const_sessions,
    delete_const_session,
    serialize_messages,
    deserialize_messages,
)


class TestMessageSerialization:
    def test_serialize_human_message(self):
        from langchain_core.messages import HumanMessage
        msg = HumanMessage(content="Hello")
        result = serialize_messages([msg])
        assert len(result) == 1
        assert result[0]["type"] == "human"
        assert result[0]["content"] == "Hello"

    def test_serialize_ai_message_with_tool_calls(self):
        from langchain_core.messages import AIMessage
        msg = AIMessage(
            content="I'll check that",
            tool_calls=[{"name": "test_tool", "args": {"x": 1}, "id": "call1"}],
        )
        result = serialize_messages([msg])
        assert result[0]["type"] == "ai"
        assert "tool_calls" in result[0]

    def test_serialize_tool_message(self):
        from langchain_core.messages import ToolMessage
        msg = ToolMessage(content="result", tool_call_id="call1", name="test_tool")
        result = serialize_messages([msg])
        assert result[0]["type"] == "tool"
        assert result[0]["tool_call_id"] == "call1"

    def test_deserialize_human(self):
        data = [{"type": "human", "content": "Hello"}]
        result = deserialize_messages(data)
        from langchain_core.messages import HumanMessage
        assert isinstance(result[0], HumanMessage)
        assert result[0].content == "Hello"

    def test_deserialize_ai_with_tool_calls(self):
        data = [{
            "type": "ai",
            "content": "I'll check",
            "tool_calls": [{"name": "test_tool", "args": {"x": 1}, "id": "call1"}],
        }]
        result = deserialize_messages(data)
        from langchain_core.messages import AIMessage
        assert isinstance(result[0], AIMessage)

    def test_deserialize_unknown_type_fallback(self):
        data = [{"type": "unknown_type", "content": "fallback"}]
        result = deserialize_messages(data)
        from langchain_core.messages import HumanMessage
        assert isinstance(result[0], HumanMessage)

    def test_roundtrip_mixed_messages(self):
        from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
        original = [
            HumanMessage(content="Hi"),
            AIMessage(content="Hello!", tool_calls=[{"name": "f", "args": {}, "id": "c1"}]),
            ToolMessage(content="done", tool_call_id="c1", name="f"),
        ]
        serialized = serialize_messages(original)
        deserialized = deserialize_messages(serialized)
        assert len(deserialized) == 3
        assert deserialized[0].content == "Hi"
        assert deserialized[1].content == "Hello!"
        assert deserialized[2].content == "done"


class TestConstSessionFileIO:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield d

    @patch("api.const_session_store._CONST_DIR")
    def test_save_and_load(self, mock_dir, temp_dir):
        mock_dir.__str__.return_value = temp_dir
        mock_dir.__truediv__ = lambda self, other: Path(temp_dir) / other

        sid = "test-session-123"
        save_const_session(sid, "Test Const", {"message_count": 5}, [])

        filepath = Path(temp_dir) / f"{sid}.yaml"
        assert filepath.exists()

        loaded = load_const_session(filepath)
        assert loaded is not None
        assert loaded["session_id"] == sid
        assert loaded["const_name"] == "Test Const"

    @patch("api.const_session_store._CONST_DIR")
    def test_delete(self, mock_dir, temp_dir):
        mock_dir.__str__.return_value = temp_dir
        mock_dir.__truediv__ = lambda self, other: Path(temp_dir) / other

        sid = "to-delete"
        save_const_session(sid, "To Delete", {}, [])
        assert delete_const_session(sid) is True
        assert delete_const_session("nonexistent") is False

    @patch("api.const_session_store._CONST_DIR")
    def test_load_all(self, mock_dir, temp_dir):
        mock_dir.__str__.return_value = temp_dir
        mock_dir.__truediv__ = lambda self, other: Path(temp_dir) / other
        mock_dir.glob = lambda self, pattern: Path(temp_dir).glob(pattern)

        save_const_session("s1", "S1", {}, [])
        save_const_session("s2", "S2", {}, [])
        all_sessions = load_all_const_sessions()
        assert len(all_sessions) == 2
```

- [ ] **Step 2: 运行测试**

```bash
cd D:/SonettoHere-main
pytest tests/test_api/test_const_session_store.py -v --tb=short
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_api/test_const_session_store.py
git commit -m "[0/3] 添加 ConstSessionStore 单元测试"
```

---

### Task 1.1.4: API 路由测试（核心路由）

**Files:**
- Create: `tests/test_api/test_sessions_routes.py`
- Create: `tests/test_api/test_health_routes.py`
- Create: `tests/test_api/test_providers_routes.py`

- [ ] **Step 1: 编写会话路由测试**

```python
"""会话 REST API 路由测试。"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.session_manager import SessionManager


@pytest.fixture
def app():
    """带 SessionManager 的最小 app。"""
    app = FastAPI()
    app.state.session_manager = SessionManager()
    app.state.llm = None
    app.state.provider_manager = MagicMock()
    app.state.provider_manager.count = 0
    app.state.system_prompt = "Test system prompt"
    app.state.native_tools = []
    app.state.mcp_tools = []
    app.state.tools = []
    app.state.ws_registry = MagicMock()
    app.state.ltm = MagicMock()
    app.state.auth_token = "test-token"

    from api.routes.sessions import router
    app.include_router(router, prefix="/api")
    return app


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestSessionsRoutes:
    async def test_create_session(self, client):
        resp = await client.post("/api/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert len(data["session_id"]) == 32

    async def test_list_sessions(self, client):
        await client.post("/api/sessions")
        resp = await client.get("/api/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert "sessions" in data
        assert len(data["sessions"]) >= 1

    async def test_get_session_not_found(self, client):
        resp = await client.get("/api/sessions/nonexistent")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    async def test_delete_session(self, client):
        create_resp = await client.post("/api/sessions")
        sid = create_resp.json()["session_id"]
        resp = await client.delete(f"/api/sessions/{sid}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

    async def test_delete_session_not_found(self, client):
        resp = await client.delete("/api/sessions/nonexistent")
        assert resp.status_code == 404
```

- [ ] **Step 2: 编写健康检查路由测试**

```python
"""健康检查 API 路由测试。"""

import pytest
from unittest.mock import MagicMock
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from api.health import get_health_report


def create_health_app():
    app = FastAPI()
    app.state.session_manager = MagicMock()
    app.state.provider_manager = MagicMock()
    app.state.provider_manager.count = 1
    app.state.ws_registry = MagicMock()
    app.state.mcp_tools = []
    app.state.auth_token = "test-token"

    @app.get("/api/health")
    async def health():
        return await get_health_report(app)

    return app


@pytest.mark.asyncio
class TestHealthRoutes:
    async def test_health_endpoint(self):
        app = create_health_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/health")
            assert resp.status_code == 200
            data = resp.json()
            assert "version" in data
            assert "status" in data
```

- [ ] **Step 3: 运行路由测试**

```bash
cd D:/SonettoHere-main
pytest tests/test_api/ -v --tb=short
```

- [ ] **Step 4: Commit**

```bash
git add tests/test_api/
git commit -m "[0/4] 添加 API 路由基础测试（会话/健康检查）"
```

---

### Task 1.1.5: 前端测试基础设施

**Files:**
- Create: `web/vitest.config.ts`
- Create: `web/src/__tests__/setup.ts`

- [ ] **Step 1: 安装前端测试依赖**

```bash
cd D:/SonettoHere-main/web
npm install -D vitest @vue/test-utils happy-dom
```

- [ ] **Step 2: 创建 vitest.config.ts**

```typescript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    environment: 'happy-dom',
    setupFiles: ['./src/__tests__/setup.ts'],
    globals: true,
  },
})
```

- [ ] **Step 3: 创建测试 setup 文件**

```typescript
// web/src/__tests__/setup.ts
// Vitest setup — 全局 mock 浏览器 API
import { vi } from 'vitest'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value },
    removeItem: (key: string) => { delete store[key] },
    clear: () => { store = {} },
    get length() { return Object.keys(store).length },
    key: (index: number) => Object.keys(store)[index] ?? null,
  }
})()

Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock crypto.randomUUID
if (!globalThis.crypto?.randomUUID) {
  Object.defineProperty(globalThis, 'crypto', {
    value: {
      randomUUID: () => 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c =>
        (c === 'x' ? Math.random() * 16 | 0 : (Math.random() * 16 | 0) & 0x3 | 0x8).toString(16)
      ),
    },
    writable: true,
  })
}
```

- [ ] **Step 4: 验证前端测试可运行**

```bash
cd D:/SonettoHere-main/web
npx vitest run --config vitest.config.ts 2>&1 || echo "测试框架就绪（尚无测试用例）"
```

- [ ] **Step 5: Commit**

```bash
git add web/vitest.config.ts web/src/__tests__/
git commit -m "[0/5] 添加前端测试基础设施（Vitest + happy-dom）"
```

---

### 1.2 代码质量

### Task 1.2.1: Ruff 自动修复 + 手动修复残留问题

**Risk: 低** — ruff 自动修复不改变语义

**Files:**
- Modify: 所有 `.py` 文件

- [ ] **Step 1: 运行 ruff 自动修复**

```bash
cd D:/SonettoHere-main
ruff check . --fix
```

- [ ] **Step 2: 检查无法自动修复的问题**

```bash
ruff check .  # 记录剩余问题列表
```

- [ ] **Step 3: 手动修复剩余问题（分类处理）**

按严重程度依次处理：
1. `F401`（未使用的 import）— 删除或添加 `__all__` 导出
2. `B` 类（bug 风险）— 逐条审查修复
3. `ARG` 类（未使用的函数参数）— 加 `_` 前缀或删除
4. `SIM` 类（简化）— 如 `if/else` 简化为三元表达式

- [ ] **Step 4: 运行测试确保无回归**

```bash
pytest tests/ -v --tb=short
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "[1/1] 代码质量：ruff 自动修复 + 手动修复残留 lint 问题"
```

---

### Task 1.2.2: 统一错误处理中间件

**Risk: 中** — 需要确保所有路由的错误响应格式一致

**Files:**
- Create: `api/middleware/error_handler.py`
- Modify: `api/server.py`

- [ ] **Step 1: 创建统一错误处理中间件**

```python
"""统一错误处理中间件 — 确保所有 API 错误响应格式一致。"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorResponseFormatter:
    """统一错误响应格式：{"error": {"code": ..., "message": ..., "detail": ...}}"""

    @staticmethod
    def format(status_code: int, message: str, detail: str | None = None) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": status_code,
                    "message": message,
                    "detail": detail or message,
                }
            },
        )


async def unified_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局异常处理：将 HTTPException 和未捕获异常统一为 JSON 格式。"""
    if isinstance(exc, StarletteHTTPException):
        return ErrorResponseFormatter.format(
            status_code=exc.status_code,
            message=exc.detail,
        )
    # 未捕获异常 → 500
    return ErrorResponseFormatter.format(
        status_code=500,
        message="Internal server error",
        detail=str(exc) if request.app.debug else None,
    )
```

- [ ] **Step 2: 在 create_app 中注册异常处理器**

修改 `D:/SonettoHere-main/api/server.py`：

```python
# 在 create_app() 函数中，app 创建后、路由挂载前添加：
from api.middleware.error_handler import unified_error_handler

def create_app() -> FastAPI:
    app = FastAPI(
        title="SonettoHere API",
        version=__version__,
        lifespan=lifespan,
    )

    # 全局异常处理器
    app.add_exception_handler(Exception, unified_error_handler)

    # ... 其余代码不变
```

- [ ] **Step 3: 运行测试确保无回归**

```bash
pytest tests/ -v --tb=short
```

- [ ] **Step 4: 手动验证错误响应格式**

```python
# 快速验证脚本
import requests
r = requests.get("http://localhost:8000/api/sessions/nonexistent")
assert r.json().get("error", {}).get("code") == 404
print("错误格式统一验证通过")
```

- [ ] **Step 5: Commit**

```bash
git add api/middleware/error_handler.py api/server.py
git commit -m "[1/2] 统一错误处理：添加全局异常处理器，标准化错误响应格式"
```

---

### Task 1.2.3: 完善类型注解

**Risk: 低** — 仅添加类型注解，不改变逻辑

**Files:**
- Modify: `api/session_manager.py`（已有 dataclass，但方法缺返回类型）
- Modify: `api/const_session_store.py`
- Modify: `config/settings.py`
- Modify: `tools/__init__.py`

- [ ] **Step 1: 为 session_manager.py 添加返回类型注解**

```python
# 关键方法补充注解
def create(self) -> SessionState: ...
def create_sub_session(self, task: str, parent_session_id: str | None = None) -> SessionState: ...
def get(self, session_id: str) -> SessionState | None: ...
def get_or_create(self, session_id: str) -> SessionState: ...
def delete(self, session_id: str) -> bool: ...
def list_sessions(self) -> list[dict]: ...
def cleanup_expired(self) -> int: ...
```

- [ ] **Step 2: 为 const_session_store.py 添加类型注解**

```python
def serialize_messages(raw_messages: list) -> list[dict]: ...
def deserialize_messages(data: list[dict]) -> list: ...
def save_const_session(session_id: str, const_name: str, metadata: dict, messages: list[dict]) -> str: ...
def load_const_session(filepath: Path) -> dict | None: ...
def load_all_const_sessions() -> list[dict]: ...
def delete_const_session(session_id: str) -> bool: ...
```

- [ ] **Step 3: 运行 ruff 检查类型相关规则**

```bash
cd D:/SonettoHere-main
ruff check . --select ANN
```

- [ ] **Step 4: Commit**

```bash
git add api/session_manager.py api/const_session_store.py config/settings.py
git commit -m "[1/3] 完善类型注解：SessionManager、ConstSessionStore、Settings"
```

---

### Task 1.2.4: 消除 dead code 和调试残留

**Risk: 低-中** — 删除代码前确认未被引用

**Files:**
- Modify: 根据分析结果决定

- [ ] **Step 1: 扫描 dead code**

```bash
cd D:/SonettoHere-main
# 查找定义了但未在项目中使用的函数/类
# 用 grep 检查函数定义和引用
grep -rn "^def \|^async def " api/ tools/ memory/ config/ agent/ | grep -v "__init__" | wc -l
```

- [ ] **Step 2: 检查 console.log 残留**

```bash
cd D:/SonettoHere-main
grep -rn "console.log" web/src/ --include="*.ts" --include="*.vue"
```

移除开发调试用的 console.log（保留错误日志和关键链路日志）。

- [ ] **Step 3: 删除确实无用的代码**

对每个找到的疑似 dead code：
1. 用 `grep -rn "函数名"` 确认无引用
2. 删除或注释（如不确定则保留并标记 TODO）

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "[1/4] 清理 dead code 和调试日志残留"
```

---

## 阶段 2：架构升级（SQLite + Docker）

### 2.1 SQLite 迁移 — 会话管理

### Task 2.1.1: SQLite 基础设施

**Risk: 中** — 需要确保数据库 schema 设计合理

**Files:**
- Create: `api/database/__init__.py`
- Create: `api/database/session_store.py`
- Create: `api/database/migrations/__init__.py`
- Create: `api/database/migrations/001_create_sessions.py`

- [ ] **Step 1: 创建数据库基础设施**

```python
"""数据库连接管理。"""

import sqlite3
import threading
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DB_DIR / "sonetto.db"

_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """获取当前线程的数据库连接（线程本地单例）。"""
    if not hasattr(_local, "conn") or _local.conn is None:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
    return _local.conn


def close_connection():
    """关闭当前线程的数据库连接。"""
    if hasattr(_local, "conn") and _local.conn is not None:
        _local.conn.close()
        _local.conn = None
```

- [ ] **Step 2: 创建会话表迁移**

```python
"""001：创建会话表。"""

CREATE_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    last_active REAL NOT NULL,
    message_count INTEGER NOT NULL DEFAULT 0,
    is_subagent INTEGER NOT NULL DEFAULT 0,
    parent_session_id TEXT,
    sub_agent_task TEXT,
    is_const INTEGER NOT NULL DEFAULT 0,
    const_name TEXT DEFAULT ''
);
"""

CREATE_SESSION_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS session_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    tool_call_id TEXT,
    tool_name TEXT,
    tool_calls_json TEXT,
    additional_kwargs_json TEXT,
    created_at REAL NOT NULL DEFAULT (julianday('now'))
);
CREATE INDEX IF NOT EXISTS idx_session_messages_session_id
    ON session_messages(session_id);
"""


def run(conn):
    conn.execute(CREATE_SESSIONS_TABLE)
    conn.execute(CREATE_SESSION_MESSAGES_TABLE)
    conn.commit()
```

- [ ] **Step 3: 实现 migrations runner**

```python
"""迁移运行器。"""

import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent

CREATE_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS _migrations (
    version INTEGER PRIMARY KEY,
    applied_at REAL NOT NULL DEFAULT (julianday('now'))
);
"""


def run_migrations(conn: sqlite3.Connection) -> list[int]:
    """运行所有未执行的迁移。返回已应用的版本号列表。"""
    conn.execute(CREATE_MIGRATIONS_TABLE)
    applied = {row["version"] for row in
               conn.execute("SELECT version FROM _migrations").fetchall()}

    # 发现迁移文件
    migrations = sorted(
        Path(p).stem for p in MIGRATIONS_DIR.glob("*.py")
        if p.stem.isdigit()
    )

    applied_versions = []
    for version in migrations:
        v = int(version)
        if v not in applied:
            module = __import__(f"api.database.migrations.{version}", fromlist=["run"])
            module.run(conn)
            conn.execute("INSERT INTO _migrations (version) VALUES (?)", (v,))
            applied_versions.append(v)

    if applied_versions:
        conn.commit()
    return applied_versions
```

- [ ] **Step 4: 测试数据库基础设施**

```python
# tests/test_database/test_migrations.py
import tempfile
from pathlib import Path
import pytest
import sqlite3


@pytest.fixture
def db_conn():
    """临时 SQLite 数据库。"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()
    Path(db_path).unlink()
```

- [ ] **Step 5: Commit**

```bash
git add api/database/ tests/test_database/
git commit -m "[2/1] SQLite 基础设施：连接管理 + 迁移运行器 + 会话表"
```

---

### Task 2.1.2: 基于 SQLite 的 SessionStore

**Risk: 高** — 需要替换 SessionManager 的内存存储，同时保持 API 兼容

**Files:**
- Create: `api/database/session_store.py`
- Modify: `api/session_manager.py`

- [ ] **Step 1: 实现 DatabaseSessionStore**

```python
"""基于 SQLite 的会话存储。"""

import json
import time
import uuid
from collections.abc import Sequence

from api.database import get_connection


class DatabaseSessionStore:
    """替代 SessionManager 的 _sessions dict，所有数据持久化到 SQLite。"""

    def create(self, is_subagent: bool = False, parent_session_id: str | None = None,
               task: str | None = None) -> dict:
        session_id = uuid.uuid4().hex
        now = time.time()
        conn = get_connection()
        conn.execute(
            """INSERT INTO sessions (session_id, created_at, last_active, message_count,
               is_subagent, parent_session_id, sub_agent_task)
               VALUES (?, ?, ?, 0, ?, ?, ?)""",
            (session_id, now, now, int(is_subagent), parent_session_id, task),
        )
        conn.commit()
        return self.get(session_id)

    def get(self, session_id: str) -> dict | None:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if row is None:
            return None
        # 更新 last_active
        conn.execute(
            "UPDATE sessions SET last_active = ? WHERE session_id = ?",
            (time.time(), session_id),
        )
        conn.commit()
        return dict(row)

    def delete(self, session_id: str) -> bool:
        conn = get_connection()
        cursor = conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
        return cursor.rowcount > 0

    def list_sessions(self) -> list[dict]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY last_active DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def cleanup_expired(self, ttl_seconds: int) -> int:
        cutoff = time.time() - ttl_seconds
        conn = get_connection()
        cursor = conn.execute(
            "DELETE FROM sessions WHERE last_active < ? AND is_const = 0",
            (cutoff,),
        )
        conn.commit()
        return cursor.rowcount

    def save_messages(self, session_id: str, messages: list) -> None:
        """批量保存消息到 session_messages 表。"""
        conn = get_connection()
        for msg in messages:
            conn.execute(
                """INSERT INTO session_messages
                   (session_id, role, content, tool_call_id, tool_name, tool_calls_json, additional_kwargs_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    getattr(msg, "type", "human"),
                    msg.content if hasattr(msg, "content") else str(msg),
                    getattr(msg, "tool_call_id", None),
                    getattr(msg, "name", None),
                    json.dumps(getattr(msg, "tool_calls", []), default=str) if hasattr(msg, "tool_calls") and msg.tool_calls else None,
                    json.dumps(getattr(msg, "additional_kwargs", {}), default=str) if hasattr(msg, "additional_kwargs") else None,
                ),
            )
        conn.commit()
```

- [ ] **Step 2: 修改 SessionManager 支持双模式**

```python
"""会话状态管理 — 支持内存模式（默认）和 SQLite 持久化模式。"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph


@dataclass
class SessionState:
    session_id: str
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    message_count: int = 0
    _active_task: asyncio.Task | None = field(default=None, repr=False)
    checkpointer: MemorySaver = field(default_factory=MemorySaver)
    _graph: CompiledStateGraph | None = field(default=None, repr=False)
    auto_approve: bool = False
    is_subagent: bool = False
    parent_session_id: str | None = None
    _sub_agent_task: str | None = field(default=None, repr=False)
    _pending_result: asyncio.Future | None = field(default=None, repr=False)
    is_const: bool = False
    const_name: str = ""


class SessionManager:
    """会话管理器。支持内存模式（向后兼容）和 SQLite 持久化模式。

    mode='memory': 原有行为，会话数据仅存内存
    mode='sqlite': 持久化到 SQLite，重启后会话恢复
    """

    def __init__(self, ttl_seconds: int = 1800, mode: Literal["memory", "sqlite"] = "memory"):
        self._sessions: dict[str, SessionState] = {}
        self._ttl = ttl_seconds
        self._mode = mode

        if mode == "sqlite":
            from api.database.session_store import DatabaseSessionStore
            self._db_store = DatabaseSessionStore()
            self._load_from_db()
        else:
            self._db_store = None

    def _load_from_db(self) -> None:
        """从 SQLite 加载所有会话到内存。"""
        if self._db_store is None:
            return
        for row in self._db_store.list_sessions():
            session = SessionState(
                session_id=row["session_id"],
                created_at=row["created_at"],
                last_active=row["last_active"],
                message_count=row["message_count"],
                is_subagent=bool(row["is_subagent"]),
                parent_session_id=row.get("parent_session_id"),
                is_const=bool(row["is_const"]),
                const_name=row.get("const_name", ""),
            )
            self._sessions[session.session_id] = session

    def create(self) -> SessionState:
        session_id = uuid.uuid4().hex
        session = SessionState(session_id=session_id)
        self._sessions[session_id] = session
        if self._db_store:
            self._db_store.create(
                is_subagent=False, parent_session_id=None, task=None
            )
        return session

    # ... 其他方法保持兼容，但写入操作同步到 SQLite
```

- [ ] **Step 3: 编写 SessionManager SQLite 模式测试**

```python
"""SessionManager SQLite 持久化模式测试。"""

import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch

from api.session_manager import SessionManager


@patch("api.database.DB_PATH", new_callable=lambda: Path(tempfile.gettempdir()) / "test_sonetto.db")
class TestSessionManagerSQLite:
    def test_create_persistent(self, mock_db):
        sm = SessionManager(mode="sqlite")
        session = sm.create()
        assert session.session_id is not None

        # 新建一个 manager 实例应能加载之前创建的会话
        sm2 = SessionManager(mode="sqlite")
        loaded = sm2.get(session.session_id)
        assert loaded is not None
        assert loaded.session_id == session.session_id

    def test_delete_persistent(self, mock_db):
        sm = SessionManager(mode="sqlite")
        session = sm.create()
        sm.delete(session.session_id)

        sm2 = SessionManager(mode="sqlite")
        assert sm2.get(session.session_id) is None

    @classmethod
    def teardown_class(cls):
        db_path = Path(tempfile.gettempdir()) / "test_sonetto.db"
        if db_path.exists():
            db_path.unlink()
```

- [ ] **Step 4: 运行全部测试验证无回归**

```bash
cd D:/SonettoHere-main
pytest tests/ -v --tb=short
```

关键验证点：
- 所有现有测试仍然通过（`mode="memory"` 模式行为不变）
- 新增的 SQLite 模式测试通过

- [ ] **Step 5: Commit**

```bash
git add api/database/session_store.py api/session_manager.py tests/
git commit -m "[2/2] SQLite 会话存储：DatabaseSessionStore + SessionManager 双模式支持"
```

---

### Task 2.1.3: 阶段切换 — 默认启用 SQLite 模式

**Risk: 高** — 切换默认模式前确保数据完整性

**Files:**
- Modify: `api/dependencies.py`（修改 SessionManager 创建方式）
- Modify: `api/server.py`（确保数据库迁移在启动时运行）

- [ ] **Step 1: 在 server.py lifespan 中添加数据库迁移**

```python
# 在 lifespan 函数开始处添加：
from api.database.migrations import run_migrations
from api.database import get_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 0. 运行数据库迁移
    conn = get_connection()
    applied = run_migrations(conn)
    if applied:
        print(f"[db] Applied migrations: {applied}")
```

- [ ] **Step 2: 切换 SessionManager 默认模式为 sqlite**

```python
# api/server.py 中创建 SessionManager 的位置
app.state.session_manager = SessionManager(mode="sqlite")
```

- [ ] **Step 3: 确认向后兼容 — const 会话仍使用 YAML**

const 会话系统的 YAML 存储保持不变（Task 2.1.4 再迁移）。

- [ ] **Step 4: 运行全部测试**

```bash
cd D:/SonettoHere-main
pytest tests/ -v --tb=short
```

- [ ] **Step 5: Commit**

```bash
git add api/server.py api/database/
git commit -m "[2/3] 默认启用 SQLite 会话存储 + 启动时自动迁移"
```

---

### Task 2.1.4: SQLite 迁移 — 记忆系统

**Risk: 中** — 记忆系统涉及 LLM 生成的 YAML 内容

**Files:**
- Create: `api/database/migrations/002_create_memories.py`
- Modify: `memory/memory_manager.py`

- [ ] **Step 1: 创建记忆表迁移**

```python
"""002：创建记忆表。"""

CREATE_MEMORIES_TABLE = """
CREATE TABLE IF NOT EXISTS memories (
    memory_id TEXT PRIMARY KEY,
    section TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_memories_section ON memories(section);
"""

CREATE_MEMORIES_BACKUP_TABLE = """
CREATE TABLE IF NOT EXISTS memories_archive (
    memory_id TEXT,
    section TEXT,
    description TEXT,
    archived_at REAL NOT NULL DEFAULT (julianday('now'))
);
"""


def run(conn):
    conn.execute(CREATE_MEMORIES_TABLE)
    conn.execute(CREATE_MEMORIES_BACKUP_TABLE)
    conn.commit()
```

- [ ] **Step 2: 修改 MemoryManager 支持 SQLite**

分析现有 `memory/memory_manager.py` 中的 CRUD 方法，添加 SQLite 存储后端。

- [ ] **Step 3: 添加导入脚本（从 YAML 导入到 SQLite）**

```python
"""从现有 memory.yaml 导入数据到 SQLite。"""
def import_memories_from_yaml(yaml_path: Path, conn) -> int:
    if not yaml_path.exists():
        return 0
    import yaml
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    count = 0
    for section, items in data.items():
        for item in items:
            conn.execute(
                "INSERT OR REPLACE INTO memories (memory_id, section, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (item.get("id", str(uuid.uuid4())), section, item.get("description", ""), time.time(), time.time()),
            )
            count += 1
    conn.commit()
    return count
```

- [ ] **Step 4: 运行测试**

```bash
pytest tests/test_memory/ -v --tb=short
```

- [ ] **Step 5: Commit**

```bash
git add api/database/migrations/002_create_memories.py memory/
git commit -m "[2/4] SQLite 记忆存储：迁移 + MemoryManager 双后端支持"
```

---

### 2.2 Docker 化

### Task 2.2.1: 创建 Dockerfile

**Risk: 低** — Docker 仅打包不影响运行代码

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`

- [ ] **Step 1: 创建 .dockerignore**

```
__pycache__/
*.pyc
.env
.venv/
venv/
node_modules/
.git/
.gitignore
*.md
tests/
dev_docs/
docs/
images/
memory/
```

- [ ] **Step 2: 创建 Dockerfile（多阶段构建）**

```dockerfile
# === Stage 1: Build Frontend ===
FROM node:20-alpine AS frontend-build
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ .
RUN npm run build

# === Stage 2: Python Backend ===
FROM python:3.11-slim AS backend
WORKDIR /app

# 安装系统依赖（Playwright 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 复制并安装 Python 依赖
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
COPY --from=frontend-build /app/web/dist /app/web/dist

# 数据卷
VOLUME ["/app/data", "/app/config/personas"]

EXPOSE 8000

CMD ["python", "main.py"]
```

- [ ] **Step 3: 创建 docker-compose.yml（可选，简便启动）**

```yaml
version: "3.9"
services:
  sonettohere:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./config/personas:/app/config/personas
      - ./.env:/app/.env
    environment:
      - SONETTO_ENV=production
    restart: unless-stopped
```

- [ ] **Step 4: 验证 Docker 构建**

```bash
cd D:/SonettoHere-main
docker build -t sonettohere:latest .
docker run --rm -p 8000:8000 sonettohere:latest
```

- [ ] **Step 5: Commit**

```bash
git add Dockerfile .dockerignore docker-compose.yml
git commit -m "[2/5] 添加 Docker 多阶段构建支持"
```

---

## 阶段 3：功能增强 + 前端优化

### 3.1 SubAgent 增强

### Task 3.1.1: SubAgent 并行执行支持

**Risk: 中** — 需要确保子 Agent 隔离性和状态管理正确

**Files:**
- Modify: `tools/sub_agent/tool_call_sub_agent.py`
- Modify: `api/routes/chat.py`

- [ ] **Step 1: 分析当前 SubAgent 实现**

查看 `tools/sub_agent/tool_call_sub_agent.py` 和 `api/routes/chat.py` 中 SubAgent 相关代码，理解现有生命周期。

- [ ] **Step 2: 添加并行 SubAgent 支持**

主要改动：
1. 允许主 Agent 同时向多个 SubAgent 派发任务
2. 每个 SubAgent 独立运行，不阻塞主 Agent
3. 结果收集：首次完成或全部完成后通知主 Agent

- [ ] **Step 3: 编写 SubAgent 单元测试**

- [ ] **Step 4: 手动测试并行 SubAgent**

```bash
# 通过 WebSocket 发送测试消息，观察子会话创建
```

- [ ] **Step 5: Commit**

```bash
git add tools/sub_agent/ api/routes/chat.py tests/
git commit -m "[3/1] SubAgent 并行执行支持"
```

---

### 3.2 用户/权限系统

### Task 3.2.1: 基础用户认证系统

**Risk: 高** — 安全相关改动必须谨慎

**Files:**
- Create: `api/database/migrations/003_create_users.py`
- Create: `api/user_manager.py`
- Modify: `api/server.py`

- [ ] **Step 1: 创建用户表迁移**

```python
"""003：创建用户表。"""

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL,
    last_login REAL
);
```

- [ ] **Step 2: 实现 UserManager**

- [ ] **Step 3: 添加用户管理 API 路由**

- [ ] **Step 4: 前端用户管理页面**

- [ ] **Step 5: Commit**

---

### 3.3 现有工具增强

### Task 3.3.1: 地图工具增强

**Files:**
- Modify: `tools/map/tool_nearby.py`
- Modify: `tools/map/tool_transit.py`

- [ ] **Step 1: 审查现有地图工具功能**

查看 `dev_docs/projects/bay-project/overview.md` 了解当前定位。

- [ ] **Step 2: 添加导航功能（高德导航 API）**

新增路线规划能力（驾车/步行/骑行已存在，确认是否需要增强）。

- [ ] **Step 3: 添加工具测试**

- [ ] **Step 4: Commit**

---

### Task 3.3.2: 天气工具增强

**Files:**
- Modify: `tools/network/tool_weather.py`

- [ ] **Step 1: 查看当前天气工具实现**

- [ ] **Step 2: 添加功能**（根据用户需求）
  - 未来天气预报（当前可能仅当天）
  - 历史天气对比
  - 更多城市支持

- [ ] **Step 3: Commit**

---

### 3.4 新工具集成

### Task 3.4.1: Notion 工具集成

**Files:**
- Create: `tools/notion/__init__.py`
- Create: `tools/notion/tool_notion.py`

（根据用户具体需求决定先集成哪个工具）

---

### 3.5 前端体验优化

### Task 3.5.1: 加载状态优化

**Files:**
- Modify: `web/src/components/ChatInput.vue`
- Modify: `web/src/components/ChatWindow.vue`

- [ ] **Step 1: 添加骨架屏加载状态**

在 WebSocket 连接建立时，ChatWindow 显示骨架屏而非空白。

- [ ] **Step 2: 输入框禁用状态**

发送消息后 ChatInput 禁用直到连接就绪。

- [ ] **Step 3: Commit**

---

### Task 3.5.2: 响应式布局改进

**Files:**
- Modify: `web/src/App.vue`
- Modify: `web/src/components/SessionSidebar.vue`

- [ ] **Step 1: 添加移动端布局适配**

当前侧边栏 220px 固定宽度，在 <768px 宽度下应自动收起或变为 overlay 模式。

- [ ] **Step 2: Commit**

---

## 阶段 4：收尾完善

### 4.1 性能优化

### Task 4.1.1: 会话查询缓存

**Risk: 低**

- [ ] **Step 1: 分析当前性能瓶颈**

```bash
# 统计各 API 路由响应时间
```

- [ ] **Step 2: 为 SessionManager.list_sessions() 添加 LRU 缓存**

- [ ] **Step 3: Commit**

---

### 4.2 文档完善

### Task 4.2.1: API 文档

**Files:**
- Create: `dev_docs/api/overview.md`
- Create: `dev_docs/api/routes.md`

- [ ] **Step 1: 编写 API 概览文档**

记录所有路由、请求/响应格式、认证方式。

- [ ] **Step 2: 确认 FastAPI 自动生成的 OpenAPI 文档可用**

```bash
# 启动后访问 http://localhost:8000/docs
```

- [ ] **Step 3: Commit**

---

### 4.3 安全审计

### Task 4.3.1: OWASP 安全检查

**Files:**
- Modify: 根据检查结果修复

- [ ] **Step 1: 运行 Gitleaks 密钥扫描**

```bash
cd D:/SonettoHere-main
gitleaks detect --source . -v
```

- [ ] **Step 2: 检查输入验证**

逐路由检查：
- 路径遍历（files route）
- SQL 注入（SQLite 查询使用参数化查询）
- XSS（前端渲染使用 markdown-it，已做转义）
- SSRF（URL 输入验证）

- [ ] **Step 3: 修复发现的安全问题**

- [ ] **Step 4: Commit**

---

## 风险登记表

| 编号 | 阶段 | 风险 | 等级 | 缓解措施 |
|------|------|------|------|----------|
| R1 | 2.1.2 | SQLite 迁移中数据丢失 | 高 | 双模式支持，保留 YAML 作为 fallback |
| R2 | 2.1.3 | 切换默认模式后会话丢失 | 高 | 启动时自动从 YAML 导入到 SQLite |
| R3 | 3.2.1 | 用户系统影响现有认证 | 中 | 保持现有 Token 认证不变，用户系统作为附加层 |
| R4 | 2.2.1 | Docker 构建中 Playwright 兼容性 | 中 | 使用 slim 镜像 + apt 安装必要依赖 |
| R5 | 1.2.2 | 统一错误处理器修改 HTTPException 行为 | 中 | 仅处理未捕获异常，不改变显式抛出的 HTTPException |
| R6 | 全部 | 测试覆盖不充分引入回归 | 中 | 每个 Task 必须运行全部测试后再提交 |

---

## 阶段间依赖图

```
阶段0（初始化）
   │
   ▼
阶段1（基础加固）←── 所有后续阶段的依赖
   │
   ├── 1.1 测试体系 → 为阶段2/3/4 提供质量保障
   └── 1.2 代码质量 → 减少阶段2/3 中的技术债务
   │
   ▼
阶段2（架构升级）
   │
   ├── 2.1 SQLite ──→ 依赖阶段1 的测试保障
   └── 2.2 Docker ──→ 独立于其他阶段，可随时执行
   │
   ▼
阶段3（功能+前端）──→ 依赖阶段2 的 SQLite 基础设施
   │
   ▼
阶段4（收尾完善）──→ 依赖前三个阶段完成
```

> **执行说明：**
> - 阶段内的 Task 可以并行执行（测试和代码质量在阶段1是并行关系）
> - 跨阶段的 Task 必须按顺序执行（阶段1 → 2 → 3 → 4）
> - 每个 Task 完成后必须运行 `pytest tests/ -v --tb=short` 确保无回归
> - Docker 化可以在阶段2的任何时间点开始，与其他 Task 无冲突
