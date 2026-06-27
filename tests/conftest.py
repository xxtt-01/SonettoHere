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
    """完整应用实例，Mock LLM 和文件系统以避免真实 API 调用。"""
    from unittest.mock import MagicMock

    from api.server import create_app

    app = create_app()
    # Mock LLM 以避免真实 API 调用
    app.state.llm = None
    return app


@pytest.fixture
async def async_client(full_app: FastAPI) -> AsyncClient:
    """异步 HTTP 客户端。"""
    from asgi_lifespan import LifespanManager

    transport = ASGITransport(app=full_app)
    async with LifespanManager(full_app):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
