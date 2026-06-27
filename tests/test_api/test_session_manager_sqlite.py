"""SessionManager SQLite 模式测试。"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from api.database import close_connection, get_connection
from api.database.migrations import run_migrations
from api.session_manager import SessionManager


@pytest.fixture
def sqlite_sm():
    """使用临时数据库的 SessionManager（sqlite 模式）。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        with patch("api.database.DB_PATH", db_path):
            # 先运行迁移，确保 sessions 表存在
            conn = get_connection()
            run_migrations(conn)
            close_connection()

            sm = SessionManager(mode="sqlite")
            yield sm

            # 清理连接，避免 temp dir 删除时文件被占用
            close_connection()


class TestSessionManagerSQLiteMode:
    def test_create_and_persist(self, sqlite_sm):
        sm = sqlite_sm
        session = sm.create()
        sid = session.session_id

        # 新建 manager 应能加载之前创建的会话
        sm2 = SessionManager(mode="sqlite")
        loaded = sm2.get(sid)
        assert loaded is not None
        assert loaded.session_id == sid

    def test_delete_persists(self, sqlite_sm):
        sm = sqlite_sm
        session = sm.create()
        sid = session.session_id
        sm.delete(sid)

        sm2 = SessionManager(mode="sqlite")
        assert sm2.get(sid) is None

    def test_list_sessions_after_reload(self, sqlite_sm):
        sm = sqlite_sm
        sm.create()
        sm.create()

        sm2 = SessionManager(mode="sqlite")
        sessions = sm2.list_sessions()
        assert len(sessions) >= 2

    def test_memory_mode_still_works(self):
        """memory 模式不受 sqlite 改动影响。"""
        sm = SessionManager(mode="memory")
        session = sm.create()
        assert sm.get(session.session_id) is not None
