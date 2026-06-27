"""SessionManager 单元测试。"""

import asyncio
import time

import pytest

from api.session_manager import SessionManager


class TestSessionManager:
    def test_create(self):
        sm = SessionManager()
        session = sm.create()
        assert session.session_id is not None
        assert len(session.session_id) == 32  # uuid4 hex
        assert session.message_count == 0
        assert not session.is_subagent
        assert not session.is_const
        assert isinstance(session.created_at, float)
        assert isinstance(session.last_active, float)

    def test_create_sub_session(self):
        sm = SessionManager()
        parent = sm.create()
        sub = sm.create_sub_session("test task", parent.session_id)
        assert sub.is_subagent
        assert sub.parent_session_id == parent.session_id
        assert sub._sub_agent_task == "test task"
        assert sub._pending_result is not None
        assert not hasattr(sub, 'is_const') or not sub.is_const

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
        assert len(sessions) >= 2
        # 最新的排前面
        assert sessions[0]["session_id"] == s2.session_id
        assert sessions[1]["session_id"] == s1.session_id

    def test_list_sessions_fields(self):
        sm = SessionManager()
        sm.create()
        sessions = sm.list_sessions()
        s = sessions[0]
        expected_keys = {
            "session_id", "message_count", "created_at", "last_active",
            "has_active_agent", "is_subagent", "is_const", "const_name",
        }
        assert expected_keys.issubset(s.keys())

    def test_cleanup_expired(self):
        sm = SessionManager(ttl_seconds=-1)  # 立即过期
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
            await asyncio.sleep(0.05)

        task = asyncio.create_task(dummy_task())
        session._active_task = task
        sessions = sm.list_sessions()
        assert sessions[0]["has_active_agent"] is True
        await task
        await asyncio.sleep(0.01)
        sessions = sm.list_sessions()
        assert sessions[0]["has_active_agent"] is False

    def test_get_updates_last_active(self):
        sm = SessionManager()
        created = sm.create()
        original = created.last_active
        time.sleep(0.01)
        sm.get(created.session_id)
        assert created.last_active > original
