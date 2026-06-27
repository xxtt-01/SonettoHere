"""会话 REST API 路由测试。"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.session_manager import SessionManager


@pytest.fixture(autouse=True)
def mock_tiktoken_encoding():
    """Mock tiktoken 避免 SSL 证书错误。"""
    mock_enc = MagicMock()
    mock_enc.encode.return_value = [1, 2, 3]
    with patch("api.context_usage._get_encoding", return_value=mock_enc):
        yield


@pytest.fixture
def app():
    """带 SessionManager 的最小 app。"""
    from unittest.mock import MagicMock

    app = FastAPI()
    sm = SessionManager()
    app.state.session_manager = sm
    app.state.llm = None
    app.state.provider_manager = MagicMock()
    app.state.provider_manager.count = 0
    app.state.system_prompt = "Test"
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
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-Sonetto-Token": "test-token"},
    ) as ac:
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

    async def test_get_session(self, client):
        create = await client.post("/api/sessions")
        sid = create.json()["session_id"]
        resp = await client.get(f"/api/sessions/{sid}")
        assert resp.status_code == 200
        assert resp.json()["session_id"] == sid

    async def test_get_session_not_found(self, client):
        resp = await client.get("/api/sessions/nonexistent")
        assert resp.status_code == 404

    async def test_get_messages_empty(self, client):
        create = await client.post("/api/sessions")
        sid = create.json()["session_id"]
        resp = await client.get(f"/api/sessions/{sid}/messages")
        assert resp.status_code == 200

    async def test_delete_session(self, client):
        create = await client.post("/api/sessions")
        sid = create.json()["session_id"]
        resp = await client.delete(f"/api/sessions/{sid}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

    async def test_delete_session_not_found(self, client):
        resp = await client.delete("/api/sessions/nonexistent")
        assert resp.status_code == 404

    async def test_context_usage_no_llm(self, client):
        create = await client.post("/api/sessions")
        sid = create.json()["session_id"]
        resp = await client.get(f"/api/sessions/{sid}/context-usage")
        # Should still return data even without LLM
        assert resp.status_code == 200
        data = resp.json()
        assert "total_tokens" in data or "session_id" in data
