"""共享 fixtures — FastAPI TestClient、认证 Token、完整 app 工厂。"""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient

from api.middleware.auth import AuthMiddleware


@pytest.fixture
def auth_token() -> str:
    """固定测试 Token。"""
    return "test-token-123"


@pytest.fixture
def minimal_app(auth_token: str) -> FastAPI:
    """最小化 FastAPI app 用于测试 AuthMiddleware。"""
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
    """Starlette TestClient 实例。"""
    return TestClient(minimal_app)


@pytest.fixture
def full_app() -> FastAPI:
    """完整应用实例，Mock 所有外部依赖，不触发 lifespan。"""
    from unittest.mock import MagicMock

    from api.session_manager import SessionManager

    app = FastAPI()

    # Mock all app state
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

    # Mount core routes
    from api.routes.sessions import router as sessions_router

    app.include_router(sessions_router, prefix="/api")

    # Health check
    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": "test"}

    return app


@pytest.fixture
async def async_client(full_app: FastAPI) -> AsyncClient:
    """异步 HTTP 客户端（不触发 lifespan）。"""
    transport = ASGITransport(app=full_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
