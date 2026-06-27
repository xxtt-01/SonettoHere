"""健康检查 API 路由测试。"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.health import get_health_report


@pytest.fixture(autouse=True)
def mock_memory_path(tmp_path):
    """创建临时 memory.yaml，避免健康检查因文件缺失而失败。"""
    memory_file = tmp_path / "memory.yaml"
    memory_file.write_text("")
    with patch("api.health.MEMORY_PATH", memory_file):
        yield


@pytest.fixture
def app():
    app = FastAPI()
    app.state.session_manager = MagicMock()
    app.state.provider_manager = MagicMock()
    app.state.provider_manager.count = 1
    mock_provider = MagicMock()
    mock_provider.provider_name = "test-provider"
    mock_provider.default_model = "test-model"
    mock_provider.config.context_window = 128_000
    mock_provider.check_health = AsyncMock(
        return_value=MagicMock(status="ok", latency_ms=5.0, detail="OK")
    )
    app.state.provider_manager.iter_enabled.return_value = [mock_provider]
    app.state.ws_registry = MagicMock()
    app.state.mcp_tools = []
    app.state.native_tools = []
    app.state.ltm = MagicMock()
    app.state.auth_token = "test-token"
    app.state.llm = None
    app.state.system_prompt = "Test"

    @app.get("/api/health")
    async def health():
        return await get_health_report(app)

    return app


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestHealthRoutes:
    async def test_health_endpoint(self, client):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        # Health report should have these top-level keys
        assert "status" in data
        assert "version" in data or "app" in data

    async def test_health_providers(self, client):
        resp = await client.get("/api/health")
        data = resp.json()
        assert data["status"] == "ok"
