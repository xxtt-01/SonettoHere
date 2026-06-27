"""API 测试共享 fixtures。"""

import pytest

from api.session_manager import SessionManager, SessionState


@pytest.fixture
def session_manager() -> SessionManager:
    """干净的 SessionManager 实例。"""
    sm = SessionManager(ttl_seconds=3600)
    return sm


@pytest.fixture
def sample_session(session_manager: SessionManager) -> SessionState:
    """在 session_manager 中创建一个会话并返回。"""
    return session_manager.create()
