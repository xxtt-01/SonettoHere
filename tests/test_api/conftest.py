"""API 测试共享 fixtures。"""

import pytest


@pytest.fixture
def session_manager():
    """干净的 SessionManager 实例。"""
    from api.session_manager import SessionManager

    sm = SessionManager(ttl_seconds=3600)
    return sm


@pytest.fixture
def sample_session(session_manager):
    """在 session_manager 中创建一个会话并返回。"""
    return session_manager.create()
